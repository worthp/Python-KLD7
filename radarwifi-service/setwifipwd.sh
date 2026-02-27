#!/bin/bash

action="$1"

#nmcli -f general.connection  device show wlan0
#GENERAL.CONNECTION:                     netplan-wlan0-WIFICD2D92-5G
if [ "${action}" = "fix" ];  then
	nmcli con modify netplan-wlan0-WIFICD2D92-5G wifi-sec.psk 'YPUQNEGILDS2MEQN'
	nmcli conn down radar-ap
elif [ "${action}" = "break" ]; then
	nmcli con modify netplan-wlan0-WIFICD2D92-5G wifi-sec.psk 'breakitthepassword'
fi
systemctl restart NetworkManager
