#!/bin/bash
set -xe

python3 --version
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python --version
pip --version

python main.py

deactivate
rm -rf venv
echo "Job Completed Successfully"
