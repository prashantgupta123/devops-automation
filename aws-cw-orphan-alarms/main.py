import AWSSession
import Notification
import yaml
import json
import logging
import sys
import xlsxwriter

# Creating an object
logger = logging.getLogger()
# Setting the threshold of logger to DEBUG
logger.setLevel(logging.INFO)
# setting stdout for logging
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def get_ec2_details(ec2_client, max_results):
    ec2_details = []
    next_token = None
    while True:
        if next_token is not None and next_token != "" and next_token:
            response = ec2_client.describe_instances(MaxResults=max_results, NextToken=next_token)
        else:
            response = ec2_client.describe_instances(MaxResults=max_results)
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                ec2_details.append({"InstanceId": instance['InstanceId']})
        if 'NextToken' in response and response["NextToken"] is not None and response['NextToken'] != "":
            next_token = response['NextToken']
        else:
            break
    return ec2_details


def get_target_group_details(elbv2_client, max_results):
    targetgroup_details = []
    target_groups = []
    next_token = None
    while True:
        if next_token is not None and next_token != "" and next_token:
            response = elbv2_client.describe_target_groups(
                Marker = next_token,
                PageSize = max_results,
            )
        else:
            response = elbv2_client.describe_target_groups(
                PageSize = max_results,
            )
        for target_group in response['TargetGroups']:
            for load_balancer in target_group["LoadBalancerArns"]:
                target_group_data = {
                    "LoadBalancer": load_balancer.split("loadbalancer/")[1],
                    "TargetGroup": "targetgroup/" + target_group['TargetGroupArn'].split("targetgroup/")[1]
                }
                targetgroup_details.append(target_group_data)
            target_groups.append({"TargetGroup": "targetgroup/" + target_group['TargetGroupArn'].split("targetgroup/")[1]})
        if 'NextMarker' in response and response["NextMarker"] is not None and response['NextMarker'] != "":
            next_token = response['NextMarker']
        else:
            break
    return target_groups, targetgroup_details


def get_load_balancer_details(elbv2_client, max_results):
    load_balancer_details = []
    next_token = None
    while True:
        if next_token is not None and next_token != "" and next_token:
            response = elbv2_client.describe_load_balancers(
                Marker = next_token,
                PageSize = max_results
            )
        else:
            response = elbv2_client.describe_load_balancers(
                PageSize = max_results
            )
        for load_balancer in response['LoadBalancers']:
            load_balancer_data = {
                "LoadBalancer": load_balancer['LoadBalancerArn'].split("loadbalancer/")[1]
            }
            load_balancer_details.append(load_balancer_data)
        if 'NextMarker' in response and response["NextMarker"] is not None and response['NextMarker'] != "":
            next_token = response['NextMarker']
        else:
            break
    return load_balancer_details


def get_rds_cluster_details(rds_client, max_results):
    rds_details = []
    next_token = None
    filters = [{
        'Name': 'engine',
        'Values': [
            "mysql",
            "aurora-mysql",
            "postgres",
            "aurora-postgresql"
        ]
    }]
    while True:
        if next_token is not None and next_token != "" and next_token:
            response = rds_client.describe_db_clusters(
                MaxRecords=max_results,
                Marker=next_token,
                Filters=filters
            )
        else:
            response = rds_client.describe_db_clusters(
                MaxRecords=max_results,
                Filters=filters
            )
        for cluster in response['DBClusters']:
            rds_details.append({
                'DBClusterIdentifier': cluster['DBClusterIdentifier']
            })
        if 'Marker' in response and response["Marker"] is not None and response['Marker'] != "":
            next_token = response['Marker']
        else:
            break
    return rds_details


def get_rds_instance_details(rds_client, max_results):
    rds_details = []
    next_token = None
    filters = [{
        'Name': 'engine',
        'Values': [
            "mysql",
            "aurora-mysql",
            "postgres",
            "aurora-postgresql"
        ]
    }]
    while True:
        if next_token is not None and next_token != "" and next_token:
            response = rds_client.describe_db_instances(
                MaxRecords=max_results,
                Marker=next_token,
                Filters=filters
            )
        else:
            response = rds_client.describe_db_instances(
                MaxRecords=max_results,
                Filters=filters
            )
        for instance in response['DBInstances']:
            rds_details.append({
                'DBInstanceIdentifier': instance['DBInstanceIdentifier']
            })
        if 'Marker' in response and response["Marker"] is not None and response['Marker'] != "":
            next_token = response['Marker']
        else:
            break
    return rds_details


