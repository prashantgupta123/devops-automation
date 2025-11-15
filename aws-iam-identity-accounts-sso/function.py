import boto3
import time
import json
from configparser import ConfigParser


PROJECT_NAME = "MyProject"
REGION = "us-east-1"
START_URL = "https://d-9999999999.awsapps.com/start"

def register_sso_client():
    oidc = boto3.client("sso-oidc", region_name=REGION)
    reg = oidc.register_client(clientName="ReadOnly-Client", clientType="public")
    return oidc, reg["clientId"], reg["clientSecret"]

def authorize_device(oidc, client_id, client_secret):
    auth = oidc.start_device_authorization(
        clientId=client_id,
        clientSecret=client_secret,
        startUrl=START_URL
    )
    print("👉 Please log in here:", auth["verificationUriComplete"])
    return auth

def get_access_token(oidc, client_id, client_secret, device_code, interval):
    token = None
    while not token:
        try:
            token = oidc.create_token(
                clientId=client_id,
                clientSecret=client_secret,
                grantType="urn:ietf:params:oauth:grant-type:device_code",
                deviceCode=device_code,
            )
        except oidc.exceptions.AuthorizationPendingException:
            time.sleep(interval)
    print("✅ Login successful")
    return token["accessToken"]

def get_accounts_and_credentials(access_token):
    sso = boto3.client("sso", region_name=REGION)
    accounts = sso.list_accounts(accessToken=access_token)["accountList"]
    account_details = []
    
    for acct in accounts:
        print(f"Found account {acct['accountId']} {acct['accountName']}")
        
        roles = sso.list_account_roles(
            accessToken=access_token,
            accountId=acct["accountId"]
        )["roleList"]

        for role in roles:
            print(f"Using account {acct['accountId']} role {role['roleName']}")
            creds = sso.get_role_credentials(
                accessToken=access_token,
                accountId=acct["accountId"],
                roleName=role["roleName"]
            )["roleCredentials"]

            account_details.append({
                "cloudName": "AWS",
                "regionName": REGION,
                "projectName": PROJECT_NAME,
                "accountId": acct["accountId"],
                "accountName": acct["accountName"],
                "roleName": role["roleName"],
                "accountKeys": {
                    "profile_name": "",
                    "role_arn": "",
                    "access_key": creds["accessKeyId"],
                    "secret_access_key": creds["secretAccessKey"],
                    "key_session_token": creds["sessionToken"]
                }
            })
    
    return account_details

def save_to_json(account_details, filename="account_details.json"):
    with open(filename, "w") as f:
        json.dump(account_details, f, indent=4)
    print(f"✅ Account details saved to {filename}")

def create_aws_config(account_details, config_path="aws_config"):
    config = ConfigParser()
    
    for account in account_details:
        profile_name = f"{account['accountId']}_{account['roleName']}"
        config[f"{profile_name}"] = {
            "aws_access_key_id": account["accountKeys"]["access_key"],
            "aws_secret_access_key": account["accountKeys"]["secret_access_key"],
            "aws_session_token": account["accountKeys"]["key_session_token"]
        }
    
    with open(config_path, "w") as f:
        config.write(f)
    print(f"✅ AWS config created at {config_path}")

def main():
    oidc, client_id, client_secret = register_sso_client()
    auth = authorize_device(oidc, client_id, client_secret)
    access_token = get_access_token(oidc, client_id, client_secret, auth["deviceCode"], auth["interval"])
    account_details = get_accounts_and_credentials(access_token)
    save_to_json(account_details)
    create_aws_config(account_details)

if __name__ == "__main__":
    main()
