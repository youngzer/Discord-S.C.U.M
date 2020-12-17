#!/bin/bash

echo "nohup pypy /root/forward_bot/forward_bot.py > /dev/null 2>&1 &" >> /etc/rc.d/rc.local
