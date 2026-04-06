# Python-KLD7
KLD7 radar  controller in python
# Features
- speed tracking with image capture based on speed thresholds
- browser based front end
  - allows radar configuration
  - provides statistics
  - provides access to images
  - provides access to network settings
  - provides some host control
## Hardware
- KLD-7 Radar
  - communicates over uart
  - for Pi models that don't expose full uart to gpio header
    - disable bluetooth
    - enable uart
    - disable serial console
    - radar cannot be wired until after first boot. the boot process fails if there is signal on the rx/tx lines.
- RTC clock module
  - Pi loses date/time without wifi
  - easiest to add rtc clock overlay 
# Pi setup
## RPI Imager Trixie Lite 64 bit
## Remount sd card 
- copy setup/config.txt to boot partition
- copy setup/user-data to boot partition
- eject media
## wire rtc module (can be done later)
## insert sd card into pi and power
- this takes about 20 minutes. it does an apt update/upgrade and then installs necessary packages for operation.
- *Note: Trixie uses cloud-init for first boot and cloud-init is a bit quirky. One of the quirks is that it will offer a login prompt even though user configuration is not complete.*
- Confirmation of successful configuration is determined by cloud-init final stage being complete.
- After successful first boot, power off the the pi and wire the radar
# Operation
- When the unit first boots it is wifi AP mode. You will need to connect to the AP ssid which is radar-ap. After connected to the network, point a browser to http://10.41.0.1:8080. You should see the home page
## Radar Control
- Control the radar
## Readings
- Look at the readings
## Stats
- Look at the stats
## Host control
- Control the host
## Images
- Look at the images
- Take a pic