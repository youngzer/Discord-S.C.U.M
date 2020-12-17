#!/usr/bin/env bash
python3 -m compileall -f -x "setup.py|__init__.py|__version__.py" ./discum/
mkdir -p ./build

find ./discum -name "*.pyc" -exec cp '{}' ./build/ \;
cp bot.cfg ./build/
cp deploy.sh ./build/
tar czf forwardbot.tar.gz ./build/*
rm -rf ./build


