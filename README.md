# Cellular Network Simulator

## Project Setup

This project requires the following:
- [Docker](https://docs.docker.com/desktop/)
    - Windows will require installation of [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) for running linux containers
- IDE Supporting [Devcontainers](https://containers.dev) (i.e VS Code)
    - [VS Code Devcontainer Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Developing with Devcontainers

Devcontainers allow an IDE to connect directly to a docker container allowing you to develop the code right in the docker environment.
Any changes made in the devcontainer will be saved to your local device.
If you are using an IDE other than VS Code, please reference the devcontainer documentation for your IDE.

To run this devcontainer in VS Code follow these steps:
1. Ensure that Docker is installed and running
1. Install the [VS Code Devcontainer Extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
1. Clone this repo locally
1. Open the repo in VS Code
1. VS Code may show a pop-up to build and reopen in a devcontainer, you can click that to build and open the repo in VS Code in that container
1. Otherwise, you may access the command palette (i.e. `cmd+shift+p` or `ctrl_shift+p`) to search and run:
```text
Dev Containers: Rebuild and Reopen in Container
```

This should build the docker container locally on your machine, launch it and connect your local VS Code into the container at the root of this repo.
You can verify that you are in the devcontainer by checking the lower left corner of VS Code for "Dev Container: CellNetSim @ desktoplinux" or something similar.

#### Exiting a Devcontainer

When you need to exit the devcontainer (i.e. to perform git operations locally), you may run:
```text
Dev Containers: Reopen Folder Locally
```

#### Reusing a Devcontainer

After building the container once, you may reuse it by opening the command palette and running:
```text
Dev Containers: Reopen in Container
```

This avoids needlessly building the container each time you open the repo.

#### Rebuilding the Devcontainer

If you *need* to update the Devcontainer (I.e. added to the Dockerfile or added packages to requirements.txt), then you can simply open the command palette to search and run:
```text
Dev Containers: Rebuild and Reopen in Container
```

### Running in Docker

This documentation assumes that the project is simply being run, not being actively developed in Docker.
You may run this project in Docker following these steps:
- *Note*: Apple Silicon macs (i.e. M1-M4) should set their default architecture for this project to AMD64, prior to running commands in Docker:
```bash
export DOCKER_DEFAULT_PLATFORM=linux/amd64
```

1. Build the container:
```bash
docker build . -f Dockerfile -t cellnetsim:latest
```
1. Run the container, with capabilities for TUN/TAP:
```bash
docker run --rm -it --cap-add=NET_ADMIN --cap-add=NET_RAW --cap-add=SYS_ADMIN --device=/dev/net/tun:/dev/net/tun --privileged cellnetsim:latest bash
```

You can then interact with this container directly via terminal.

### Running the App
You can run the app for development from within the container by following these steps:
1. Open the src directory:
    ```bash
    cd src
    ```
1. Launch uvicorn with the --reload parameter for live reloading (good for interactive development):
    ```bash
    uvicorn main:app --reload
    ```

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
