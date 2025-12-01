from .core import TechProfile
from . import core
from typing import List

LTE_20 = TechProfile("LTE-20MHz", carrier_hz=2.6e9, bandwidth_hz=20e6, eta_eff=0.50)
NR_100 = TechProfile("NR-100MHz", carrier_hz=3.5e9, bandwidth_hz=100e6, eta_eff=0.60)


class UE:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y


class Tower:
    def __init__(
        self, x: float, y: float, on: bool = True, tech: TechProfile = LTE_20
    ):  # constructor
        self.t = tech
        self.x = x
        self.y = y
        self.on = on

    def upload_latency(self, ue: UE, nbytes: int, active_ues: List[UE]) -> float:
        distances = [ue_tower_dist(aue, self) for aue in active_ues if aue != ue]
        return self.t.up_latency(ue_tower_dist(ue, self), nbytes, distances)

    def download_latency(
        self, ue: UE, nbytes: int, active_towers: List["Tower"]
    ) -> float:
        distances = [
            ue_tower_dist(ue, tower) for tower in active_towers if self != tower
        ]
        return self.t.down_latency(ue_tower_dist(ue, self), nbytes, distances)

    def download_bandwidth_mbps(self, ue: UE, active_towers: List["Tower"]) -> float:
        distances = [
            ue_tower_dist(ue, tower) for tower in active_towers if self != tower
        ]
        return (
            self.t.rate_bps(self.t.sinr_dl(ue_tower_dist(ue, self), distances)) / 1e6
        )  # convert to Mbps

    def upload_bandwidth_mbps(self, ue: UE, active_ues: List[UE]) -> float:
        distances = [ue_tower_dist(aue, self) for aue in active_ues if aue != ue]
        return (
            self.t.rate_bps(self.t.sinr_ul(ue_tower_dist(ue, self), distances)) / 1e6
        )  # convert to Mbps

    def download_packet_error_rate(
        self, ue: UE, nbytes: int, active_towers: List["Tower"]
    ) -> float:
        distances = [
            ue_tower_dist(ue, tower) for tower in active_towers if self != tower
        ]
        return self.t.per_dl_qpsk(ue_tower_dist(ue, self), nbytes, distances)

    def upload_packet_error_rate(
        self, ue: UE, nbytes: int, active_ues: List[UE]
    ) -> float:
        distances = [ue_tower_dist(aue, self) for aue in active_ues if aue != ue]
        return self.t.per_ul_qpsk(ue_tower_dist(ue, self), nbytes, distances)


# distance helper to calculate the distance between a UE and a tower
def ue_tower_dist(ue: UE, tower: Tower) -> float:
    return core.dist((ue.x, ue.y), (tower.x, tower.y))


def demo():
    t1 = Tower(600, 300, True, LTE_20)
    t2 = Tower(400, 150, True, LTE_20)
    ue1 = UE(610, 320)
    ue2 = UE(450, 250)
    towers = [t1, t2]
    ues = [ue1, ue2]
    print(f"dist t1-ue1: {ue_tower_dist(ue1, t1)} m")
    print(f"dist t1-ue2: {ue_tower_dist(ue2, t1)} m")
    print(f"dist t2-ue1: {ue_tower_dist(ue1, t2)} m")
    print(f"dist t2-ue2: {ue_tower_dist(ue2, t2)} m")
    print("---- Distances ----")
    print(t1.download_packet_error_rate(ue1, 1024, towers))
    print(t1.download_packet_error_rate(ue2, 1024, towers))
    print(t2.download_packet_error_rate(ue1, 1024, towers))
    print(t2.download_packet_error_rate(ue2, 1024, towers))
    print("---- Download Packet Error Rates ----")

    # now uploads
    print(t1.upload_packet_error_rate(ue1, 1024, ues))
    print(t1.upload_packet_error_rate(ue2, 1024, ues))
    print(t2.upload_packet_error_rate(ue1, 1024, ues))
    print(t2.upload_packet_error_rate(ue2, 1024, ues))
    print("---- Upload Packet Error Rates ----")


if __name__ == "__main__":
    demo()
