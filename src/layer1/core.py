"""
Physical Layer for 4G/LTE & 5G
- Create two 5G macros and one LTE small cell
- Drop three UEs on the map
- Attach UEs to their best tower
- Print DL/UL SINR, estimated rates, and serving tower for each UE

"""

import math
import random
from typing import List, Tuple

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


# Tech profiles (LTE/5G)
class TechProfile:
    def __init__(
        self, name: str, carrier_hz: float, bandwidth_hz: float, eta_eff: float
    ):  # constructor
        self.name = name
        self.carrier_freq = carrier_hz
        self.bandwidth_hz = bandwidth_hz
        self.eta_eff = eta_eff

        self.rng = random.Random(RNG_SEED)
        # Precompute noise for this bandwidth
        self.noise_dbm = BACKGROUND_NOISE + 10.0 * math.log10(self.bandwidth_hz)
        self.noise_mw = db_to_lin(self.noise_dbm)  # convert noise density to linear

    # Free space path loss
    def pl1m_db(self) -> float:  # free space path loss at 1 meter
        c = 3e8  # speed of light in m/s
        lambda_wavelength = c / self.carrier_freq
        return 20.0 * math.log10((4 * math.pi * 1) / lambda_wavelength)

    # Real life path loss
    def pathloss_db(self, d_m: float) -> float:
        d = max(MIN_DISTANCE_M, d_m)
        base = self.pl1m_db() + 10.0 * PATHLOSS_N * math.log10(d)
        # signal changing randomly for realistic simulations
        shadow = self.rng.gauss(0.0, SHADOW_SIGMA_DB)
        return base + shadow

    # Received power (dBm)
    def rx_power_dbm(
        self, tx_dbm: float, tx_g_dbi: float, rx_g_dbi: float, d_m: float
    ) -> float:
        pl = self.pathloss_db(d_m)
        # received power = transmitter power + transmitter gain + receiver gain - path loss
        p_dbm = tx_dbm + tx_g_dbi + rx_g_dbi - pl
        return p_dbm

    # Downlink SINR (linear), tower to UE
    def sinr_dl(self, d_serv_m: float, active_towers_to_ue_distance: List[float]) -> float:
        # signal
        s_dbm = self.rx_power_dbm(BS_TX_POWER_DBM, BS_GAIN_DBI, UE_GAIN_DBI, d_serv_m)
        s_mw = db_to_lin(s_dbm)  # convert received power to linear
        # interference (reuse-1, all towers 100% busy)
        I_mw = 0.0
        if active_towers_to_ue_distance:
            for d_i in active_towers_to_ue_distance:
                p_i_dbm = self.rx_power_dbm(
                    BS_TX_POWER_DBM, BS_GAIN_DBI, UE_GAIN_DBI, d_i
                )
                I_mw += db_to_lin(p_i_dbm)
        return s_mw / (I_mw + self.noise_mw)

    # Uplink SINR (linear), UE to tower
    def sinr_ul(self, d_serv_m: float, active_ue_to_tower_distance: List[float]) -> float:
        s_dbm = self.rx_power_dbm(UE_TX_POWER, UE_GAIN_DBI, BS_GAIN_DBI, d_serv_m)
        s_mw = db_to_lin(s_dbm)
        I_mw = 0.0
        if active_ue_to_tower_distance:
            for d_i in active_ue_to_tower_distance:
                p_i_dbm = self.rx_power_dbm(UE_TX_POWER, UE_GAIN_DBI, BS_GAIN_DBI, d_i)
                I_mw += db_to_lin(p_i_dbm)
        return s_mw / (I_mw + self.noise_mw)

    # Shannon throughput
    def rate_bps(self, sinr_linear: float) -> float:
        return self.eta_eff * self.bandwidth_hz * math.log2(1.0 + sinr_linear)

    # Calculate uplink latency in ms
    def up_latency(
        self, ue_distance: float, nbytes: int, active_ue_to_tower_distance: List[float]
    ) -> float:
        c = 3e8  # speed of light in m/s
        prop = ue_distance / c
        transmission = (
            nbytes
            * 8
            / (self.rate_bps(self.sinr_ul(ue_distance, active_ue_to_tower_distance)))
        )
        up_latency = prop + transmission
        return up_latency * 1e3

    # Calculate downlink latency in ms
    def down_latency(
        self,
        ue_distance: float,
        nbytes: int,
        active_towers_to_ue_distance: list[float],
    ) -> float:
        c = 3e8  # speed of light in m/s
        prop = ue_distance / c
        interferer_ds = active_towers_to_ue_distance
        transmission = (
            nbytes * 8 / (self.rate_bps(self.sinr_dl(ue_distance, interferer_ds)))
        )
        downLatency = prop + transmission
        return downLatency * 1e3

    # Bit Error Rate for QPSK modulation (downlink)
    def ber_dl_qpsk(
        self,
        d_serv_m: float,
        active_towers_to_ue_distance: List[float],
    ) -> float:
        sinr = self.sinr_dl(d_serv_m, active_towers_to_ue_distance)
        return ber_qpsk_awgn(sinr)

    # Bit Error Rate for QPSK modulation (uplink)
    def ber_ul_qpsk(
        self,
        d_serv_m: float,
        active_ues_to_tower_distance: List[float],
    ) -> float:
        sinr = self.sinr_ul(d_serv_m, active_ues_to_tower_distance)
        return ber_qpsk_awgn(sinr)

    # Packet Error Rate for QPSK modulation (downlink)
    def per_dl_qpsk(
        self,
        ue_distance: float,
        nbytes: int,
        active_towers_to_ue_distance: List[float],
    ) -> float:
        ber = self.ber_dl_qpsk(ue_distance, active_towers_to_ue_distance)
        return packet_error_prob_bytes(ber, nbytes)

    # Packet Error Rate for QPSK modulation (uplink)
    def per_ul_qpsk(
        self,
        ue_distance: float,
        nbytes: int,
        active_ues_to_tower_distance: List[float],
    ) -> float:
        ber = self.ber_ul_qpsk(ue_distance, active_ues_to_tower_distance)
        return packet_error_prob_bytes(ber, nbytes)


