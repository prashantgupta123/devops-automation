import json
from datetime import datetime, timedelta
import logging
import sys
from AWSSession import get_aws_session
from Notification import send_email

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    try:
        # Load configuration
        with open('input.json', 'r') as f:
            config = json.load(f)
        
        # Get AWS session
        aws_creds = config['awsCredentials']
        session = get_aws_session(
            region_name=aws_creds['region_name'],
            role_arn=aws_creds.get('role_arn', ''),
            profile_name=aws_creds.get('profile_name', ''),
            access_key=aws_creds.get('access_key', ''),
            secret_key=aws_creds.get('secret_access_key', ''),
            session_token=aws_creds.get('session_token', '')
        )
        
        # Initialize clients
        elbv2_client = session.client('elbv2')
        cloudwatch_client = session.client('cloudwatch')
        
        error_threshold = config.get('error_threshold', 10)
        logger.info(f"Using error threshold: {error_threshold}%")
        
        # Get all target groups
        logger.info("Fetching all target groups")
        all_target_groups = get_all_target_groups(elbv2_client)
        
        # Generate report
        report_data = []
        for tg in all_target_groups:
            tg_metrics = get_target_group_metrics(cloudwatch_client, elbv2_client, tg['TargetGroupArn'])
            tg_error_percentage = calculate_error_percentage(tg_metrics)
            
            if tg_error_percentage > error_threshold:
                report_data.append({
                    'target_group': tg['TargetGroupName'],
                    'error_percentage': tg_error_percentage,
                    'metrics': tg_metrics
                })
        
        # Sort report data by error percentage in descending order
        report_data.sort(key=lambda x: x['error_percentage'], reverse=True)
        
        # Send email report
        logger.info("Sending email report")
        if report_data:
            logger.info(f"Target groups exceeding error threshold: {len(report_data)}")
            send_email_report(config, report_data, error_threshold)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Report generated successfully',
                'high_error_target_groups': len(report_data),
                'total_target_groups': len(all_target_groups)
            })
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}

def get_all_target_groups(elbv2_client):
    """Get all target groups"""
    try:
        response = elbv2_client.describe_target_groups()
        return response['TargetGroups']
    except Exception as e:
        logger.error(f"Error getting all target groups: {str(e)}")
        return []

def get_target_group_metrics(cloudwatch_client, elbv2_client, target_group_arn):
    """Fetch CloudWatch metrics for target group over 7 days"""
    end_time = datetime.now()
    start_time = end_time - timedelta(days=7)
    
    # Extract CloudWatch dimension values from ARN
    # ARN format: arn:aws:elasticloadbalancing:region:account:targetgroup/name/id
    # TargetGroup dimension: targetgroup/name/id
    # LoadBalancer dimension: app/lb-name/lb-id (from target group's load balancer)
    
    arn_parts = target_group_arn.split(':')
    tg_resource = arn_parts[-1]  # targetgroup/name/id
    
    # Get load balancer info from target group
    tg_response = elbv2_client.describe_target_groups(TargetGroupArns=[target_group_arn])
    lb_arns = tg_response['TargetGroups'][0]['LoadBalancerArns']
    
    if not lb_arns:
        logger.info(f"No load balancer found for target group: {target_group_arn}")
        return {}
    
    # Get load balancer dimension value
    lb_arn = lb_arns[0]  # Use first LB if multiple
    lb_resource = lb_arn.split(':')[-1]  # app/lb-name/lb-id
    
    # Remove 'loadbalancer/' prefix if present
    if lb_resource.startswith('loadbalancer/'):
        lb_resource = lb_resource.replace('loadbalancer/', '', 1)
    
    logger.info(f"TargetGroup dimension: {tg_resource}")
    logger.info(f"LoadBalancer dimension: {lb_resource}")

    logger.info(f"Start time: {start_time}, End time: {end_time}")
    
    metrics = {}
    metric_names = ['HTTPCode_Target_2XX_Count', 'HTTPCode_Target_3XX_Count', 'HTTPCode_Target_4XX_Count']
    
    for metric_name in metric_names:
        try:
            response = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName=metric_name,
                Dimensions=[
                    {'Name': 'TargetGroup', 'Value': tg_resource},
                    {'Name': 'LoadBalancer', 'Value': lb_resource}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=86400,  # Daily aggregation
                Statistics=['Sum']
            )
            
            total_count = sum([point['Sum'] for point in response['Datapoints']])
            metrics[metric_name] = total_count
            logger.info(f"Metric {metric_name}: {total_count}")
            logger.info(f"Metric {metric_name}: {total_count}")
            
        except Exception as e:
            logger.error(f"Error fetching metric {metric_name}: {str(e)}")
            metrics[metric_name] = 0
    
    return metrics

def calculate_error_percentage(metrics_data):
    """Calculate error percentage (3XX + 4XX) / 2XX * 100"""
    target_2xx = metrics_data.get('HTTPCode_Target_2XX_Count', 0)
    target_3xx = metrics_data.get('HTTPCode_Target_3XX_Count', 0)
    target_4xx = metrics_data.get('HTTPCode_Target_4XX_Count', 0)
    
    total_errors = target_3xx + target_4xx
    
    if target_2xx == 0:
        return 100.0 if total_errors > 0 else 0.0
    
    error_percentage = (total_errors / target_2xx) * 100
    return round(error_percentage, 2)

def send_email_report(config, report_data, error_threshold):
    """Send email report with target group metrics"""
    smtp_creds = config['smtpCredentials']
    smtp_details = config['notification']['email']
    user_email = smtp_details['to']
    
    # Generate HTML email content
    html_content = f"""
    <html>
    <body>
        <h2>Target Group Error Rate Report</h2>
        <p><strong>Report Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Analysis Period:</strong> Last 7 days</p>
        
        <h3>Target Groups with Error Rate > {error_threshold}%</h3>
    """
    
    if report_data:
        html_content += """
        <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>Target Group Name</th>
                <th>Error Percentage</th>
                <th>2XX Count</th>
                <th>3XX Count</th>
                <th>4XX Count</th>
            </tr>
        """
        
        for item in report_data:
            metrics = item['metrics']
            html_content += f"""
            <tr>
                <td>{item['target_group']}</td>
                <td>{item['error_percentage']}%</td>
                <td>{metrics.get('HTTPCode_Target_2XX_Count', 0)}</td>
                <td>{metrics.get('HTTPCode_Target_3XX_Count', 0)}</td>
                <td>{metrics.get('HTTPCode_Target_4XX_Count', 0)}</td>
            </tr>
            """
        
        html_content += "</table>"
    else:
        html_content += f"<p>No target groups found with error rate > {error_threshold}%</p>"
    
    html_content += f"""
        <br>
        <p><em>This report shows target groups where the combined 3XX and 4XX error rate exceeds {error_threshold}% compared to 2XX success responses over the last 7 days.</em></p>
    </body>
    </html>
    """
    
    try:
        send_email(
            smtp_credentials=smtp_creds,
            smtp_details=smtp_details,
            email_subject="Target Group Error Rate Report",
            email_content=html_content,
            user_email=user_email
        )
        logger.info("Email report sent successfully")
        logger.info("Email report sent successfully")
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise
