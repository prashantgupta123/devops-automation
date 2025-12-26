import boto3


def get_aws_session(request_data):
    if request_data["profile_name"]:
        print("AWS ProfileSession")
        session = boto3.session.Session(profile_name=request_data["profile_name"],
                                        region_name=request_data["region_name"])
    elif request_data["role_arn"]:
        print("AWS AssumedRoleSession")
        session_name = 'AssumedRoleSession'
        duration_seconds = 3600
        sts_client = boto3.client('sts', region_name=request_data["region_name"])
        assumed_role = sts_client.assume_role(
            RoleArn=request_data["role_arn"],
            RoleSessionName=session_name,
            DurationSeconds=duration_seconds
        )
        aws_temp_access_key_id = assumed_role['Credentials']['AccessKeyId']
        aws_temp_secret_access_key = assumed_role['Credentials']['SecretAccessKey']
        aws_temp_session_token = assumed_role['Credentials']['SessionToken']
        session = boto3.session.Session(aws_access_key_id=aws_temp_access_key_id,
                                        aws_secret_access_key=aws_temp_secret_access_key,
                                        aws_session_token=aws_temp_session_token,
                                        region_name=request_data["region_name"])
    elif request_data["session_token"] is not None and request_data["session_token"]:
        print("AWS AccessKeyTokenSession")
        session = boto3.session.Session(aws_access_key_id=request_data["access_key"],
                                        aws_secret_access_key=request_data["secret_key"],
                                        aws_session_token=request_data["session_token"],
                                        region_name=request_data["region_name"])
    elif request_data["access_key"] is not None and request_data["access_key"]:
        print("AWS AccessKeySession")
        session = boto3.session.Session(aws_access_key_id=request_data["access_key"],
                                        aws_secret_access_key=request_data["secret_key"],
                                        region_name=request_data["region_name"])
    else:
        print("AWS DefaultSession")
        session = boto3.session.Session(region_name=request_data["region_name"])
    return session
