#!/bin/bash

WLAN="en0"
ETH="en6"

# Set default values
prev_eth_status="Off"
prev_air_status="Off"

eth_status="Off"

# Determine previous ethernet status
# If file prev_eth_on exists, ethernet was active last time we checked
if [ -f "/var/tmp/prev_eth_on" ]; then
    prev_eth_status="On"
fi

# Determine same for WiFi status
# File is prev_air_on
if [ -f "/var/tmp/prev_air_on" ]; then
    prev_air_status="On"
fi

# Check actual current ethernet status
if [ "`ifconfig ${ETH} | grep \"status: active\"`" != "" ]; then
    eth_status="On"
fi

# And actual current WiFi status
air_status=`/usr/sbin/networksetup -getairportpower ${WLAN} | awk '{ print $4 }'`

# If any change has occured. Run external script (if it exists)
if [ "$prev_air_status" != "$air_status" ] || [ "$prev_eth_status" != "$eth_status" ]; then
    if [ -f "./statusChanged.sh" ]; then
    "./statusChanged.sh" "$eth_status" "$air_status" &
    fi
fi

# Determine whether ethernet status changed
if [ "$prev_eth_status" != "$eth_status" ]; then

    if [ "$eth_status" = "On" ]; then
        osascript -e "display notification \"Ethernet network detected\" with title \"Network connection\" subtitle \"Switching WiFi off\""
        /usr/sbin/networksetup -setairportpower ${WLAN} off
        rm -f /var/tmp/prev_air_on
    else
        osascript -e "display notification \"Ethernet network down\" with title \"Network connection\" subtitle \"Switching WiFi on\""
        /usr/sbin/networksetup -setairportpower ${WLAN} on && \
        touch /var/tmp/prev_air_on
    fi

# If ethernet did not change
else

    # Check whether WiFi status changed
    # If so it was done manually by user
    if [ "$prev_air_status" != "$air_status" ]; then
        if [ "$air_status" = "On" ]; then
            touch /var/tmp/prev_air_on
            osascript -e "display notification \"WiFi network manually enabled\" with title \"Network connection\" subtitle \"Ethernet is $eth_status\""
        else
            rm -f /var/tmp/prev_air_on
            osascript -e "display notification \"WiFi network manually disabled\" with title \"Network connection\""
        fi

    fi

fi

# Update ethernet status
if [ "$eth_status" = "On" ]; then
    touch /var/tmp/prev_eth_on
else
    rm -f /var/tmp/prev_eth_on
fi

exit 0
