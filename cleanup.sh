#!/bin/bash

find . -type d -name ".venv"
find . -type d -name ".venv" -exec rm -rf {} +
find . -type d -name "venv"
find . -type d -name "venv" -exec rm -rf {} +
find . -type d -name "python-venv"
find . -type d -name "python-venv" -exec rm -rf {} +
find . -type d -name "__pycache__"
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name "node_modules"
find . -type d -name "node_modules" -exec rm -rf {} +
find . -type d -name ".terraform"
find . -type d -name ".terraform" -exec rm -rf {} +
