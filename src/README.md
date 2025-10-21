# Wireless Network Simulator (4G/5G)

This code simulates a wireless network with base stations (towers) and user devices (phones) to calculate signal strength, interference, and data rates.

## What This Code Does

We have: (feel free to play with the number)
- **3 Towers**: 2 big 5G towers + 1 small LTE tower
- **3 Phones**: Users trying to connect to the best tower
- **Goal**: Calculate which tower each phone should connect to for the best signal

## Key Concept

### 1. **Signal Strength** 
- Gets weaker the farther you are from the tower
- Measured in dBm
### 2. **Path Loss**
- How much the signal weakens as it travels through air
- Formula: `PL = 20*log10((4*π*distance)/wavelength)`


### 3. **Shadow Fading**
- Random signal variations due to buildings, trees, weather
- Simulated with random numbers

### 4. **SINR (Signal-to-Interference Ratio)**
- How good your signal is compared to interference from other towers
- Higher SINR = better connection = faster internet

### 5. **Data Rate**
- How fast you can download/upload data
- Based on Shannon's formula: `Rate = efficiency × bandwidth × log2(1 + SINR)`

## Code Structure


#### Constant Explanations:
- **`BACKGROUND_NOISE`**: Thermal noise floor at room temperature
- **`PATHLOSS_N`**: How quickly signal weakens with distance (5.0 = urban environment)
- **`SHADOW_SIGMA_DB`**: Random signal variations due to obstacles (6 dB is typical for urban)
- **`MIN_DISTANCE_M`**: Prevents division by zero in path loss calculations
- **`BS_GAIN_DBI`**: Tower pantennas amplify signals (15 dBi = good directional antenna)
- **`UE_GAIN_DBI`**: Phone antennas (0 dBi = typical omnidirectional antenna)
- **`BS_TX_POWER_DBM`**: Tower power (40 dBm = 10 Watts, typical for macro cells)
- **`UE_TX_POWER`**: Phone power (23 dBm = 200 mW, typical for mobile devices)
- **`RNG_SEED`**: Makes random shadow fading reproducible for testing

### Main Classes

#### `TechProfile`
- Defines technology settings (LTE vs 5G)
- **LTE**: 20 MHz bandwidth, 2.6 GHz frequency
- **5G**: 100 MHz bandwidth, 3.5 GHz frequency

#### `PhysicalLayer`
- Does all the math calculations
- **`pathloss_db()`**: Calculates how much signal is lost over distance
- **`rx_power_dbm()`**: Calculates received signal strength
- **`sinr_dl()`**: Calculates downlink signal quality
- **`rate_bps()`**: Calculates data rate

#### `TechProfile`
- **Purpose**: Defines technology settings for different wireless standards
- **Attributes**:
  - `name`: Technology name (e.g., "LTE-20MHz", "NR-100MHz")
  - `carrier_freq`: Radio frequency in Hz (e.g., 2.6 GHz for LTE, 3.5 GHz for 5G)
  - `bandwidth_hz`: Channel bandwidth in Hz (e.g., 20 MHz for LTE, 100 MHz for 5G)
  - `eta_eff`: Efficiency factor (0.5 for LTE, 0.6 for 5G)
- **Predefined instances**:
  - `LTE_20`: LTE with 20 MHz bandwidth
  - `NR_100`: 5G NR with 100 MHz bandwidth

#### `PhysicalLayer`
- **Purpose**: Performs all the wireless physics calculations
- **Key methods**:
  - `pl1m_db()`: Calculates free space path loss at 1 meter
  - `pathloss_db(d_m)`: Calculates total path loss including shadow fading
  - `rx_power_dbm(tx_dbm, tx_gain, rx_gain, distance)`: Calculates received signal strength
  - `sinr_dl(d_serv_m, interferer_ds_m)`: Calculates downlink SINR (tower to phone)
  - `sinr_ul(d_serv_m, cochannel_ue_ds_m)`: Calculates uplink SINR (phone to tower)
  - `rate_bps(sinr_linear)`: Calculates data rate using Shannon's formula

#### `Tower`
- **Purpose**: Represents a base station (cell tower)
- **Attributes**:
  - `id`: Unique identifier
  - `tech`: Technology profile (LTE or 5G)
  - `x, y`: 2D coordinates on the map
  - `on`: Whether the tower is active (True/False)
  - `name`: Human-readable name (e.g., "NR-Macro-A")

#### `UE` (User Equipment)
- **Purpose**: Represents a user device (phone, tablet, etc.)
- **Attributes**:
  - `id`: Unique identifier
  - `x, y`: 2D coordinates on the map
  - `serving`: ID of the tower this UE is connected to

#### Helper Functions
- **`dist(a, b)`**: Calculates 2D distance between two points using Pythagorean theorem
- **`attach_star(ues, towers, phy_map)`**: Connects each UE to the best tower based on expected data rate
- **`summarize_ue(ue, towers, phy_map)`**: Creates a formatted string showing UE connection details
- **`demo()`**: Main simulation function that creates towers, UEs, and runs the simulation

## How It Works

1. **Create towers and phones** with positions
2. **For each phone**:
   - Calculate signal strength from each tower
   - Account for interference from other towers
   - Choose the tower with best expected data rate
3. **Print results**: Show which tower each phone connects to and expected speeds

## Example Output
```
UE0 @(150,250) → NR-Macro-A [NR-100MHz]
  d=70.7 m, DL SINR=-20.5 dB, UL SINR=-26.0 dB
  DL≈0.8 Mbps, UL≈0.2 Mbps
```

This means:
- Phone 0 connects to 5G tower A
- Distance: 70.7 meters
- Downlink speed: ~0.8 Mbps
- Uplink speed: ~0.2 Mbps

## Key Formulas

### Free Space Path Loss
```
PL(dB) = 20*log10((4*π*distance)/wavelength)
```
- **distance**: How far from tower
- **wavelength**: Speed of light / frequency

### Received Power
```
Received Power = Transmit Power + TX Gain + RX Gain - Path Loss
```

### Data Rate (Shannon)
```
Rate = efficiency × bandwidth × log2(1 + SINR)
```

## Running the Code

```bash
python layer1PHY.py
```

The code will automatically:
1. Create 3 towers and 3 phones
2. Calculate best connections
3. Print a summary table

## What Each Number Means

- **SINR**: Signal quality (higher = better)
- **Distance**: How far from tower (shorter = better)
- **Mbps**: Internet speed (higher = faster)
- **dBm**: Signal strength (closer to 0 = stronger)


