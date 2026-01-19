import json
import logging
import sys
from typing import Dict, List, Any
from AWSSession import get_aws_session

# Creating an object
logger = logging.getLogger()
# Setting the threshold of logger to DEBUG
logger.setLevel(logging.INFO)
# setting stdout for logging
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def load_config_files():
    """Load input.json and account_details.json files."""
    with open('input.json', 'r') as f:
        input_config = json.load(f)
    
    with open('account_details.json', 'r') as f:
        account_details = json.load(f)
    
    return input_config, account_details

def create_iam_policy_if_not_exists(iam_client, policy_config: Dict[str, Any], default_tags: Dict[str, str], account_info: Dict[str, str]) -> str:
    """Create IAM policy if it doesn't exist."""
    policy_name = policy_config['policy_name']
    
    try:
        # Check if policy exists
        response = iam_client.get_policy(PolicyArn=f"arn:aws:iam::{account_info['accountId']}:policy/{policy_name}")
        logger.info(f"Policy {policy_name} already exists")
        return response['Policy']['Arn']
    except iam_client.exceptions.NoSuchEntityException:
        pass
    
    # Load policy document
    with open(f"policy/{policy_config['policy_file']}", 'r') as f:
        policy_document = json.load(f)
    
    # Merge default tags with policy-specific tags
    tags = {**default_tags, 'Name': policy_name, **policy_config.get('tags', {})}
    
    # Create policy
    response = iam_client.create_policy(
        PolicyName=policy_name,
        PolicyDocument=json.dumps(policy_document),
        Description=policy_config['description'],
        Tags=[{'Key': k, 'Value': v} for k, v in tags.items()]
    )
    
    logger.info(f"Created policy {policy_name}")
    return response['Policy']['Arn']

def get_sso_instance_arn(sso_admin_client) -> str:
    """Get SSO instance ARN."""
    response = sso_admin_client.list_instances()

    if not response['Instances']:
        raise Exception("No IAM Identity Center instances found.")

    if len(response['Instances']) > 1:
        raise Exception("Multiple IAM Identity Center instances found. Please specify the correct instance.")
    
    logger.info(f"Identity Store ID: {response['Instances'][0]['IdentityStoreId']}")

    return response['Instances'][0]['InstanceArn']

def create_permission_set_if_not_exists(sso_admin_client, instance_arn: str, ps_config: Dict[str, Any], default_tags: Dict[str, str]) -> str:
    """Create permission set if it doesn't exist."""
    ps_name = ps_config['permission_set_name']
    
    try:
        # List existing permission sets
        paginator = sso_admin_client.get_paginator('list_permission_sets')
        for page in paginator.paginate(InstanceArn=instance_arn):
            for ps_arn in page['PermissionSets']:
                ps_details = sso_admin_client.describe_permission_set(
                    InstanceArn=instance_arn,
                    PermissionSetArn=ps_arn
                )
                if ps_details['PermissionSet']['Name'] == ps_name:
                    logger.info(f"Permission set {ps_name} already exists")
                    return ps_arn
    except Exception as e:
        logger.error(f"Error checking permission sets: {e}")
    
    # Merge default tags with Name tag
    tags = {**default_tags, 'Name': ps_name, **ps_config.get('tags', {})}
    
    # Create permission set
    response = sso_admin_client.create_permission_set(
        Name=ps_name,
        Description=ps_config['description'],
        InstanceArn=instance_arn,
        SessionDuration=ps_config['session_duration'],
        Tags=[{'Key': k, 'Value': v} for k, v in tags.items()]
    )
    
    ps_arn = response['PermissionSet']['PermissionSetArn']
    logger.info(f"Created permission set {ps_name}")
    
    # Attach AWS managed policies
    for policy_name in ps_config['aws_managed_policies']:
        sso_admin_client.attach_managed_policy_to_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=ps_arn,
            ManagedPolicyArn=f"arn:aws:iam::aws:policy/{policy_name}"
        )
    
    # Attach customer managed policies
    for policy_name in ps_config['customer_managed_policies']:
        sso_admin_client.attach_customer_managed_policy_reference_to_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=ps_arn,
            CustomerManagedPolicyReference={'Name': policy_name}
        )
    
    # Add inline policy if specified
    if ps_config['inline_policy']:
        with open(f"policy/{ps_config['inline_policy']}", 'r') as f:
            inline_policy = json.load(f)
        
        sso_admin_client.put_inline_policy_to_permission_set(
            InstanceArn=instance_arn,
            PermissionSetArn=ps_arn,
            InlinePolicy=json.dumps(inline_policy)
        )
    
    return ps_arn

def create_iam_identity_center_resources():
    """Main function to create IAM Identity Center permission sets and IAM policies."""
    input_config, account_details = load_config_files()
    
    # Create SSO admin session for org account
    org_session = get_aws_session(input_config['awsCredentials'])
    sso_admin_client = org_session.client('sso-admin', region_name=input_config['awsCredentials']['region_name'])
    instance_arn = get_sso_instance_arn(sso_admin_client)
    
    # Create IAM policies in member accounts
    for account in account_details:
        logger.info(f"Processing account: {account['accountName']}")
        
        # Create session for member account
        member_session = get_aws_session(account['accountKeys'])
        iam_client = member_session.client('iam', region_name=account['regionName'])
        
        # Create each default IAM policy
        for policy_key, policy_config in input_config['defaultIAMPolicy'].items():
            logger.info(f"Creating IAM policy: {policy_key}")

            create_iam_policy_if_not_exists(iam_client, policy_config, input_config['defaultTags'], account)
    
    # Create permission sets in org account
    for ps_key, ps_config in input_config['permissionSetConfig'].items():
        logger.info(f"Creating permission set: {ps_key}")

        create_permission_set_if_not_exists(sso_admin_client, instance_arn, ps_config, input_config['defaultTags'])
    
    logger.info("IAM Identity Center resources creation completed")

if __name__ == "__main__":
    create_iam_identity_center_resources()