def get_ecs_cluster_details(ecs_client, max_results):
    ecs_details = []
    next_token = None
    while True:
        if next_token is not None and next_token != "" and next_token:
            response = ecs_client.list_clusters(maxResults=max_results, nextToken=next_token)
        else:
            response = ecs_client.list_clusters(maxResults=max_results)
        for cluster_arn in response['clusterArns']:
            ecs_details.append({"ClusterName": cluster_arn.split("cluster/")[1]})
        if 'nextToken' in response and response["nextToken"] is not None and response['nextToken'] != "":
            next_token = response['nextToken']
        else:
            break
    return ecs_details


def get_ecs_service_details(ecs_client, max_results):
    ecs_details = []
    next_token = None
    while True:
        if next_token is not None and next_token != "" and next_token:
            response = ecs_client.list_clusters(maxResults=max_results, nextToken=next_token)
        else:
            response = ecs_client.list_clusters(maxResults=max_results)
        for cluster_arn in response['clusterArns']:
            service_next_token = None
            while True:
                if service_next_token is not None and service_next_token != "" and service_next_token:
                    service_response = ecs_client.list_services(cluster=cluster_arn, maxResults=max_results, nextToken=service_next_token)
                else:
                    service_response = ecs_client.list_services(cluster=cluster_arn, maxResults=max_results)
                for service_arn in service_response['serviceArns']:
                    ecs_details.append({
                        "ClusterName": cluster_arn.split("cluster/")[1],
                        "ServiceName": service_arn.split("/")[-1]
                    })
                if 'nextToken' in service_response and service_response["nextToken"] is not None and service_response['nextToken'] != "":
                    service_next_token = service_response['nextToken']
                else:
                    break
        if 'nextToken' in response and response["nextToken"] is not None and response['nextToken'] != "":
            next_token = response['nextToken']
        else:
            break
    return ecs_details


def get_lambda_details(lambda_client, max_results):
    ecs_details = []
    next_token = None
    while True:
        if next_token is not None and next_token != "" and next_token:
            response = lambda_client.list_functions(MaxItems=max_results, Marker=next_token)
        else:
            response = lambda_client.list_functions(MaxItems=max_results)
        for function in response['Functions']:
            ecs_details.append({"FunctionName": function["FunctionName"]})
        if 'NextMarker' in response and response["NextMarker"] is not None and response['NextMarker'] != "":
            next_token = response['NextMarker']
        else:
            break
    return ecs_details


def get_lambda_resource_details(lambda_client, max_results):
    ecs_details = []
    next_token = None
    while True:
        if next_token is not None and next_token != "" and next_token:
            response = lambda_client.list_functions(MaxItems=max_results, Marker=next_token)
        else:
            response = lambda_client.list_functions(MaxItems=max_results)
        for function in response['Functions']:
            version_next_token = None
            while True:
                if version_next_token is not None and version_next_token != "" and version_next_token:
                    version_response = lambda_client.list_versions_by_function(FunctionName=function["FunctionName"], MaxItems=max_results, Marker=version_next_token)
                else:
                    version_response = lambda_client.list_versions_by_function(FunctionName=function["FunctionName"], MaxItems=max_results)
                for version_function in version_response['Versions']:
                    if version_function["Version"] == "$LATEST":
                        ecs_details.append({
                            "FunctionName": version_function["FunctionName"],
                            "Resource": version_function["FunctionName"]
                        })
                    else:
                        ecs_details.append({
                            "FunctionName": version_function["FunctionName"],
                            "Resource": version_function["FunctionName"] + ":" + version_function["Version"]
                        })
                if 'NextMarker' in version_response and version_response["NextMarker"] is not None and version_response['NextMarker'] != "":
                    version_next_token = version_response['NextMarker']
                else:
                    break
        if 'NextMarker' in response and response["NextMarker"] is not None and response['NextMarker'] != "":
            next_token = response['NextMarker']
        else:
            break
    return ecs_details


