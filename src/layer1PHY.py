"""
Physical Layer for 4G/LTE & 5G
- Create two 5G macros and one LTE small cell
- Drop three UEs on the map
- Attach UEs to their best tower
- Print DL/UL SINR, estimated rates, and serving tower for each UE

"""

import enum
import math
import random
from typing import List, Tuple, Optional


# Helpers
def db_to_lin(x_db: float) -> float:  # convert dB to linear
    return 10 ** (x_db / 10.0)


def lin_to_db(x: float) -> float:  # convert linear to dB
    if x <= 0:
        return -999.0
    return 10.0 * math.log10(x)


# Tech profiles (LTE/5G)
class TechProfile:
    def __init__(
        self, name: str, carrier_hz: float, bandwidth_hz: float, eta_eff: float
    ):  # constructor
        self.name = name
        self.carrier_freq = carrier_hz
        self.bandwidth_hz = bandwidth_hz
        self.eta_eff = eta_eff


LTE_20 = TechProfile("LTE-20MHz", carrier_hz=2.6e9, bandwidth_hz=20e6, eta_eff=0.50)
NR_100 = TechProfile("NR-100MHz", carrier_hz=3.5e9, bandwidth_hz=100e6, eta_eff=0.60)


class TechProfiles(enum.Enum):
    LTE_20 = LTE_20
    NR_100 = NR_100


# Physical layer constants
BACKGROUND_NOISE = -174.0  # thermal noise density (dBm/Hz)
PATHLOSS_N = 5.0  # path-loss exponent (4–6 urban)
SHADOW_SIGMA_DB = 6.0  # lognormal shadow standard deviation  (dB)
MIN_DISTANCE_M = 1.0  # free space path loss at 1 meter
BS_GAIN_DBI = 15.0  # base-station antenna gain
UE_GAIN_DBI = 0.0  # UE antenna gain
BS_TX_POWER_DBM = 40.0  # Base station transmit power 10 W macro
UE_TX_POWER = 23.0  # UE transmit power ~200 mW
RNG_SEED = 7  # random number generator seed


class UE:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.serving = None  # tower id


# Math stuff
class Tower:
    def __init__(
        self, x: float, y: float, on: bool, tech: TechProfile
    ):  # constructor
        self.t = tech
        self.x = x
        self.y = y
        self.on = on
        self.rng = random.Random(RNG_SEED)
        # Precompute noise for this bandwidth
        self.noise_dbm = BACKGROUND_NOISE + 10.0 * math.log10(self.t.bandwidth_hz)
        self.noise_mw = db_to_lin(self.noise_dbm)  # convert noise density to linear

    # Free space path loss
    def pl1m_db(self) -> float:  # free space path loss at 1 meter
        c = 3e8  # speed of light in m/s
        lambda_wavelength = c / self.t.carrier_freq
        return 20.0 * math.log10((4 * math.pi * 1) / lambda_wavelength)

    # Real life path loss
    def pathloss_db(self, d_m: float) -> float:
        d = max(MIN_DISTANCE_M, d_m)
        base = self.pl1m_db() + 10.0 * PATHLOSS_N * math.log10(d)
        shadow = self.rng.gauss(
            0.0, SHADOW_SIGMA_DB
        )  # signal changing randomly for realistic simulations
        return base + shadow

    # Received power (dBm)
    def rx_power_dbm(
        self, tx_dbm: float, tx_g_dbi: float, rx_g_dbi: float, d_m: float
    ) -> float:
        pl = self.pathloss_db(d_m)
        p_dbm = (
            tx_dbm + tx_g_dbi + rx_g_dbi - pl
        )  # received power = transmitter power + transmitter gain + receiver gain - path loss
        return p_dbm

    # Downlink SINR (linear), tower to UE
    def sinr_dl(self, d_serv_m: float, interferer_ds_m: List[float]) -> float:
        # signal
        s_dbm = self.rx_power_dbm(BS_TX_POWER_DBM, BS_GAIN_DBI, UE_GAIN_DBI, d_serv_m)
        s_mw = db_to_lin(s_dbm)  # convert received power to linear
        # interference (reuse-1, all towers 100% busy)
        I_mw = 0.0
        if interferer_ds_m:
            for d_i in interferer_ds_m:
                p_i_dbm = self.rx_power_dbm(
                    BS_TX_POWER_DBM, BS_GAIN_DBI, UE_GAIN_DBI, d_i
                )
                I_mw += db_to_lin(p_i_dbm)
        return s_mw / (I_mw + self.noise_mw)

    # Uplink SINR (linear), UE to tower
    def sinr_ul(
        self, d_serv_m: float, cochannel_ue_ds_m: Optional[List[float]] = None
    ) -> float:
        s_dbm = self.rx_power_dbm(UE_TX_POWER, UE_GAIN_DBI, BS_GAIN_DBI, d_serv_m)
        s_mw = db_to_lin(s_dbm)
        I_mw = 0.0
        if cochannel_ue_ds_m:
            for d_i in cochannel_ue_ds_m:
                p_i_dbm = self.rx_power_dbm(UE_TX_POWER, UE_GAIN_DBI, BS_GAIN_DBI, d_i)
                I_mw += db_to_lin(p_i_dbm)
        return s_mw / (I_mw + self.noise_mw)

    # Shannon throughput
    def rate_bps(self, sinr_linear: float) -> float:
        return self.t.eta_eff * self.t.bandwidth_hz * math.log2(1.0 + sinr_linear)

    # Calculate uplink latency in ms
    # packet size in bytes
    def up_latency(self, ue: UE, packet_size: int) -> float:
        c = 3e8  # speed of light in m/s
        distance = ue_tower_dist(ue, self)
        prop = distance / c
        transmission = packet_size * 8 / (self.rate_bps(self.sinr_ul(distance)))
        upLatency = prop + transmission
        return upLatency * 1e3

    # Calculate downlink latency in ms
    # packet size in bytes
    def down_latency(
        self,
        ue: UE,
        packet_size: int,
        towers: list["Tower"],
    ) -> float:
        c = 3e8  # speed of light in m/s
        distance = ue_tower_dist(ue, self)
        prop = distance / c
        interferer_ds = [ue_tower_dist(ue, o) for o in towers if o.on and (self != o)]
        transmission = (
            packet_size * 8 / (self.rate_bps(self.sinr_dl(distance, interferer_ds)))
        )
        downLatency = prop + transmission
        return downLatency * 1e3


# distance helper to calculate the distance between two points
def dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


# distance helper to calculate the distance between a UE and a tower
def ue_tower_dist(ue: UE, tower: Tower) -> float:
    return dist((ue.x, ue.y), (tower.x, tower.y))
