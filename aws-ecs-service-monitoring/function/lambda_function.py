import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Validate required environment variables
required_env_vars = ['REGION', 'ALERT_TOPIC_ARN', 'PROJECT_NAME', 'ENV']
for var in required_env_vars:
    if not os.environ.get(var):
        raise ValueError(f"Required environment variable {var} is not set")

regionName = os.environ.get('REGION')

def putMetricData(clusterName, serviceName, customMetricName, countValue):
    cloudWatchClient = boto3.client('cloudwatch', region_name=regionName)
    response = cloudWatchClient.put_metric_data(
        Namespace='AWS/ECS',
        MetricData=[
            {
                'MetricName': customMetricName,
                'Dimensions': [
                    {
                        'Name': 'ClusterName',
                        'Value': clusterName
                    },
                    {
                        'Name': 'ServiceName',
                        'Value': serviceName
                    },
                ],
                'Values': [countValue],
                'Unit': 'Count'
            }
        ]
    )


def sendSnsNotification(snsArn, snsSubject, snsMessage):
    snsClient = boto3.client('sns', region_name=regionName)
    logger.info("SNS ARN: " + snsArn)
    logger.info("SNS subject: " + snsSubject)
    logger.info("SNS message: " + snsMessage)
    response = snsClient.publish(
        TopicArn=snsArn,
        Subject=snsSubject,
        Message=snsMessage,
    )


def lambda_handler(event, context):
    sendNotification = False
    customMetricName="ECSServiceErrorEventsCount"
    snsArn = os.environ.get('ALERT_TOPIC_ARN')
    try:
        if event["source"] == "aws.ecs":
            region = event["region"]
            serviceName = event["resources"][0].split("/", 2)[2]
            clusterName = event["resources"][0].split("/", 2)[1]
            reason = ""
            if "reason" in event["detail"]:
                reason = event["detail"]["reason"]
            eventName = event["detail"]["eventName"]
            eventType = event["detail"]["eventType"]
            snsSubject = ""
            messageBody = ""
            if event["detail-type"] == "ECS Service Action":
                if eventName == "SERVICE_TASK_PLACEMENT_FAILURE":
                    snsSubject = "ECS Service Task Placement Failure"
                    messageBody = "Not enough CPU or memory capacity on the available container instances or no container instances being available"
                    sendNotification = True
                elif eventName == "SERVICE_TASK_CONFIGURATION_FAILURE":
                    snsSubject = "ECS Service Task Configuration Failure"
                    messageBody = "Tags were being applied to the service but the user or role had not opted in to the new Amazon Resource Name (ARN) format in the Region"
                    sendNotification = True
                elif eventName == "SERVICE_DAEMON_PLACEMENT_CONSTRAINT_VIOLATED":  
                    snsSubject = "ECS Service Daemon Placement Constraint Violated"
                    messageBody = "A task in a service using the DAEMON service scheduler strategy no longer meets the placement constraint strategy for the service."
                    sendNotification = True
                elif eventName == "ECS_OPERATION_THROTTLED":
                    snsSubject = "ECS Operation Throttled"
                    messageBody = "The service scheduler has been throttled due to the Amazon ECS API throttle limits."
                    sendNotification = True
                elif eventName == "SERVICE_DISCOVERY_OPERATION_THROTTLED":
                    snsSubject = "ECS Service Discovery Operation Throttled"
                    messageBody = "The service scheduler has been throttled due to the AWS Cloud Map API throttle limits. This can occur on services configured to use service discovery."
                    sendNotification = True
                elif eventName == "SERVICE_DEPLOYMENT_FAILED":
                    snsSubject = "ECS Service Deployment Failed"
                    messageBody = "A service deployment did not reach the steady. This happens when a CloudWatch is triggered or the circuit breaker detects a service deployment failure."
                    sendNotification = True
                elif eventName == "SERVICE_TASK_START_IMPAIRED":
                    snsSubject = "ECS Service Task Start Impaired"
                    messageBody = "The service is unable to consistently start tasks successfully."
                    sendNotification = True
                elif eventName == "SERVICE_DISCOVERY_INSTANCE_UNHEALTHY":
                    snsSubject = "ECS Service Discovery Instance Unhealthy"
                    messageBody = "A service using service discovery contains an unhealthy task. The service scheduler detects that a task within a service registry is unhealthy."
                    sendNotification = True
                elif eventName == "VPC_LATTICE_TARGET_UNHEALTHY":
                    snsSubject = "ECS Service VPC Lattice Target Unhealthy"
                    messageBody = "The service using VPC Lattice has detected one of the targets for the VPC Lattice is unhealthy."
                    sendNotification = True
            elif event["detail-type"] == "ECS Deployment State Change":
                if eventName == "SERVICE_DEPLOYMENT_FAILED":
                    snsSubject = "ECS Service Deployment Failed"
                    messageBody = "The service deployment has failed. This event is sent for services with deployment circuit breaker logic turned on."
                    sendNotification = True

            if sendNotification:
                snsSubject = os.environ['PROJECT_NAME'] + " | " + os.environ['ENV'] + " | " + "ERROR: " + snsSubject
                snsMessage = "Hi,\n\nCluster Name: " + clusterName + "\nService Name: " + serviceName + "\nRegion: " + region + "\nEvent Name: " + eventName + "\nReason: " + reason + "\nMessage: " + messageBody
                sendSnsNotification(snsArn, snsSubject, snsMessage)
                putMetricData(clusterName, serviceName, customMetricName, 1)
            elif eventType == "ERROR":
                snsSubject = os.environ['PROJECT_NAME'] + " | " + os.environ['ENV'] + " | " + "ERROR: " + "ECS Error Service Events"
                snsMessage = "Hi,\n\nNo Event found for: " + str(event)
                sendSnsNotification(snsArn, snsSubject, snsMessage)
        else:
            logger.info("Error: Function only supports input from events with a source type of: aws.ecs")
    except Exception as e:
        snsSubject = os.environ['PROJECT_NAME'] + " | " + os.environ['ENV'] + " | " + "ERROR: " + "ECS Service Events"
        snsMessage = "Hi,\n\nEvent: " + str(event) + "Exception occur: " + str(e)
        sendSnsNotification(snsArn, snsSubject, snsMessage)
