#!/bin/bash
NETNS=$1
SUBNET=$2


ip link add cab-inet type veth peer name cab-ue-inet 
ip link set cab-ue-inet netns $NETNS

ip addr add 10.200.0.1/24 dev cab-inet
ip link set cab-inet up

ip netns exec $NETNS ip addr add 10.200.0.2/24 dev cab-ue-inet 
ip netns exec $NETNS ip link set cab-ue-inet up

ip netns exec $NETNS ip route add default via 10.200.0.1


sysctl -w net.ipv4.ip_forward=1

# allow forwarding and masquerade
EGIF=$(ip route show default | awk '/default/ {print $5}')
iptables -t nat -A POSTROUTING -s 10.200.0.0/24 -o "$EGIF" -j MASQUERADE

# forwarding rules for cab
EGIF=$(ip -n  $NETNS route show default | awk '/default/ {print $5}')
ip netns exec $NETNS iptables -t nat -A POSTROUTING -s $SUBNET -o "$EGIF" -j MASQUERADE
