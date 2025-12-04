#!/bin/bash

if [[ "$1" == "list" || "$1" == "-l" ]]; then
    echo "gateway"
    ip netns list | awk -F'-' '{print$2}' | tail -n +2
    exit 0
elif [[ "$1" == "gateway" ]]; then
    echo "now in gateway!"
    ip netns exec $( ip netns list | head -n 1 | awk '{print$1}') bash
    echo "exiting gateway..."
else
    IP=$1
    echo "now in UE with ip: $IP!"
    ip netns exec cab-$IP bash
    echo "exiting UE..."
fi
