#!/usr/bin/env bash

# setup a debian/ubuntu host machine to provide internet for USB device connected
#   this should be run ONCE on the host machine

# Note: I have not gotten this to work yet, something in routing is not quite right
#   It might be that we need to do additional route rules device-side

# need to be root
if [ "$(id -u)" != "0" ]; then
    echo "Must be run as root"
    exit 1
fi

# prevent systemd / udev from renaming usb network devices by mac address
rm /lib/systemd/network/73-usb-net-by-mac.link
#  allow IP forwarding
echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.conf
sysctl -p  # reload from conf
# forwarding rules
iptables -P FORWARD ACCEPT
iptables -A POSTROUTING -t nat -j MASQUERADE -s 192.168.7.0/24
mkdir /etc/iptables
iptables-save > /etc/iptables/rules.v4

# write the config
mkdir -p /etc/network/interfaces.d/
cat << EOF >> /etc/network/interfaces.d/usb0
allow-hotplug usb0
iface usb0 inet static
	address 192.168.7.1
	netmask 255.255.255.0
EOF
