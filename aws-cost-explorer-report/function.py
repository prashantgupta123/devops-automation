import json
from datetime import datetime, timedelta
from AWSSession import get_aws_session

# Sample Data
# [
#     {
#         "cloudName": "AWS",
#         "regionName": "us-east-1",
#         "projectName": "MyProject",
#         "accountId": "999999999999",
#         "accountName": "myproject-nonprod",
#         "roleName": "myproject_ro"
#     }
# ]
def load_account_details():
    """Load account details from JSON file"""
    with open('account_details.json', 'r') as f:
        return json.load(f)


def get_cost_by_region_for_account(account):
    """Get cost breakdown by region for a single account"""
    # Calculate last month's date range
    today = datetime.now()
    first_day_current_month = today.replace(day=1)
    last_day_previous_month = first_day_current_month - timedelta(days=1)
    first_day_previous_month = last_day_previous_month.replace(day=1)
    
    start_date = first_day_previous_month.strftime('%Y-%m-%d')
    end_date = first_day_current_month.strftime('%Y-%m-%d')

    print(f"Getting cost breakdown for account {account['accountId']} ({account['accountName']}) for {start_date} to {end_date}")
    
    # Get AWS session using account details
    session = get_aws_session(
        region_name=account["regionName"],
        role_arn=account['accountKeys']['role_arn'],
        profile_name=account['accountKeys']['profile_name'],
        access_key=account['accountKeys']['access_key'],
        secret_key=account['accountKeys']['secret_access_key'],
        session_token=account['accountKeys']['key_session_token']
    )
    
    # Create Cost Explorer client
    ce_client = session.client('ce')
    
    # Query Cost Explorer API for regions
    region_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'REGION'
            }
        ]
    )
    
    # Query Cost Explorer API for services
    service_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            }
        ]
    )
    
    # Query Cost Explorer API for region and service combination
    region_service_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': start_date,
            'End': end_date
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost'],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'REGION'
            },
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            }
        ]
    )
    
    # Process response to extract region-wise costs
    regions = {}
    for time_period in region_response['ResultsByTime']:
        for group in time_period['Groups']:
            region = group['Keys'][0] if group['Keys'][0] else 'No Region'
            cost = round(float(group['Metrics']['UnblendedCost']['Amount']), 2)
            
            if cost > 0:
                if region in regions:
                    regions[region] += cost
                else:
                    regions[region] = cost
    
    # Process response to extract service-wise costs
    services = {}
    for time_period in service_response['ResultsByTime']:
        for group in time_period['Groups']:
            service = group['Keys'][0] if group['Keys'][0] else 'No Service'
            cost = round(float(group['Metrics']['UnblendedCost']['Amount']), 2)
            
            if cost > 0:
                if service in services:
                    services[service] += cost
                else:
                    services[service] = cost
    
    # Process response to extract region-service costs
    region_services = {}
    for time_period in region_service_response['ResultsByTime']:
        for group in time_period['Groups']:
            region = group['Keys'][0] if group['Keys'][0] else 'No Region'
            service = group['Keys'][1] if len(group['Keys']) > 1 and group['Keys'][1] else 'No Service'
            cost = round(float(group['Metrics']['UnblendedCost']['Amount']), 2)
            
            if cost > 0:
                if region not in region_services:
                    region_services[region] = {}
                if service in region_services[region]:
                    region_services[region][service] += cost
                else:
                    region_services[region][service] = cost
    
    # Sort regions and services by cost in descending order
    sorted_regions = dict(sorted(regions.items(), key=lambda x: x[1], reverse=True))
    sorted_services = dict(sorted(services.items(), key=lambda x: x[1], reverse=True))
    
    # Sort services within each region
    sorted_region_services = {}
    for region in sorted(region_services.keys()):
        sorted_region_services[region] = dict(sorted(region_services[region].items(), key=lambda x: x[1], reverse=True))
    
    # Calculate total cost
    total_cost = round(sum(regions.values()), 2)
    
    return {
        'accountId': account['accountId'],
        'accountName': account['accountName'],
        'period': f"{start_date} to {end_date}",
        'total': total_cost,
        'regions': sorted_regions,
        'services': sorted_services,
        'regionServices': sorted_region_services
    }


def get_cost_by_region_all_accounts():
    """Get cost breakdown by region for all accounts"""
    accounts = load_account_details()
    results = []
    
    for account in accounts:
        try:
            account_cost = get_cost_by_region_for_account(account)
            results.append(account_cost)
            account["regions"] = list(account_cost["regions"].keys())
            account["services"] = list(account_cost["services"].keys())
        except Exception as e:
            results.append({
                'accountId': account['accountId'],
                'accountName': account['accountName'],
                'error': str(e)
            })
    
    # Save to file
    with open('cost_breakdown_by_region.json', 'w') as f:
        json.dump(results, f, indent=4)

    # Save updated accounts data to file
    with open('account_details.json', 'w') as f:
        json.dump(accounts, f, indent=4)
    
    return json.dumps(results, indent=4)


if __name__ == "__main__":
    cost_data = get_cost_by_region_all_accounts()
    print("Cost data saved to cost_breakdown_by_region.json")
    print(cost_data)
