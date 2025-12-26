#!/bin/bash

read -r -p "Enter the environment (default) you want to run: " env
set -e

rm -rf .terraform
if [ "${env}" == "default" ]; then
	terraform init
	terraform workspace list
	terraform workspace select "${env}"
	terraform fmt .
	terraform validate
	terraform apply
else
	echo "Please enter correct environment"
fi
