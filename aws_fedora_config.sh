#!/bin/bash

# Update package lists
sudo yum update

# Upgrade installed packages
sudo yum upgrade -y

# Install python3-pip
sudo yum install python3-pip -y

# Install git
sudo yum install git -y

# Fix for flask version
pip3 install --upgrade flask
