import asyncio
import ipaddress
import threading
import time
from typing import List

import layer1 as phy
import layer3 as net
from packet_queue import PacketQueue, Packet
from queue import Queue
from model import UE, BaseStation


class Glu:
    def __init__(self):
        self.cabernet: net.Cabernet = net.Cabernet()
        self.subnet = ipaddress.ip_network("10.0.0.0/24")
        self.starting_ip: ipaddress.IPv4Address = ipaddress.ip_address("10.0.0.1")
        self.last_assigned_ip: ipaddress.IPv4Address = None

        self.ues: list[UE] = []
        self.base_stations: list[BaseStation] = []
        self.ue_id_counter: int = 0
        self.tower_id_counter: int = 0

        self.log_queue = Queue()
        self.upload_queue = PacketQueue()
        self.download_queue = PacketQueue()

        self.frame_at_ue_ready = threading.Event()
        self.frame_at_tower_ready = threading.Event()

        self.pause_event = threading.Event()
        self.paused = True

        self.pixels_per_meter: float = 1.0

        self.threads: list[threading.Thread] = []

    def active_towers(self) -> list[phy.Tower]:
        return [
            bs.tower
            for bs in self.base_stations
            if bs.tower.on and bs.active_upload_packets > 0
        ]

    def active_ues(self) -> list[phy.UE]:
        return [ue.l1ue for ue in self.ues if ue.active_upload_packets > 0]

    def add_ue(self, x: float, y: float) -> UE:
        ip = str(self.generate_next_ip())
        self.cabernet.create_ue(ip)
        l1ue = phy.UE(x, y)
        ue = UE(self.ue_id_counter, l1ue, ip)
        self.ues.append(ue)
        self.ue_id_counter += 1
        self.syncronize_map()
        return ue

    def get_ue(self, ue_id: int) -> UE | None:
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
        l1tower = phy.Tower(x, y, on)
        bs = BaseStation(self.tower_id_counter, l1tower)
        self.base_stations.append(bs)
        self.tower_id_counter += 1
        self.syncronize_map()
        return bs

    def get_tower(self, bs_id: int) -> BaseStation | None:
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
                d_serv = phy.ue_tower_dist(ue.l1ue, bs.tower)
                if d_serv < best_dist:
                    best_dist = d_serv
                    best_bs = bs
            ue.connected_to = best_bs

    def try_poll_ues(self) -> bool:
        frame = self.cabernet.poll_frame()
        # None means no frame available
        if not frame:
            return False

        (src, _) = extract_ips_from_frame(frame)

        # packet source is internet: forward to tower
        if ipaddress.ip_address(src) not in self.subnet:
            packet = Packet(now_in_ms(), frame, 0.0, None, None)
            self.upload_queue.enqueue(packet)
            self.log_queue.put(packet)
            return True

        src_ue = self.get_ue_by_ip(src)

        # source UE not found or not connected: drop frame
        if not src_ue or src_ue.connected_to is None:
            return False

        upload_latency = src_ue.connected_to.tower.upload_latency(
            src_ue.l1ue, len(frame), self.active_ues()
        )
        packet_error_rate = src_ue.connected_to.tower.upload_packet_error_rate(
            src_ue.l1ue, len(frame), self.active_ues()
        )
        packet = Packet(
            now_in_ms() + upload_latency,
            frame,
            packet_error_rate,
            src_ue,
            src_ue.connected_to,
        )
        self.upload_queue.enqueue(packet)
        self.log_queue.put(packet)
        return True

    def try_poll_towers(self) -> bool:
        ready_packets: List[Packet] = self.upload_queue.pop_arrived()

        # no packets to process: block until next poll
        if len(ready_packets) == 0:
            return False

        for packet in ready_packets:
            packet.deliver()
            # arrived packet is corrupted: continue
            if packet.is_corrupted():
                continue

            (_, dst) = extract_ips_from_frame(packet.frame)

            # packet destination is internet: forward to cabernet
            if ipaddress.ip_address(dst) not in self.subnet:
                self.cabernet.send_frame(packet.frame)
                continue

            dst_ue = self.get_ue_by_ip(dst)

            # destination ip is in subnet but UE not found or not connected: drop packet
            if not dst_ue or not dst_ue.connected_to:
                continue

            download_latency = dst_ue.connected_to.tower.download_latency(
                dst_ue.l1ue, len(packet.frame), self.active_towers()
            )
            packet_error_rate = dst_ue.connected_to.tower.download_packet_error_rate(
                dst_ue.l1ue, len(packet.frame), self.active_towers()
            )
            packet = Packet(
                now_in_ms() + download_latency,
                packet.frame,
                packet_error_rate,
                dst_ue.connected_to,
                dst_ue,
            )
            self.download_queue.enqueue(packet)
        return True

    def try_send_frame(self) -> bool:
        ready_packets: List[Packet] = self.download_queue.pop_arrived()

        # no packets to process: block until next poll
        if len(ready_packets) == 0:
            return False

        for packet in ready_packets:
            packet.deliver()

            # arrived packet is corrupted: continue
            if packet.is_corrupted():
                continue

            self.cabernet.send_frame(packet.frame)
        return True

    def __run_poll_ues(self):
        while True:
            if self.paused:
                self.pause_event.wait()
                continue
            polled = self.try_poll_ues()
            if polled:
                self.frame_at_ue_ready.set()

    def __run_poll_towers(self):
        while True:
            if self.paused:
                self.pause_event.wait()
                continue
            polled = self.try_poll_towers()
            if polled:
                self.frame_at_tower_ready.set()
            else:
                self.frame_at_ue_ready.wait(
                    timeout=self.upload_queue.next_ready_timeout()
                )

    def __run_send(self):
        while True:
            if self.paused:
                self.pause_event.wait()
                continue
            sent = self.try_send_frame()
            if not sent:
                self.frame_at_tower_ready.wait(
                    timeout=self.download_queue.next_ready_timeout()
                )

    def __run_stat(self, log_to_sdout: bool = True):
        while True:
            towers = [bs.tower for bs in self.base_stations]
            ues = [ue.l1ue for ue in self.ues]
            self.syncronize_map()
            time.sleep(0.5)
            show = ""
            show += "\n" + "\033[2J\033[H\n"  # Clear + move cursor home
            show += "\n" + f"=== Glu Stats {'pased' if self.paused else 'running'} ==="
            for ue in self.ues:
                show += (
                    "\n" + f"UE {ue.id} at ({ue.l1ue.x}, {ue.l1ue.y}) with IP {ue.ip}"
                )
                bs = ue.connected_to
                if ue.connected_to:
                    bs = ue.connected_to
                    show += (
                        "\n"
                        + f"  connected to Tower {bs.id} at ({bs.tower.x}, {bs.tower.y}) distance: {phy.ue_tower_dist(ue.l1ue, bs.tower)}"
                    )

                else:
                    show += "\n" + "  not connected to any tower"
                show += (
                    "\n"
                    + f"  DL QPSK PER: {bs.tower.download_packet_error_rate(ue.l1ue, 1024, towers) if bs else 'N/A'}"
                )

                show += (
                    "\n"
                    + f"  UL QPSK PER: {bs.tower.upload_packet_error_rate(ue.l1ue, 1024, ues) if bs else 'N/A'}"
                )

                show += (
                    "\n"
                    + f"  DL mbps: {bs.tower.download_bandwidth_mbps(ue.l1ue, towers) if bs else 'N/A'}"
                )

                show += (
                    "\n"
                    + f"  UL mbps: {bs.tower.upload_bandwidth_mbps(ue.l1ue, ues) if bs else 'N/A'}"
                )
            if log_to_sdout:
                print(show)
            with open("glu_stat.txt", "w") as f:
                f.write(show)

    def run_poll_ues(self) -> threading.Thread:
        poll_t = threading.Thread(
            target=self.__run_poll_ues, name="GluPollUEs", daemon=True
        )
        poll_t.start()
        return poll_t

    def run_poll_towers(self) -> threading.Thread:
        poll_t = threading.Thread(
            target=self.__run_poll_towers, name="GluPollTowers", daemon=True
        )
        poll_t.start()
        return poll_t

    def run_send(self) -> threading.Thread:
        send_t = threading.Thread(target=self.__run_send, name="GluSend", daemon=True)
        send_t.start()
        return send_t

    def run_stat(self, log_to_sdout: bool = True) -> threading.Thread:
        stat_t = threading.Thread(
            target=self.__run_stat, args=(log_to_sdout,), name="GluStat", daemon=True
        )
        stat_t.start()
        return stat_t

    def run(self, log_to_sdout: bool = True) -> None:
        t1 = self.run_poll_ues()
        t2 = self.run_poll_towers()
        t3 = self.run_send()
        t4 = self.run_stat(log_to_sdout)
        self.threads.extend([t1, t2, t3, t4])

    def block(self) -> None:
        for t in self.threads:
            t.join()

    def get_ue_by_ip(self, ip: str) -> UE | None:
        for ue in self.ues:
            if ue.ip == ip:
                return ue
        return None

    def toggle_pause(self) -> None:
        self.paused = not self.paused
        if not self.paused:
            self.pause_event.set()

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
    g.add_tower(200.0, 300.0)
    g.add_tower(600.0, 300.0)
    g.add_tower(400.0, 150.0)
    g.add_ue(164.0, 264.0)
    g.add_ue(590.0, 290.0)
    g.add_ue(420.0, 130.0)

    g.run()
    g.toggle_pause()  # unpause
    g.block()




if __name__ == "__main__":
    demo()
