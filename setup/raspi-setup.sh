#!/usr/bin/bash
#

# make sure where we are
cd ~

# standard
sudo apt update
sudo apt upgrade -y

# move the primary uart to gpio pins so we radar can use them
echo 'dtoverlay=disable-bt' | sudo tee --append /boot/firmware/config.txt

# cli raspi-config to disable console from serial
sudo /usr/bin/raspi-config nonint do_serial_cons 1
#
# turn off wifi power_save. # doing in cron just because. could be a systemd service as well
#
sudo crontab - << EOF
@reboot /usr/sbin/iw wlan0 set power_save off
EOF


# disable cloud-init going forward
sudo touch /etc/cloud/cloud-init.disabled

# probably overkill but don't let cloud-init fuck with hostnames
sudo sed -i '/manage_etc_hosts: true/s//manage_etc_hosts: false/' /boot/firmware/user-data

# needed for radar to use serial
sudo apt install -y python3-serial

# used by radar for taking pics
sudo apt install -y python3-picamera2 --no-install-recommends

# in case serial comms are wonky require troubleshooting
sudo apt install -y minicom

# create virtual env for python so we can add non-system packages
mkdir -p .pyenvs/default
python -m venv --system-site-packages .pyenvs/default
chmod 755 ~/.pyenvs/default/bin/activate
#
# for creating overlay on pics
~/.pyenvs/default/bin/pip install opencv-python-headless

# put code where systemd service will look for it
# maybe package this one day
wget https://github.com/worthp/Python-KLD7/archive/refs/tags/latest.zip -O radar.zip
unzip radar.zip

mkdir radar-service
mv Python-KLD7-latest/radar/* radar-service
mkdir radar-service/images

# install systemd radar service 
sudo cp Python-KLD7-latest/setup/radar.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl status radar

#
# development set up
# 
sudo apt install -y git

# this is for connecting to git
git config --global user.name "Patrick Worth"
git config --global user.email "worthp@worthconsulting.com"

# creating ssh keys to be able to connect to git and whereever else
mkdir .ssh > /dev/null 2>&1
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""

# personal prefs
cat << EOF > ~/.bash_aliases
set -o vi
alias r='fc -e -'
alias ll='ls -lrt'
alias l='ls -A'

# fucking python
~/.pyenvs/default/bin/activate

alias py='python'
alias pip='~/.pyenvs/default/bin/pip'
alias pip3='~/.pyenvs/default/bin/pip3'
alias python='~/.pyenvs/default/bin/python'
EOF

source ~/.bash_aliases

mkdir -p devel/software
