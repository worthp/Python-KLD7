#!/bin/bash

nmcli connection show --active | grep wlan0 > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo 'we are down'
  sudo nmcli device wifi  hotspot con-name radar-ap ssid radar-ap band bg password password
else
  echo 'we are up'
fi
