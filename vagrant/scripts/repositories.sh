#!/bin/sh -e

echo "Package repositories provision step"

# Install apt sources
cat << EOF > /etc/apt/sources.list
##### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ### WARNING #####
#
# This file is managed via automatic vagrant provision, DO NOT EDIT THIS FILE
# DIRECTLY, it is going to be overridden by the next provision run!
#
##### WARNING ### WARNING ### WARNING ### WARNING ### WARNING ### WARNING #####

# Ubuntu xenial
deb http://archive.ubuntu.com/ubuntu/ xenial main restricted universe multiverse
deb-src http://archive.ubuntu.com/ubuntu/ xenial main restricted universe multiverse

# Ubuntu updates
deb http://archive.ubuntu.com/ubuntu/ xenial-updates main restricted universe multiverse
deb-src http://archive.ubuntu.com/ubuntu/ xenial-updates main restricted universe multiverse

# Ubuntu backports
deb http://archive.ubuntu.com/ubuntu/ xenial-backports main restricted universe multiverse
deb-src http://archive.ubuntu.com/ubuntu/ xenial-backports main restricted universe multiverse

# Ubuntu partners
deb http://archive.canonical.com/ubuntu xenial partner
deb-src http://archive.canonical.com/ubuntu xenial partner

# Security Updates
deb http://security.ubuntu.com/ubuntu xenial-security main restricted universe multiverse
deb-src http://security.ubuntu.com/ubuntu xenial-security main restricted universe multiverse
EOF

# Generate locales
locale-gen en_US en_US.UTF-8 de_AT.UTF-8
update-locale LANG=en_US.UTF-8 LC_CTYPE=en_US.UTF-8

# Install administration packages
apt-get update
apt-get install -y software-properties-common aptitude

# UbuntuGIS Unstable
add-apt-repository ppa:ubuntugis/ubuntugis-unstable

# Upgrade packages
aptitude update
#aptitude safe-upgrade -y
