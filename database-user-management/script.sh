#!/bin/bash
set -xe

python3 -m pip install --upgrade pip
pip3 install -r requirements.txt

python3 database.py \
--action "REMOVE" \
--name "Prashant Gupta" \
--email "prashant.gupta@cloudplatform.com" \
--project "project" \
--access_level "READ_WRITE_ADMIN" \
--database "dev_project" \
--database_expiry "NA"