# distance helper to calculate the distance between two points
def dist(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])




def db_to_lin(x_db: float) -> float:  # convert dB to linear
    return 10 ** (x_db / 10.0)


def lin_to_db(x: float) -> float:  # convert linear to dB
    if x <= 0:
        return -999.0
    return 10.0 * math.log10(x)


def byte_error_prob(ber: float) -> float:
    """
    Probability that a single 8-bit byte is received with at least one bit error.
    """
    return 1.0 - (1.0 - ber) ** 8


def packet_error_prob_bits(ber: float, n_bits: int) -> float:
    """
    Probability that a packet of n_bits is received with at least one bit error.
    """
    return 1.0 - (1.0 - ber) ** n_bits


def packet_error_prob_bytes(ber: float, n_bytes: int) -> float:
    """
    Same but parameterized by number of bytes.
    """
    return packet_error_prob_bits(ber, n_bytes * 8)


def ber_qpsk_awgn(sinr_linear: float) -> float:
    """
    Approximate BER for uncoded QPSK/BPSK in AWGN, assuming
    sinr_linear ≈ Eb/N0 (per-bit SNR).
    """
    if sinr_linear <= 0:
        return 0.5  # totally unreliable
    return 0.5 * math.erfc(math.sqrt(sinr_linear))


def ber_mqam_awgn(sinr_linear: float, M: int) -> float:
    """
    Approximate BER for square M-QAM (M = 4,16,64,256,...) in AWGN.
    Assumes sinr_linear is SNR per *symbol* (rough approximation).
    """
    if sinr_linear <= 0 or M < 4:
        return 0.5
    k = math.log2(M)  # bits per symbol
    # Symbol error approximation
    Pb_sym = (
        4
        * (1 - 1 / math.sqrt(M))
        * 0.5
        * math.erfc(math.sqrt(3 * sinr_linear / (2 * (M - 1))))
    )
    # Convert roughly to BER
    return Pb_sym / k