def get_sqs_details(sqs_client, max_results):
    sqs_details = []
    next_token = None
    while True:
        if next_token is not None and next_token != "" and next_token:
            response = sqs_client.list_queues(MaxResults=max_results, NextToken=next_token)
        else:
            response = sqs_client.list_queues(MaxResults=max_results)
        for queue_url in response['QueueUrls']:
            sqs_details.append({"QueueName": queue_url.split("/")[-1]})
        if 'NextToken' in response and response["NextToken"] is not None and response['NextToken'] != "":
            next_token = response['NextToken']
        else:
            break
    return sqs_details


def list_alarms_for_aws_resources(cloudwatch_client, max_results):
    cloudwatch_alarms = []
    next_token = None
    while True:
        if next_token is not None and next_token != "" and next_token:
            response = cloudwatch_client.describe_alarms(MaxRecords=max_results, NextToken=next_token)
        else:
            response = cloudwatch_client.describe_alarms(MaxRecords=max_results)

        for alarm in response['MetricAlarms']:
            try:
                if "Namespace" in alarm:
                    cloudwatch_alarms.append({
                        "AlarmName": alarm["AlarmName"],
                        "Namespace": alarm["Namespace"],
                        "Dimensions": alarm["Dimensions"]
                    })
                else:
                    if "Metrics" in alarm:
                        for metric in alarm["Metrics"]:
                            if "MetricStat" in metric:
                                cloudwatch_alarms.append({
                                    "AlarmName": alarm["AlarmName"],
                                    "Namespace": metric["MetricStat"]["Metric"]["Namespace"],
                                    "Dimensions": metric["MetricStat"]["Metric"]["Dimensions"]
                                })
                    else:
                        logger.error("No Alarm Metrics found: " + alarm["AlarmName"])
            except Exception as e:
                logger.error("Exception in alarm: " + alarm["AlarmName"])
                logger.error(e)

        if 'NextToken' in response and response["NextToken"] is not None and response['NextToken'] != "":
            next_token = response['NextToken']
        else:
            break
    return cloudwatch_alarms


def check_alarm_aws_resources_with_resource_list(resource_details, namespace, alarms, service_data):
    unused_alarms = []
    dimensions = resource_details['Dimension']
    exclude_dimension = resource_details['ExcludeDimension']
    for alarm in alarms:
        if alarm['Namespace'] == namespace:
            alarm_dimensions = {dimension['Name']: dimension['Value'] for dimension in alarm['Dimensions']}
            all_dimension_present = []
            for resource_dimension in dimensions:
                if resource_dimension in alarm_dimensions:
                    all_dimension_present.append(True)
                else:
                    all_dimension_present.append(False)
            for resource_dimension in exclude_dimension:
                if resource_dimension in alarm_dimensions:
                    all_dimension_present.append(False)
            dimension_present = all(all_dimension_present)

            if dimension_present:
                resource_present = False
                for resource in service_data:
                    all_resource_present = []
                    for resource_dimension in dimensions:
                        if alarm_dimensions[resource_dimension] == resource[resource_dimension]:
                            all_resource_present.append(True)
                        else:
                            all_resource_present.append(False)
                    resource_present = all(all_resource_present)
                    if resource_present:
                        break
                if not resource_present:
                    unused_alarms.append(alarm)
    return unused_alarms


def delete_alarms(cloudwatch_client, service, alarm_names):
    try:
        cloudwatch_client.delete_alarms(AlarmNames=alarm_names)
        logger.error("Successfully deleted alarms for: " + service)
    except Exception as e:
        logger.error("Error deleting alarms:", e)


