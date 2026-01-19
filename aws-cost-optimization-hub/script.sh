#!/bin/bash
set -xe

python3 --version
python3 -m venv python-venv
source python-venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python --version
pip --version

python function.py

deactivate
rm -rf python-venv
echo "Job Completed Successfully"
