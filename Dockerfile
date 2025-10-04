FROM python:3.13-trixie AS dev

# Install needed linux packages
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    iproute2 \
    iptables \
    nftables \
    iputils-ping \
    procps \
    curl \
    tcpdump \
    net-tools \
    ethtool \
    dnsutils \
    socat \
    netcat-traditional \
    vim \
    nano \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Copy source code into the container at /src
WORKDIR /src/
COPY src/ .

# Install python packages
RUN pip install -r requirements.txt
