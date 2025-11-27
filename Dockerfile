######################### Rust Build ##############################
FROM python:3.13-trixie AS builder

# Wheel build deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc g++ make pkg-config libssl-dev \
 && rm -rf /var/lib/apt/lists/*

# Install Rust
ENV RUSTUP_HOME=/usr/local/rustup \
    CARGO_HOME=/usr/local/cargo \
    PATH=/usr/local/cargo/bin:$PATH
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
    | sh -s -- -y --profile minimal --default-toolchain stable

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir maturin

WORKDIR /app
COPY src/layer3/ ./layer3/

RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/usr/local/cargo/git \
    maturin build \
      --release \
      -m layer3/Cargo.toml \
      --interpreter python3 \
      -o /wheels



######################### Runtime #################################
FROM python:3.13-trixie AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libssl3 ca-certificates iproute2 netcat-openbsd telnet iperf iptables iputils-ping tcpdump vim && \ 
    rm -rf /var/lib/apt/lists/*

# Install Firefox and dependencies for Wayland GUI + audio
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        firefox-esr \
        mesa-utils \
        libgl1 \
        libglvnd0 \
        libcanberra-gtk3-module \
        fonts-dejavu-core \
        dbus \
        libdbus-glib-1-2 \
        libasound2 \
        pulseaudio \
        && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Environment variables for Firefox on Wayland
ENV GTK_THEME=Adwaita \
    MOZ_ENABLE_WAYLAND=1 \
    MOZ_DISABLE_RDD_SANDBOX=1

# Bring layer3 wheels from the builder stage
COPY --from=builder /wheels /wheels

COPY src/requirements.txt ./

# Use a pip cache mount for faster iterative installs
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir /wheels/*.whl \
 && if [ -s requirements.txt ]; then \
      pip install --no-cache-dir -r requirements.txt; \
    fi

COPY src/*.py ./
COPY src/layer1 ./layer1
COPY src/static ./static
COPY src/templates ./templates

CMD ["python", "main.py"]
