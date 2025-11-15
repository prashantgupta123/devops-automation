import json
from datetime import datetime, timedelta
import logging
from AWSSession import get_aws_session
from Notification import send_email

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add console handler for local testing
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

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
        
        response_time_threshold = config.get('response_time_threshold', 500)
        logger.info(f"Using response time threshold: {response_time_threshold}ms")

        max_response_time_threshold = config.get('max_response_time_threshold', 2000)
        logger.info(f"Using max response time threshold: {max_response_time_threshold}ms")

        max_results = config.get('max_results', 50)
        logger.info(f"Using max results: {max_results}")

        period = config.get('period', 60)
        logger.info(f"Using period: {period}")
        last_days = config.get('last_days', 7)
        logger.info(f"Using last days: {last_days}")
        
        # Get all target groups
        logger.info("Fetching all target groups")
        all_target_groups = get_all_target_groups(elbv2_client, max_results)
        
        # Generate report
        report_data = []
        for tg in all_target_groups:
            tg_metrics = get_target_group_response_time_metrics(cloudwatch_client, elbv2_client, tg['TargetGroupArn'], period, last_days)
            
            if tg_metrics and (tg_metrics.get('avg_response_time', 0) > response_time_threshold or tg_metrics.get('max_response_time', 0) > max_response_time_threshold):
                report_data.append({
                    'target_group': tg['TargetGroupName'],
                    'max_response_time': tg_metrics.get('max_response_time', 0),
                    'avg_response_time': tg_metrics.get('avg_response_time', 0)
                })
        
        # Sort report data by avg response time first, then max response time in descending order
        report_data.sort(key=lambda x: (x['avg_response_time'], x['max_response_time']), reverse=True)
        
        # Send email report
        logger.info("Sending email report")
        if report_data:
            logger.info(f"Target groups exceeding response time threshold: {len(report_data)}")
            send_email_report(config, report_data, response_time_threshold, max_response_time_threshold, last_days)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Response time report generated successfully',
                'high_response_time_target_groups': len(report_data),
                'total_target_groups': len(all_target_groups)
            })
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}

def get_all_target_groups(elbv2_client, max_results):
    """Get all target groups with pagination"""
    try:
        all_target_groups = []
        marker = None
        
        while True:
            params = {'PageSize': max_results}
            if marker:
                params['Marker'] = marker
            
            response = elbv2_client.describe_target_groups(**params)
            all_target_groups.extend(response['TargetGroups'])
            
            marker = response.get('NextMarker')
            if not marker:
                break
        
        return all_target_groups
    except Exception as e:
        logger.error(f"Error getting all target groups: {str(e)}")
        return []

def get_target_group_response_time_metrics(cloudwatch_client, elbv2_client, target_group_arn, period, last_days):
    """Fetch CloudWatch response time metrics day by day and combine results"""
    # Extract CloudWatch dimension values from ARN
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
    
    all_max_values = []
    all_avg_values = []
    
    # Fetch metrics day by day to stay within 1440 datapoint limit
    for day in range(last_days):
        end_time = datetime.now() - timedelta(days=day)
        start_time = end_time - timedelta(days=1)
        
        try:
            response = cloudwatch_client.get_metric_statistics(
                Namespace='AWS/ApplicationELB',
                MetricName='TargetResponseTime',
                Dimensions=[
                    {'Name': 'TargetGroup', 'Value': tg_resource},
                    {'Name': 'LoadBalancer', 'Value': lb_resource}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=period,
                Statistics=['Maximum', 'Average']
            )
            
            if response['Datapoints']:
                day_max_values = [point['Maximum'] for point in response['Datapoints']]
                day_avg_values = [point['Average'] for point in response['Datapoints']]
                all_max_values.extend(day_max_values)
                all_avg_values.extend(day_avg_values)
                
        except Exception as e:
            logger.error(f"Error fetching metrics for day {day}: {str(e)}")
            continue
    
    # Calculate combined metrics
    metrics = {}
    if all_max_values and all_avg_values:
        # Convert from seconds to milliseconds
        metrics['max_response_time'] = round(max(all_max_values) * 1000, 2)
        metrics['avg_response_time'] = round(sum(all_avg_values) / len(all_avg_values) * 1000, 2)
        
        logger.info(f"Max Response Time: {metrics['max_response_time']}ms")
        logger.info(f"Avg Response Time: {metrics['avg_response_time']}ms")
    else:
        metrics['max_response_time'] = 0
        metrics['avg_response_time'] = 0
    
    return metrics

def send_email_report(config, report_data, response_time_threshold, max_response_time_threshold, last_days):
    """Send email report with target group response time metrics"""
    smtp_creds = config['smtpCredentials']
    smtp_details = config['notification']['email']
    user_email = smtp_details['to']
    
    # Generate HTML email content
    html_content = f"""
    <html>
    <body>
        <h2>Target Group Response Time Report</h2>
        <p><strong>Report Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Analysis Period:</strong> Last {last_days} days</p>
        
        <h3>Target Groups with Average Response Time > {response_time_threshold}ms</h3>
        <h3>Target Groups with Maximum Response Time > {max_response_time_threshold}ms</h3>
    """
    
    if report_data:
        html_content += """
        <table border="1" cellpadding="5" cellspacing="0">
            <tr>
                <th>Target Group Name</th>
                <th>Average Response Time (ms)</th>
                <th>Maximum Response Time (ms)</th>
            </tr>
        """
        
        for item in report_data:
            avg_time = item['avg_response_time']
            max_time = item['max_response_time']
            if avg_time > response_time_threshold:  # High avg response time - Critical
                row_style = 'background-color: #cc0000; color: white;'  # Dark red
            elif max_time >= 10000:  # 10+ seconds - Critical
                row_style = 'background-color: #ff0000; color: white;'  # Red
            elif max_time >= 5000:  # 5+ seconds - Unacceptable
                row_style = 'background-color: #ff9999;'  # Light red
            elif max_time >= 2000:  # 2+ seconds - Poor
                row_style = 'background-color: #ff8800;'  # Orange
            elif max_time >= 1000:  # 1+ seconds - Noticeable
                row_style = 'background-color: #ffab00;'  # Yellow 
            else:
                row_style = ''
            
            html_content += f"""
            <tr style="{row_style}">
                <td>{item['target_group']}</td>
                <td>{item['avg_response_time']}</td>
                <td>{item['max_response_time']}</td>
            </tr>
            """
        
        html_content += "</table>"
    else:
        html_content += f"<p>No target groups found with response time > {response_time_threshold}ms</p>"
    
    html_content += f"""
        <br>
        <p><em>This report shows target groups where the maximum or average response time exceeds {response_time_threshold}ms over the last {last_days} days.</em></p>
    </body>
    </html>
    """
    
    try:
        send_email(
            smtp_credentials=smtp_creds,
            smtp_details=smtp_details,
            email_subject="Target Group Response Time Report",
            email_content=html_content,
            user_email=user_email
        )
        logger.info("Email report sent successfully")
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise


# For Local Testing
lambda_handler(None, None)