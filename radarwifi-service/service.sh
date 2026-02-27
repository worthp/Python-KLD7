#! /bin/bash

CONTROL_FILE="wifidown"

# monitor wlan connection
while true
do
	nmcli -f general.connection device show wlan0 | grep -- '--'
	if [ $? = 0 ]; then
		echo "wifi connection is down"
		if [ ! -e "${CONTROL_FILE}" ]; then
			touch ${CONTROL_FILE}
		else
			echo "wifi has not been connected for"
	else
		echo "wifi is up"
		rm ${CONTROL_FILE}
	fi

	sleep 2
done
