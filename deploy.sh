#!/bin/bash

echo "nohup python3 /root/discum/forward_bot.py > /dev/null 2>&1 &" >> /etc/rc.d/rc.local
