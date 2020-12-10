#!/bin/bash
cp ./forwardbot.service /etc/systemd/system

systemctl enable forwardbot.service

