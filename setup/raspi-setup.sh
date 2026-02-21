#!/usr/bin/bash
#
cd ~
sudo apt update
sudo apt upgrade -y

# move the primary uart to gpio pins
# echo 'dtoverlay=disable-bt' >> /boot/firmware/config.txt
# cli raspi-config to disable console from serial
#
# turn off wifi power_save
# sudo crontab -e and add in the reboot thing to disable wifi power_save

mkdir .ssh > /dev/null 2>&1
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ""

sudo apt install -y minicom
sudo apt install -y neovim
sudo apt install -y git
git config --global user.name "Patrick Worth"
git config --global user.email "worthp@worthconsulting.com"

mkdir -p .pyenvs/default
python -m venv --system-site-packages .pyenvs/default
chmod 755 ~/.pyenvs/default/bin/activate


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

sudo apt install -y python3-serial
sudo apt install -y python3-picamera2 --no-install-recommends


mkdir -p devel/software
