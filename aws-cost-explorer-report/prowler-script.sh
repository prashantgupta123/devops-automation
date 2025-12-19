#!/bin/bash

virtualenv -p python3 venv
source venv/bin/activate
pip install --upgrade pip
pip install prowler

# Check if account_details.json exists
if [[ ! -f "account_details.json" ]]; then
    echo "Error: account_details.json not found"
    exit 1
fi

# Read and process each account
jq -c '.[]' account_details.json | while read -r account; do
    account_id=$(echo "$account" | jq -r '.accountId')
    role_name=$(echo "$account" | jq -r '.roleName')
    
    # Filter regions (exclude "global" and "NoRegion")
    regions=$(echo "$account" | jq -r '.regions[]' | grep -v -E '^(global|NoRegion)$' | tr '\n' ' ')
    
    if [[ -n "$regions" ]]; then
        echo "Running prowler for account: $account_id"
        mkdir -p "$account_id"
        prowler aws --profile "$account_id"_"$role_name" --region $regions --output-format csv --output-filename "$account_id" --output-directory "$account_id" --compliance aws_foundational_security_best_practices_aws aws_well_architected_framework_security_pillar_aws aws_well_architected_framework_reliability_pillar_aws
    else
        echo "No valid regions for account: $account_id"
    fi
done

deactivate
