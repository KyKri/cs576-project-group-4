"""
Physical Layer for 4G/LTE & 5G
- Create two 5G macros and one LTE small cell
- Drop three UEs on the map
- Attach UEs to their best tower
- Print DL/UL SINR, estimated rates, and serving tower for each UE

"""
import math
import random
from typing import List, Tuple, Optional


# Helpers
def db_to_lin(x_db: float) -> float: # convert dB to linear
    return 10 ** (x_db / 10.0)

def lin_to_db(x: float) -> float: # convert linear to dB
    if x <= 0:
        return -999.0
    return 10.0 * math.log10(x)

# Tech profiles (LTE/5G)
class TechProfile:
    def __init__(self, name: str, carrier_hz: float, bandwidth_hz: float, eta_eff: float): # constructor
        self.name = name
        self.carrier_freq = carrier_hz      
        self.bandwidth_hz = bandwidth_hz     
        self.eta_eff = eta_eff              

LTE_20 = TechProfile("LTE-20MHz", carrier_hz=2.6e9, bandwidth_hz=20e6, eta_eff=0.50)
NR_100 = TechProfile("NR-100MHz",  carrier_hz=3.5e9, bandwidth_hz=100e6, eta_eff=0.60)

# Physical layer constants
BACKGROUND_NOISE = -174.0 # thermal noise density (dBm/Hz)
PATHLOSS_N = 5.0 # path-loss exponent (4–6 urban)
SHADOW_SIGMA_DB = 6.0 # lognormal shadow standard deviation  (dB)   
MIN_DISTANCE_M = 1.0 # free space path loss at 1 meter
BS_GAIN_DBI = 15.0 # base-station antenna gain 
UE_GAIN_DBI = 0.0 # UE antenna gain
BS_TX_POWER_DBM = 40.0 #Base station transmit power 10 W macro 
UE_TX_POWER= 23.0 # UE transmit power ~200 mW
RNG_SEED = 7 # random number generator seed

# Math stuff
class PhysicalLayer:
    def __init__(self, tech: TechProfile): # constructor
        self.t = tech
        self.rng = random.Random(RNG_SEED)
        # Precompute noise for this bandwidth
        self.noise_dbm = BACKGROUND_NOISE + 10.0 * math.log10(self.t.bandwidth_hz)
        self.noise_mw = db_to_lin(self.noise_dbm) # convert noise density to linear

    # Free space path loss
    def pl1m_db(self) -> float: # free space path loss at 1 meter
        c = 3e8  # speed of light in m/s
        lambda_wavelength = c / self.t.carrier_freq
        return 20.0 * math.log10((4 * math.pi * 1) / lambda_wavelength)

    # Real life path loss
    def pathloss_db(self, d_m: float) -> float:
        d = max(MIN_DISTANCE_M, d_m)
        base = self.pl1m_db() + 10.0 * PATHLOSS_N * math.log10(d)
        shadow = self.rng.gauss(0.0, SHADOW_SIGMA_DB) # signal changing randomly for realistic simulations
        return base + shadow

    # Received power (dBm)
    def rx_power_dbm(self, tx_dbm: float, tx_g_dbi: float, rx_g_dbi: float, d_m: float) -> float:
        pl = self.pathloss_db(d_m)
        p_dbm = tx_dbm + tx_g_dbi + rx_g_dbi - pl # received power = transmitter power + transmitter gain + receiver gain - path loss
        return p_dbm

    # Downlink SINR (linear), tower to UE
    def sinr_dl(self, d_serv_m: float, interferer_ds_m: List[float]) -> float:
        # signal
        s_dbm = self.rx_power_dbm(BS_TX_POWER_DBM, BS_GAIN_DBI, UE_GAIN_DBI, d_serv_m)
        s_mw = db_to_lin(s_dbm) # convert received power to linear
        # interference (reuse-1, all towers 100% busy)
        I_mw = 0.0
        if interferer_ds_m:
            for d_i in interferer_ds_m:
                p_i_dbm = self.rx_power_dbm(BS_TX_POWER_DBM, BS_GAIN_DBI, UE_GAIN_DBI, d_i)
                I_mw += db_to_lin(p_i_dbm)
        return s_mw / (I_mw + self.noise_mw)

    # Uplink SINR (linear), UE to tower
    def sinr_ul(self, d_serv_m: float, cochannel_ue_ds_m: Optional[List[float]] = None) -> float:
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

