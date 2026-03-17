#!/bin/bash
# Cloud-init script for inventory-api compute instance
# Installs Docker and Docker Compose for container-based deployment

set -e

# Update system packages
yum update -y

# Install Docker
yum install -y yum-utils
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Add opc user to docker group
usermod -aG docker opc

# Install Python 3.9+ for local development/debugging
yum install -y python39 python39-pip

# Open firewall for application port
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=443/tcp
firewall-cmd --reload

echo "Cloud-init completed successfully for inventory-api"
