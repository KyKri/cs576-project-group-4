import layer1PHY as phy
import layer3 as net
import heapq
import time
import threading
import ipaddress


class UE:
    def __init__(self, id: int, l1ue: phy.UE, l3ue: net.UE, ip: str):
        self.l1ue = l1ue
        self.l3ue = l3ue
        self.id = id
        self.ip = ip
        self.connected_to: BaseStation | None = None


class BaseStation:
    def __init__(self, id: int, l1tower: phy.Tower):
        self.tower = l1tower
        self.id = id


class Glu:
    def __init__(self):
        self.ues: list[UE] = []
        self.base_stations: list[BaseStation] = []
        self.queue: list[tuple[float, bytes]] = []
        self.ue_id_counter: int = 0
        self.tower_id_counter: int = 0
        self.cabernet: net.Cabernet = net.Cabernet()
        self.event = threading.Event()
        self.pause_event = threading.Event()
        self.paused = True
        self.pixels_per_meter: float = 1.0
        self.tech_profile: phy.TechProfile = phy.LTE_20
        self.starting_ip: ipaddress.IPv4Address = ipaddress.ip_address("10.0.0.1")
        self.last_assigned_ip: ipaddress.IPv4Address = None

    def add_ue(self, x: float, y: float) -> UE:
        ip = str(self.generate_next_ip())
        l3ue = self.cabernet.create_ue(ip)
        l1ue = phy.UE(x, y)
        ue = UE(self.ue_id_counter, l1ue, l3ue, ip)
        self.ues.append(ue)
        self.ue_id_counter += 1
        self.syncronize_map()
        return ue

    def get_ue(self, ue_id: int) -> UE:
        for ue in self.ues:
            if ue.id == ue_id:
                return ue
        return None

    def update_ue_ip(self, ue_id: int):
        new_ip = str(self.generate_next_ip())
        for ue in self.ues:
            if ue.id == ue_id:
                self.cabernet.change_ip(ue.ip, new_ip)
                ue.ip = new_ip
                break

    def add_tower(self, x: float, y: float, on: bool = True) -> BaseStation:
        l1tower = phy.Tower(x, y, on, self.tech_profile)
        bs = BaseStation(self.tower_id_counter, l1tower)
        self.base_stations.append(bs)
        self.tower_id_counter += 1
        self.syncronize_map()
        return bs

    def get_tower(self, bs_id: int) -> BaseStation:
        for bs in self.base_stations:
            if bs.id == bs_id:
                return bs
        return None

    # update the UE to tower associations based on current positions and tower states
    def syncronize_map(self):
        for ue in self.ues:
            best_bs = None
            best_dist = float("inf")
            for bs in self.base_stations:
                if not bs.tower.on:
                    continue
                d_serv = phy.dist((ue.l1ue.x, ue.l1ue.y), (bs.tower.x, bs.tower.y))
                if d_serv < best_dist:
                    best_dist = d_serv
                    best_bs = bs
            ue.connected_to = best_bs

    def poll_ue(self, ip: str) -> bool:
        frame = self.cabernet.poll_frame_from_ue(ip)
        # None means no frame available
        if not frame:
            return False

        (src, dst) = extract_ips_from_frame(frame)
        src_ue = self.get_ue_by_ip(src)
        dst_ue = self.get_ue_by_ip(dst)
        if (
            not src_ue
            or not dst_ue
            or src_ue.connected_to is None
            or dst_ue.connected_to is None
        ):
            return False
        upload_latency = src_ue.connected_to.tower.up_latency(src_ue.l1ue, len(frame))
        download_latency = dst_ue.connected_to.tower.down_latency(
            dst_ue.l1ue,
            len(frame),
            [bs.tower for bs in self.base_stations],
        )
        total_latency = upload_latency + download_latency
        heapq.heappush(self.queue, (now_in_ms() + total_latency, frame))
        return True

    def try_send_frame(self) -> tuple[bool, float]:
        if not self.queue:
            return False, 0
        (send_time, frame) = self.queue[0]
        if send_time > now_in_ms():
            return False, send_time - now_in_ms()

        (_, frame) = heapq.heappop(self.queue)
        self.cabernet.send_frame(frame)
        return True, 0

    def get_ue_by_ip(self, ip: str) -> UE | None:
        for ue in self.ues:
            if ue.ip == ip:
                return ue
        return None

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if not self.paused:
            self.pause_event.set()

    def __run_poll(self):
        while True:
            if self.paused:
                self.pause_event.wait()
                continue
            for ue in self.ues:
                polled = self.poll_ue(ue.ip)
                if polled:
                    self.event.set()

    def __run_send(self):
        while True:
            if self.paused:
                self.pause_event.wait()
                continue
            sent, wait = self.try_send_frame()
            if not sent:
                if wait == 0:
                    self.event.wait()
                else:
                    self.event.wait(timeout=wait / 1000.0)

    def run_poll(self) -> threading.Thread:
        poll_t = threading.Thread(target=self.__run_poll, name="GluPoll", daemon=True)
        poll_t.start()
        return poll_t

    def run_send(self) -> threading.Thread:
        send_t = threading.Thread(target=self.__run_send, name="GluSend", daemon=True)
        send_t.start()
        return send_t

    def set_tech_profile(self, tech: str) -> None:
        new_tech_profile = phy.LTE_20  # default

        if tech == "LTE_20":
            new_tech_profile = phy.LTE_20
        elif tech == "NR_100":
            new_tech_profile = phy.NR_100

        self.tech_profile = new_tech_profile

    def set_starting_ip(self, ip: str = "10.0.0.1") -> None:
        self.starting_ip = ipaddress.ip_address(ip)

    def generate_next_ip(self) -> ipaddress.IPv4Address:
        last_ip = self.last_assigned_ip

        if last_ip is None:
            next_ip = self.starting_ip
        else:
            next_ip = last_ip + 1

        self.last_assigned_ip = next_ip

        return next_ip

    def set_pixels_per_meter(self, ppm: float) -> None:
        self.pixels_per_meter = ppm


def extract_ips_from_frame(frame: bytes) -> tuple[str, str]:
    # assuming IPv4 and no options
    src_ip = ".".join(str(b) for b in frame[12:16])
    dst_ip = ".".join(str(b) for b in frame[16:20])
    return (src_ip, dst_ip)


def now_in_ms() -> int:
    return int(time.time() * 1000)


def demo():
    g = Glu()
    g.add_tower(phy.NR_100, 200.0, 300.0)
    g.add_tower(phy.NR_100, 600.0, 300.0)
    g.add_tower(phy.LTE_20, 400.0, 150.0)
    g.add_ue(150.0, 250.0)
    g.add_ue(500.0, 350.0)
    g.add_ue(650.0, 140.0)
    g.syncronize_map()
    # multithreaded polling and sending would go here
    poll_t = g.run_poll()
    send_t = g.run_send()
    poll_t.join()
    send_t.join()


if __name__ == "__main__":
    demo()
