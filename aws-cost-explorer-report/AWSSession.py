import boto3


def get_aws_session(region_name, role_arn="", profile_name="", access_key="", secret_key="", session_token=""):
    if profile_name:
        session = boto3.session.Session(profile_name=profile_name, region_name=region_name)
    elif role_arn:
        session_name = 'AssumedRoleSession'
        duration_seconds = 3600
        sts_client = boto3.client('sts', region_name=region_name)
        assumed_role = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name,
            DurationSeconds=duration_seconds
        )
        aws_temp_access_key_id = assumed_role['Credentials']['AccessKeyId']
        aws_temp_secret_access_key = assumed_role['Credentials']['SecretAccessKey']
        aws_temp_session_token = assumed_role['Credentials']['SessionToken']
        session = boto3.session.Session(aws_access_key_id=aws_temp_access_key_id,
                                        aws_secret_access_key=aws_temp_secret_access_key,
                                        aws_session_token=aws_temp_session_token, region_name=region_name)
    elif session_token:
        session = boto3.session.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key,
                                        aws_session_token=session_token, region_name=region_name)
    elif access_key:
        session = boto3.session.Session(aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region_name)
    else:
        session = boto3.session.Session(region_name=region_name)
    return session
