# Cellular Network Simulator

## Assignment description

### Physical
- Realistic physical layer implementation is not required.
- Mimic 4G/LTE and 5G data speeds and range.
- Define cell towers and user equipment (i.e., cellular phone)
- Form star topologies between cellular towers and user equipment

### Link / MAC
- Mimic 4G/LTE or 5G link layer when forming 
- Simulate link quality.
- Simulate transmission failure probabilities, implement up to N retransmissions; consider ACK/NACK delay.
- Simulate neighbor discovery algorithms.

### Network
- Implement topology formation based on physical positions.
- Consider handovers for nodes moving across cells.
- Consider connectivity restoration.
- Simulate the IP protocol.
- Facilitate inter-UE data transmission through IP address.
- Ignore PSTN connection and phone calls.

### Mobility
- UE models: Grid/Manhattan; walking (1–2 m/s) and vehicular (10–15 m/s).
- Topology events: cell on/off or small-cell move mid-run; optional TDD pattern change for one sector.
- Logs: Try transmission success/failure rates, outage duration, time-to-restore.

### GUI
- Coverage heatmap
- Controls: toggle fallback access; trigger cell off/on; standard run controls.
- Panels: throughput, latency/miss rate.

### Experiments 
- E1 send data between different UEs through the IP network.
- E2 Move and UE between different cells
- E3 Turn off a station tower and let other towers take over given the coverage.

### Rubric (100 pts)
- PHY/MAC/Network fidelity — 22
- Alternate access (LTE/Wi-Fi) + selection policy — 5
- Topology change (cell on/off/move) implemented & analyzed — 5
- Connectivity restoration — 5
- Mobility integration — 6
- GUI completeness & clarity — 6
- Experimental design & statistics — 18
- Results & insights — 18
- Code quality & reproducibility — 10
- Presentation & Q&A — 5

### Deliverables (all projects)
- Code + README; design doc (up to 5 pp)
- experiment report (up to 5 p)
- demo (8–10 min)
- reproducible artifacts, configs, results CSV/plots, etc.