# Geometry & nodes (star topology)
class Tower:
    def __init__(self, id: int, tech: TechProfile, x: float, y: float, on: bool = True, name: str = ""):
        self.id = id
        self.tech = tech
        self.x = x
        self.y = y
        self.on = on
        self.name = name

class UE:
    def __init__(self, id: int, x: float, y: float, serving: Optional[int] = None):
        self.id = id
        self.x = x
        self.y = y
        self.serving = serving  # tower id

# distance helper to calculate the distance between two points
def dist(a: Tuple[float,float], b: Tuple[float,float]) -> float:
    return math.hypot(a[0]-b[0], a[1]-b[1])

# Build star: attach each UE to the tower with max expected DL rate

def attach_star(ues: List[UE], towers: List[Tower], phy_map: dict[int, PhysicalLayer]) -> None:
    for ue in ues:
        best_tid = None
        best_rate = -1.0
        for t in towers:
            if not t.on:
                continue
            phy = phy_map[t.id]
            d_serv = dist((ue.x, ue.y), (t.x, t.y))
            # crude interference distances: all other ON towers
            interferer_ds = [dist((ue.x, ue.y), (o.x, o.y)) for o in towers if o.on and o.id != t.id]
            sinr = phy.sinr_dl(d_serv_m=d_serv, interferer_ds_m=interferer_ds)
            rate = phy.rate_bps(sinr)
            if rate > best_rate:
                best_rate = rate
                best_tid = t.id
        ue.serving = best_tid

# Convenience printers

def summarize_ue(ue: UE, towers: List[Tower], phy_map: dict[int, PhysicalLayer]) -> str:
    if ue.serving is None:
        return f"UE{ue.id}: not attached"
    t = next(tt for tt in towers if tt.id == ue.serving)
    phy = phy_map[t.id]
    d_serv = dist((ue.x, ue.y), (t.x, t.y))
    interferer_ds = [dist((ue.x, ue.y), (o.x, o.y)) for o in towers if o.on and o.id != t.id]
    sinr_dl = phy.sinr_dl(d_serv_m=d_serv, interferer_ds_m=interferer_ds)
    sinr_ul = phy.sinr_ul(d_serv_m=d_serv)
    r_dl = phy.rate_bps(sinr_dl)
    r_ul = phy.rate_bps(sinr_ul)
    return (f"UE{ue.id} @({ue.x:.0f},{ue.y:.0f}) → {t.name or ('Tower'+str(t.id))} [{t.tech.name}]\n"
            f"  d={d_serv:.1f} m, DL SINR={lin_to_db(sinr_dl):.1f} dB, UL SINR={lin_to_db(sinr_ul):.1f} dB\n"
            f"  DL≈{r_dl/1e6:.1f} Mbps, UL≈{r_ul/1e6:.1f} Mbps")


# Demo scenario
def demo() -> None:
    # Tech & PHY engines per tower (could mix LTE & NR)
    towers: List[Tower] = [
        Tower(id=0, tech=NR_100, x=200.0, y=300.0, name="NR-Macro-A"),
        Tower(id=1, tech=NR_100, x=600.0, y=300.0, name="NR-Macro-B"),
        Tower(id=2, tech=LTE_20, x=400.0, y=150.0, name="LTE-SmallCell"),
    ]
    phy_map: dict[int, PhysicalLayer] = {t.id: PhysicalLayer(t.tech) for t in towers}

    # UEs
    ues: List[UE] = [
        UE(id=0, x=150.0, y=250.0),
        UE(id=1, x=500.0, y=350.0),
        UE(id=2, x=650.0, y=140.0),
    ]

    # Star-attach by best expected DL rate
    attach_star(ues, towers, phy_map)

    print("=== Minimal PHY Snapshot (Star Topology) ===")
    for ue in ues:
        print(summarize_ue(ue, towers, phy_map))

if __name__ == "__main__":
    demo()
