# AWS SSO Account Credentials Extractor

Automates AWS SSO authentication and extracts account credentials for multiple accounts and roles.

## Prerequisites

- Python 3.13+
- boto3 library
- AWS SSO configured

## Installation

```bash
pip install boto3
```

## Configuration

Update the following variables in `function.py`:
- `REGION`: Your Identity Center region
- `START_URL`: Your SSO start URL
- `project_name`: Your project name

## Usage

```bash
python function.py
```

1. Script will display a login URL
2. Complete authentication in browser
3. Account credentials saved to `account_details.json`

## Output Format

```json
[
    {
        "cloudName": "AWS",
        "regionName": "us-east-1",
        "projectName": "MyProject",
        "accountId": "999999999999",
        "accountName": "Production",
        "accountKeys": {
            "profile_name": "",
            "role_arn": "",
            "access_key": "AKIA...",
            "secret_access_key": "...",
            "key_session_token": "..."
        }
    }
]
```

## Functions

- `register_sso_client()` - Register SSO client
- `authorize_device()` - Start device authorization
- `get_access_token()` - Poll for access token
- `get_accounts_and_credentials()` - Extract account credentials
- `save_to_json()` - Save to JSON file
