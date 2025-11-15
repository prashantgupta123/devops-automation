import json
from AWSSession import get_aws_session
from Notification import send_email


def get_ondemand_ec2_instances(session):
    """Fetch all EC2 instances running on OnDemand lifecycle"""
    ec2_client = session.client('ec2')
    
    try:
        response = ec2_client.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                # Filter for On-Demand instances (no InstanceLifecycle field means On-Demand)
                # Ignore instances that are part of Auto Scaling Groups
                if 'InstanceLifecycle' not in instance:
                    is_asg_instance = False
                    for tag in instance.get('Tags', []):
                        if tag['Key'] == 'aws:autoscaling:groupName':
                            is_asg_instance = True
                            break
                    
                    if not is_asg_instance:
                        instance_name = 'N/A'
                        for tag in instance.get('Tags', []):
                            if tag['Key'] == 'Name':
                                instance_name = tag['Value']
                                break
                        
                        instances.append({
                            'InstanceId': instance['InstanceId'],
                            'Name': instance_name
                        })
        
        return instances
    except Exception as e:
        print(f"Error fetching EC2 instances: {str(e)}")
        return []


def get_backup_protected_resources(session):
    """Get all EC2 resources protected by AWS Backup plans"""
    backup_client = session.client('backup')
    
    try:
        protected_resources = set()
        
        # Get all backup plans
        plans_response = backup_client.list_backup_plans()
        
        for plan in plans_response['BackupPlansList']:
            plan_id = plan['BackupPlanId']
            
            # Get selections for each plan
            selections_response = backup_client.list_backup_selections(BackupPlanId=plan_id)
            
            for selection in selections_response['BackupSelectionsList']:
                selection_id = selection['SelectionId']
                
                # Get detailed selection info
                selection_detail = backup_client.get_backup_selection(
                    BackupPlanId=plan_id,
                    SelectionId=selection_id
                )
                
                backup_selection = selection_detail['BackupSelection']
                
                # Check resources in selection
                for resource in backup_selection.get('Resources', []):
                    if resource.startswith('arn:aws:ec2:') and ':instance/' in resource:
                        # Extract instance ID from ARN
                        instance_id = resource.split('/')[-1]
                        protected_resources.add(instance_id)
        
        return protected_resources
    except Exception as e:
        print(f"Error fetching backup protected resources: {str(e)}")
        return set()


def check_unprotected_instances(instances, protected_resources):
    """Check which instances are not protected by AWS Backup"""
    unprotected = []
    
    for instance in instances:
        if instance['InstanceId'] not in protected_resources:
            unprotected.append(instance)
    
    return unprotected


def send_email_alert(session, smtp_secret_name, notification_config, unprotected_instances):
    """Send email alert for unprotected instances using Notification.py"""
    if not unprotected_instances:
        print("No unprotected instances found. No email sent.")
        return
    
    try:
        subject = "EC2 Instances Not Protected by AWS Backup"
        
        body = f"""
        <html>
        <body>
        <h2>EC2 Instances Not Protected by AWS Backup</h2>
        <p>The following EC2 On-Demand instances are currently running but are not protected by any AWS Backup plan:</p>
        
        <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr>
        <th style="padding: 8px; background-color: #f2f2f2;">Instance ID</th>
        <th style="padding: 8px; background-color: #f2f2f2;">Instance Name</th>
        </tr>
        """
        
        for instance in unprotected_instances:
            body += f"""
            <tr>
            <td style="padding: 8px;">{instance['InstanceId']}</td>
            <td style="padding: 8px;">{instance['Name']}</td>
            </tr>
            """
        
        body += """
        </table>
        
        <p><strong>Action Required:</strong> Please ensure these instances are added to an appropriate AWS Backup plan to protect against data loss.</p>
        
        <p>This is an automated alert from the EC2 Backup Compliance Monitor.</p>
        </body>
        </html>
        """
        
        send_email(session, smtp_secret_name, notification_config['email'], subject, body, notification_config['email']['to'])
        print("Email alert sent successfully using Notification.py")
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")


def lambda_handler(event, context):
    """Main Lambda handler function"""
    try:
        # Load configuration
        with open('input.json', 'r') as f:
            config = json.load(f)
        
        aws_creds = config['awsCredentials']
        notification_config = config['notification']
        smtp_secret_name = config.get('smtp_secret_name')
        
        # Create AWS session
        session = get_aws_session(
            region_name=aws_creds['region_name'],
            role_arn=aws_creds.get('role_arn', ''),
            profile_name=aws_creds.get('profile_name', ''),
            access_key=aws_creds.get('access_key', ''),
            secret_key=aws_creds.get('secret_access_key', ''),
            session_token=aws_creds.get('session_token', '')
        )
        
        print("Starting EC2 backup compliance check...")
        
        # Step 1: Get all On-Demand EC2 instances
        print("Fetching On-Demand EC2 instances...")
        instances = get_ondemand_ec2_instances(session)
        print(f"Found {len(instances)} On-Demand EC2 instances")
        if not instances:
            print("No On-Demand EC2 instances found. Exiting.")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No On-Demand EC2 instances found. Exiting.'
                })
            }
        print("On-Demand EC2 instances found. Continuing...")
        # Debug: Print instance details
        for inst in instances:
            print(f"InstanceId: {inst['InstanceId']}, Name: {inst['Name']}")
        
        # Step 2: Get AWS Backup protected resources
        print("Fetching AWS Backup protected resources...")
        protected_resources = get_backup_protected_resources(session)
        print(f"Found {len(protected_resources)} protected EC2 resources")
        if not protected_resources:
            print("No AWS Backup protected resources found. All instances are unprotected.")
        else:
            print("AWS Backup protected resources found. Continuing...")
            # Debug: Print protected resource IDs
            for res in protected_resources:
                print(f"Protected Resource InstanceId: {res}")
        
        # Step 3: Check for unprotected instances
        print("Checking for unprotected instances...")
        unprotected_instances = check_unprotected_instances(instances, protected_resources)
        print(f"Found {len(unprotected_instances)} unprotected instances")
        
        # Step 4: Send email alert if unprotected instances found
        if unprotected_instances:
            print("Sending email alert for unprotected instances...")
            send_email_alert(session, smtp_secret_name, notification_config, unprotected_instances)
        else:
            print("All instances are protected by AWS Backup. No alert needed.")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'EC2 backup compliance check completed successfully',
                'total_instances': len(instances),
                'protected_instances': len(instances) - len(unprotected_instances),
                'unprotected_instances': len(unprotected_instances),
                'unprotected_list': unprotected_instances
            })
        }
        
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


# For local testing
# if __name__ == "__main__":
#     lambda_handler({}, {})
