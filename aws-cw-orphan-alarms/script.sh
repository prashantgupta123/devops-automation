#!/bin/bash
set -xe

python3 --version
python3 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install --upgrade pip
python -m pip --version
python -m pip install -r requirements.txt
python main.py
deactivate
rm -rf .venv
echo "Job Completed Successfully"
