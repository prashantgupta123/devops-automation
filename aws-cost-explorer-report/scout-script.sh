#!/bin/bash

virtualenv -p python3 venv
source venv/bin/activate
pip install --upgrade pip
pip install scoutsuite

# Check if account_details.json exists
if [[ ! -f "account_details.json" ]]; then
    echo "Error: account_details.json not found"
    exit 1
fi

# Read and process each account
jq -c '.[]' account_details.json | while read -r account; do
    account_id=$(echo "$account" | jq -r '.accountId')
    access_key=$(echo "$account" | jq -r '.accountKeys.access_key')
    secret_key=$(echo "$account" | jq -r '.accountKeys.secret_access_key')
    session_token=$(echo "$account" | jq -r '.accountKeys.key_session_token')
    
    # Filter regions (exclude "global" and "NoRegion")
    regions=$(echo "$account" | jq -r '.regions[]' | grep -v -E '^(global|NoRegion)$' | tr '\n' ' ')
    
    if [[ -n "$regions" ]]; then
        echo "Running scout for account: $account_id"
        mkdir -p "$account_id"
        scout aws --access-key-id "$access_key" --secret-access-key "$secret_key" --session-token "$session_token" --regions $regions --report-dir "$account_id" --report-name "$account_id" --no-browser --force
    else
        echo "No valid regions for account: $account_id"
    fi
done

deactivate
