#!/bin/bash

# Update package lists
sudo yum update

# Upgrade installed packages
sudo yum upgrade -y

# Install python3-pip
sudo yum install python3-pip -y
