#!/usr/bin/env bash

# setup a debian/ubuntu host machine to provide internet for USB device connected
#   this should be run ONCE on the host machine

# need to be root
if [ "$(id -u)" != "0" ]; then
    echo "Must be run as root"
    exit 1
fi

if [ "$(uname -s)" != "Linux" ]; then
    echo "Only works on Linux!"
    exit 1
fi

function remove_if_exists() {
    # remove a file if it exists
    FILEPATH="$1"
    if [ -f "$FILEPATH" ]; then
        echo "found ${FILEPATH}, removing"
        rm "$FILEPATH"
    fi
}

function append_if_missing() {
    # append string to file only if it does not already exist in the file
    STRING="$1"
    FILEPATH="$2"
    grep -q "$STRING" "$FILEPATH" || {
        echo "appending \"$STRING\" to $FILEPATH"
        echo "$STRING" >> "$FILEPATH"
        return 1
    }
    echo "Already found \"$STRING\" in $FILEPATH"
    return 0
}

set -e  # bail on any errors

# install needed packages
export DEBIAN_FRONTEND=noninteractive
apt install -y git htop build-essential cmake python3 python3-dev python3-pip iptables adb android-sdk-platform-tools-common iptables-persistent
python3 -m pip install --break-system-packages virtualenv nuitka ordered-set
python3 -m pip install --break-system-packages git+https://github.com/superna9999/pyamlboot

# fix usb enumeration when connecting superbird in maskroom mode
echo '# Amlogic S905 series can be booted up in Maskrom Mode, and it needs a rule to show up correctly' > /etc/udev/rules.d/70-carthing-maskrom-mode.rules
echo 'SUBSYSTEM=="usb", ENV{DEVTYPE}=="usb_device", ATTR{idVendor}=="1b8e", ATTR{idProduct}=="c003", MODE:="0666", SYMLINK+="worldcup"' >> /etc/udev/rules.d/70-carthing-maskrom-mode.rules

# prevent systemd / udev from renaming usb network devices by mac address
remove_if_exists /lib/systemd/network/73-usb-net-by-mac.link
remove_if_exists /lib/udev/rules.d/73-usb-net-by-mac.rules

#  allow IP forwarding
append_if_missing "net.ipv4.ip_forward = 1" /etc/sysctl.conf || {
    sysctl -p  # reload from conf
}


# forwarding rules
mkdir -p /etc/iptables

iptables -P FORWARD ACCEPT
iptables -A FORWARD -o eth0 -i eth1 -s 192.168.7.0/24 -m conntrack --ctstate NEW -j ACCEPT
iptables -A FORWARD -o eth0 -i eth1 -s 192.168.7.0/24 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A POSTROUTING -t nat -j MASQUERADE -s 192.168.7.0/24

iptables-save > /etc/iptables/rules.v4

# write the config
mkdir -p /etc/network/interfaces.d/

cat << EOF > /etc/network/interfaces.d/usb0
allow-hotplug usb0
iface usb0 inet static
	address 192.168.7.1
	netmask 255.255.255.0
EOF

echo "Need to reboot for all changes to take effect"
