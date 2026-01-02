#!/bin/bash
set -xe

python3 -m pip install --upgrade pip
pip3 install -r requirements.txt

python3 funtion.py
