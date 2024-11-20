#!/bin/bash

install() {
  VERSION="v1.0.1"
  BIN_URL="https://github.com/bednark/dns-proxy/releases/download/$VERSION/dns-proxy"
  SERVICE_FILE="/etc/systemd/system/dns-proxy.service"

  echo "Installing dns-proxy version: $VERSION"
  wget -O /usr/local/bin/dns-proxy $BIN_URL
  chmod 755 /usr/local/bin/dns-proxy

  echo "Creating configuration directory"
  mkdir -p /etc/dns-proxy/

  if [[ ! -f /etc/dns-proxy/health-check.yml ]]; then
    echo "Creating health-checks.yml"
    cat <<EOF > /etc/dns-proxy/health-check.yml
health_checks:
  - domain: example.com
    ip: 192.168.1.1
EOF
  else
    echo "Configuration file already exists"
  fi

  if [[ ! -f $SERVICE_FILE ]]; then
    echo "Creating service file"
    cat <<EOF > $SERVICE_FILE
[Unit]
Description=DNS Proxy with Health Checks
After=network.target

[Service]
ExecStart=/usr/local/bin/dns-proxy
Restart=always

[Install]
WantedBy=multi-user.target
EOF
  else
    echo "Service file already exists"
  fi
  chmod 644 $SERVICE_FILE
  systemctl daemon-reload
  systemctl enable dns-proxy
  systemctl start dns-proxy
}

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

install