def create_excel_report(request_data, input_data, output_data, cloudwatch_client):
    workbook = xlsxwriter.Workbook('Inventory.xlsx')
    cell_format = workbook.add_format()
    cell_format.set_text_wrap()
    for service in output_data:
        if output_data[service]:
            alarm_names = []
            alarm_dimensions_headers = input_data[service]["Dimension"]
            bold = workbook.add_format({'bold': True})
            worksheet = workbook.add_worksheet(service)
            worksheet.set_row(0, 25)
            row = 0
            col = 0
            worksheet.write(row, col, "AlarmName", bold)
            worksheet.set_column(col, col, 70, cell_format)
            col += 1
            worksheet.write(row, col, "Namespace", bold)
            worksheet.set_column(col, col, 20, cell_format)
            col += 1
            for dimension in alarm_dimensions_headers:
                worksheet.write(row, col, dimension, bold)
                worksheet.set_column(col, col, 50, cell_format)
                col += 1

            for alarm in output_data[service]:
                col = 0
                row += 1
                worksheet.write(row, col, alarm["AlarmName"])
                col += 1
                worksheet.write(row, col, alarm["Namespace"])
                col += 1
                alarm_dimensions = {dimension['Name']: dimension['Value'] for dimension in alarm['Dimensions']}
                for dimension in alarm_dimensions_headers:
                    worksheet.write(row, col, alarm_dimensions[dimension])
                    col += 1
                alarm_names.append(alarm["AlarmName"])
            if request_data["delete"]:
                delete_alarms(cloudwatch_client, service, alarm_names)
    workbook.close()


def get_aws_services_data(session, max_results, request_data):
    ec2_client = session.client('ec2', region_name=request_data["region_name"])
    elbv2_client = session.client('elbv2', region_name=request_data['region_name'])
    rds_client = session.client('rds', region_name=request_data["region_name"])
    ecs_client = session.client('ecs', region_name=request_data["region_name"])
    lambda_client = session.client('lambda', region_name=request_data["region_name"])
    sqs_client = session.client('sqs', region_name=request_data["region_name"])
    ec2_instance_ids = get_ec2_details(ec2_client, max_results)
    load_balancers = get_load_balancer_details(elbv2_client, max_results)
    target_groups, load_balancers_target_group = get_target_group_details(elbv2_client, max_results)
    rds_clusters = get_rds_cluster_details(rds_client, max_results)
    rds_instances = get_rds_instance_details(rds_client, max_results)
    ecs_clusters = get_ecs_cluster_details(ecs_client, max_results)
    ecs_services = get_ecs_service_details(ecs_client, max_results)
    lambda_names = get_lambda_details(lambda_client, max_results)
    lambda_resources = get_lambda_resource_details(lambda_client, max_results)
    sqs_names = get_sqs_details(sqs_client, max_results)
    service_data = {
        "EC2Instance": ec2_instance_ids,
        "RDSCluster": rds_clusters,
        "RDSInstance": rds_instances,
        "TargetGroup": target_groups,
        "LoadBalancerTargetGroup": load_balancers_target_group,
        "LoadBalancer": load_balancers,
        "ECSService": ecs_services,
        "ECSCluster": ecs_clusters,
        "Lambda": lambda_names,
        "LambdaResource": lambda_resources,
        "SQS": sqs_names
    }
    return service_data


def main():
    with open("inputs.yml", 'r') as file:
        request_data = yaml.safe_load(file)

    with open("input.json", 'r') as file:
        input_data = json.load(file)

    session = AWSSession.get_aws_session(request_data)
    max_results = 100
    service_data = get_aws_services_data(session, max_results, request_data)
    cloudwatch_client = session.client('cloudwatch', region_name=request_data["region_name"])
    cloudwatch_alarms = list_alarms_for_aws_resources(cloudwatch_client, max_results)

    output_data = {}
    for resource_name, resource_details in input_data.items():
        logger.info(f"\n---- Checking {resource_name} ----")
        if resource_name in service_data:
            unused_alarms = []
            for namespace in resource_details['Namespace']:
                unused_alarms.extend(check_alarm_aws_resources_with_resource_list(resource_details, namespace, cloudwatch_alarms, service_data[resource_name]))
            output_data[resource_name] = unused_alarms

    logger.info("\nOutput:")
    logger.info(json.dumps(output_data, indent=4))

    if output_data:
        with open("output.json", "w") as outfile:
            outfile.write(json.dumps(output_data, indent=4))

        create_excel_report(request_data, input_data, output_data, cloudwatch_client)

        if request_data["Email"]["enabled"]:
            script_subject = "AWS Inventory Report"
            script_message = "Please find the generated inventory file attached"
            Notification.send_email(script_subject, script_message, 'Inventory.xlsx')


if __name__ == "__main__":
    main()
