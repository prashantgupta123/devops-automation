import yaml
import json
import logging
import sys
import AWSSession
import Notification
import time

# Creating an object
logger = logging.getLogger()
# Setting the threshold of logger to DEBUG
logger.setLevel(logging.INFO)
# setting stdout for logging
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


def sending_emails(aws_session, resource_list):
    ending_body = "</div><br><br><div><b>NOTE: DevOps will modify resources after reviewing manually.</b></div><br><br></body></html>"
    table_starting = """
        <table cellspacing="0" border="0" style="font-family:Arial;font-size:x-small">
            <colgroup width="300"></colgroup>
            <colgroup width="300"></colgroup>
            <colgroup width="400"></colgroup>
            <tbody>
    """
    table_ending = "</tbody></table>"
    heading = """
        <tr>
            <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" height="17" align="center"><b>Name</b></td>
            <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" height="17" align="center"><b>SummaryMessage</b></td>
            <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" height="17" align="center"><b>ErrorMessage</b></td>
        </tr>
    """
    table_row = """
        <td style="border-width:1px;border-style:solid;border-color:rgb(0,0,0);font-family:&quot;Liberation Sans&quot;" align="center">{rowValue}</td>
    """
    starting_body = "<html><body><div>Hi All,</div>"
    body_prefix_content = f"""
        <br><div>{script_message}</div>
        <br><div>
    """
    smtp_body = starting_body + body_prefix_content + table_starting + heading
    for resource in resource_list:
        row_values = "<tr>"
        row_values = row_values + table_row.format(rowValue=str(resource))
        row_values = row_values + table_row.format(rowValue=str(resource_list[resource].get("SummaryMessage", "N/A")))
        row_values = row_values + table_row.format(rowValue=str(resource_list[resource].get("ErrorMessage", "N/A")))
        row_values += "</tr>"
        smtp_body += row_values
    smtp_body += table_ending
    smtp_body += ending_body

    Notification.send_email(aws_session, script_subject, smtp_body)


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


def get_failed_alarms(cloudwatch_client, max_results, cloudwatch_alarms):
    failed_cloudwatch_alarms = {}
    for alarm_name in cloudwatch_alarms:
        alarm_response = cloudwatch_client.describe_alarm_history(
            AlarmName=alarm_name["AlarmName"],
            HistoryItemType='Action',
            MaxRecords=max_results
        )
        if "AlarmHistoryItems" in alarm_response:
            for alarm_history in alarm_response["AlarmHistoryItems"]:
                history_data = json.loads(alarm_history["HistoryData"])
                if history_data["actionState"] == "Failed":
                    error_data = {}
                    logger.info(alarm_name["AlarmName"])
                    logger.info(alarm_history)
                    if "error" in history_data:
                        error_data["ErrorMessage"] = history_data["error"]
                    if "HistorySummary" in alarm_history:
                        error_data["SummaryMessage"] = alarm_history["HistorySummary"]
                        logger.info(error_data)
                    failed_cloudwatch_alarms[alarm_name["AlarmName"]] = error_data
                    break
        time.sleep(1)
    return failed_cloudwatch_alarms


def lambda_handler():
    max_results = 5
    session = AWSSession.get_aws_session(input_data)
    cloudwatch_client = session.client('cloudwatch', region_name=region_name)
    cloudwatch_alarms = list_alarms_for_aws_resources(cloudwatch_client, max_results)
    logger.info(json.dumps(cloudwatch_alarms, indent=4))
    resource_list = get_failed_alarms(cloudwatch_client, max_results, cloudwatch_alarms)
    logger.info(json.dumps(resource_list, indent=4))
    if resource_list:
        if email_enabled:
            sending_emails(session, resource_list)


try:
    with open("inputs.yml", 'r') as file:
        input_data = yaml.safe_load(file)
except FileNotFoundError:
    print("Error: inputs.yml file not found")
    sys.exit(1)
except yaml.YAMLError as e:
    print(f"Error parsing inputs.yml: {e}")
    sys.exit(1)
region_name = input_data["region_name"]
profile_name = input_data["profile_name"]
role_arn = input_data["role_arn"]
access_key = input_data["access_key"]
secret_key = input_data["secret_key"]
session_token = input_data["session_token"]
email_enabled = input_data["Email"]["enabled"]

script_subject = "Failed Cloudwatch Alarms Report"
script_message = "Please find AWS Failed Cloudwatch Alarms Report."

lambda_handler()
