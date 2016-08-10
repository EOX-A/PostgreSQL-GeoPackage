#!/bin/sh -e

echo "User custom provision step"

# Add your custom configuration below.

# Add alias
if ! grep -Fxq "alias l=\"ls -lah\"" /root/.bashrc ; then
    cat << EOF >> /root/.bashrc
alias l="ls -lah"
EOF
    cat << EOF >> /home/vagrant/.bashrc
alias l="ls -lah"
EOF
fi

# Generate locales
locale-gen en_US en_US.UTF-8 de_AT.UTF-8
