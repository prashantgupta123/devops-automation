"""AWS Cost Optimization Hub Main Function.

Retrieves cost optimization recommendations and summaries from AWS.
"""

import json
import sys
import logging
from datetime import datetime
from pathlib import Path
from AWSSession import get_aws_session
from Notification import send_email
import xlsxwriter
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def load_config(config_path: str = "input.json") -> dict:
    """Load configuration from JSON file."""
    with open(config_path, 'r') as f:
        return json.load(f)


def load_accounts() -> list:
    """Load accounts from account_details.json if exists, otherwise return None."""
    try:
        with open('account_details.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def list_recommendation_summaries(client, max_results: int = 50) -> dict:
    """Retrieve recommendation summaries from Cost Optimization Hub."""
    logger.info("Fetching recommendation summaries")
    all_items = []
    next_token = None
    
    while True:
        params = {'maxResults': max_results, 'groupBy': 'ResourceType'}
        if next_token:
            params['nextToken'] = next_token
        
        response = client.list_recommendation_summaries(**params)
        all_items.extend(response.get('items', []))
        
        next_token = response.get('nextToken')
        if not next_token:
            break
    
    response['items'] = all_items
    
    # output_file = f"recommendation_summaries.json"
    # with open(output_file, 'w') as f:
    #     json.dump(response, f, indent=2, default=str)
    # logger.info(f"Recommendation summaries saved to {output_file}")

    return response


def list_recommendations(client, max_results: int = 50) -> dict:
    """Retrieve detailed recommendations from Cost Optimization Hub."""
    logger.info("Fetching recommendations")
    all_items = []
    next_token = None
    
    while True:
        params = {'maxResults': max_results, 'includeAllRecommendations': True, 'orderBy': {'dimension': 'ResourceType', 'order': 'Asc'}}
        if next_token:
            params['nextToken'] = next_token
        
        response = client.list_recommendations(**params)
        all_items.extend(response.get('items', []))
        
        next_token = response.get('nextToken')
        if not next_token:
            break
    
    response['items'] = all_items

    # output_file = f"recommendations.json"
    # with open(output_file, 'w') as f:
    #     json.dump(response, f, indent=2, default=str)
    # logger.info(f"Recommendations saved to {output_file}")

    return response


def create_excel_report(summaries: dict, recommendations: dict, config: dict) -> str:
    """Create Excel report with summaries and recommendations."""
    filename = f"aws_cost_optimization_report.xlsx"
    
    workbook = xlsxwriter.Workbook(filename)
    
    header_format = workbook.add_format({
        "bold": True,
        "text_wrap": True,
        "align": "center",
        "valign": "vcenter",
        "fg_color": "#D7E4BC",
        "border": 1
    })
    
    cell_format = workbook.add_format({
        "border": 1,
        "text_wrap": True,
        "valign": "vcenter"
    })
    
    # Get currency code from first recommendation
    currency_code = recommendations.get('items', [{}])[0].get('currencyCode', 'USD') if recommendations.get('items') else 'USD'
    
    # Currency format for monetary values
    currency_format = workbook.add_format({
        "border": 1,
        "valign": "vcenter",
        "num_format": f'"$"#,##0.00' if currency_code == 'USD' else '#,##0.00'
    })
    
    # Summary sheet
    summary_sheet = workbook.add_worksheet("Summary")
    summary_headers = ["Account ID", "Account Name", "Resource Type", f"Estimated Monthly Savings ({currency_code})", "Recommendation Count"]
    for col, header in enumerate(summary_headers):
        summary_sheet.write(0, col, header, header_format)
    
    for row, item in enumerate(summaries.get('items', []), start=1):
        summary_sheet.set_row(row, 20)
        summary_sheet.write(row, 0, item.get('accountId', ''), cell_format)
        summary_sheet.write(row, 1, item.get('accountName', ''), cell_format)
        summary_sheet.write(row, 2, item.get('group', ''), cell_format)
        summary_sheet.write(row, 3, item.get('estimatedMonthlySavings', 0), currency_format)
        summary_sheet.write(row, 4, item.get('recommendationCount', 0), cell_format)
    
    summary_sheet.set_row(0, 30)
    summary_sheet.set_column(0, 0, 30)
    summary_sheet.set_column(1, 4, 30)
    
    # All Recommendations sheet
    rec_sheet = workbook.add_worksheet("All Recommendations")
    rec_headers = [
        "Account ID", "Account Name", "Region", "Resource Type", "Resource ID", "Recommended Action", 
        "Current Resource Summary", "Recommended Resource Summary", "Estimated Savings Percentage", 
        f"Estimated Monthly Savings ({currency_code})", f"Estimated Monthly Cost ({currency_code})", "Implementation Effort", 
        "Is Resource Restart Needed", "Is Rollback Possible", "Source", "Tags"
    ]
    
    for col, header in enumerate(rec_headers):
        rec_sheet.write(0, col, header, header_format)
    
    items = recommendations.get('items', [])
    
    for row, item in enumerate(items, start=1):
        account_id = item.get('accountId', '')
        account_name = item.get('accountName', '')
        tags = ', '.join([f"{t.get('key', '')}={t.get('value', '')}" for t in item.get('tags', [])])
        
        rec_sheet.write(row, 0, account_id, cell_format)
        rec_sheet.write(row, 1, account_name, cell_format)
        rec_sheet.write(row, 2, item.get('region', ''), cell_format)
        rec_sheet.write(row, 3, item.get('currentResourceType', ''), cell_format)
        rec_sheet.write(row, 4, item.get('resourceId', ''), cell_format)
        rec_sheet.write(row, 5, item.get('actionType', ''), cell_format)
        rec_sheet.write(row, 6, item.get('currentResourceSummary', ''), cell_format)
        rec_sheet.write(row, 7, item.get('recommendedResourceSummary', ''), cell_format)
        rec_sheet.write(row, 8, item.get('estimatedSavingsPercentage', 0), cell_format)
        rec_sheet.write(row, 9, item.get('estimatedMonthlySavings', 0), currency_format)
        rec_sheet.write(row, 10, item.get('estimatedMonthlyCost', 0), currency_format)
        rec_sheet.write(row, 11, item.get('implementationEffort', ''), cell_format)
        rec_sheet.write(row, 12, item.get('restartNeeded', ''), cell_format)
        rec_sheet.write(row, 13, item.get('rollbackPossible', ''), cell_format)
        rec_sheet.write(row, 14, item.get('source', ''), cell_format)
        rec_sheet.write(row, 15, tags, cell_format)
    
    rec_sheet.set_row(0, 30)
    rec_sheet.set_column(0, 15, 20)
    
    # Group by Resource Type
    grouped = defaultdict(list)
    for item in items:
        grouped[item.get('currentResourceType', 'Unknown')].append(item)
    
    for resource_type, type_items in grouped.items():
        sheet_name = resource_type[:31]
        type_sheet = workbook.add_worksheet(sheet_name)
        
        for col, header in enumerate(rec_headers):
            type_sheet.write(0, col, header, header_format)

        type_sheet.set_row(0, 30)
        
        for row, item in enumerate(type_items, start=1):
            account_id = item.get('accountId', '')
            account_name = item.get('accountName', '')
            tags = ', '.join([f"{t.get('key', '')}={t.get('value', '')}" for t in item.get('tags', [])])
            
            type_sheet.write(row, 0, account_id, cell_format)
            type_sheet.write(row, 1, account_name, cell_format)
            type_sheet.write(row, 2, item.get('region', ''), cell_format)
            type_sheet.write(row, 3, item.get('currentResourceType', ''), cell_format)
            type_sheet.write(row, 4, item.get('resourceId', ''), cell_format)
            type_sheet.write(row, 5, item.get('actionType', ''), cell_format)
            type_sheet.write(row, 6, item.get('currentResourceSummary', ''), cell_format)
            type_sheet.write(row, 7, item.get('recommendedResourceSummary', ''), cell_format)
            type_sheet.write(row, 8, item.get('estimatedSavingsPercentage', 0), cell_format)
            type_sheet.write(row, 9, item.get('estimatedMonthlySavings', 0), currency_format)
            type_sheet.write(row, 10, item.get('estimatedMonthlyCost', 0), currency_format)
            type_sheet.write(row, 11, item.get('implementationEffort', ''), cell_format)
            type_sheet.write(row, 12, item.get('restartNeeded', ''), cell_format)
            type_sheet.write(row, 13, item.get('rollbackPossible', ''), cell_format)
            type_sheet.write(row, 14, item.get('source', ''), cell_format)
            type_sheet.write(row, 15, tags, cell_format)
        
        type_sheet.set_column(0, 15, 20)
    
    workbook.close()
    logger.info(f"Excel report created: {filename}")
    return filename


def create_email_content(summaries: dict, recommendations: dict) -> str:
    """Create HTML email content with summary table."""
    currency_code = recommendations.get('items', [{}])[0].get('currencyCode', 'USD') if recommendations.get('items') else 'USD'
    total_savings = summaries.get('estimatedTotalDedupedSavings', 0)
    total_recommendations = len(recommendations.get('items', []))
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            h2 {{ color: #2c3e50; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th {{ background-color: #D7E4BC; padding: 12px; text-align: left; border: 1px solid #ddd; }}
            td {{ padding: 10px; border: 1px solid #ddd; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .note {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0; }}
            .summary {{ color: #27ae60; font-size: 18px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <h2>AWS Cost Optimization Hub Report</h2>
        <p>Dear Team,</p>
        <p>Please find the AWS Cost Optimization recommendations for your review.</p>
        
        <p class="summary">Total Estimated Monthly Savings: {currency_code} {total_savings:,.2f}</p>
        <p class="summary">Total Recommendations: {total_recommendations}</p>
        
        <h3>Summary by Resource Type</h3>
        <table>
            <tr>
                <th>Account ID</th>
                <th>Account Name</th>
                <th>Resource Type</th>
                <th>Estimated Monthly Savings ({currency_code})</th>
                <th>Recommendation Count</th>
            </tr>
    """
    
    for item in summaries.get('items', []):
        html += f"""
            <tr>
                <td>{item.get('accountId', '')}</td>
                <td>{item.get('accountName', '')}</td>
                <td>{item.get('group', '')}</td>
                <td>{item.get('estimatedMonthlySavings', 0):,.2f}</td>
                <td>{item.get('recommendationCount', 0)}</td>
            </tr>
        """
    
    html += """
        </table>
        
        <div class="note">
            <h4>Important Notes:</h4>
            <ul>
                <li><strong>Review Recommendations:</strong> Please review all recommendations in the attached Excel report before implementation.</li>
                <li><strong>Implementation Effort:</strong> Each recommendation includes an implementation effort indicator (VeryLow, Low, Medium, High) to help prioritize actions.</li>
                <li><strong>Rollback Capability:</strong> Check the "Is Rollback Possible" column before implementing changes to understand reversibility.</li>
                <li><strong>Resource Restart:</strong> Some recommendations may require resource restarts. Plan accordingly to minimize service disruption.</li>
                <li><strong>Savings Plans & Reserved Instances:</strong> Consider your organization's commitment capacity before purchasing savings plans or reserved instances.</li>
                <li><strong>Testing:</strong> Test recommendations in non-production environments first when possible.</li>
                <li><strong>Regular Review:</strong> Cost optimization is an ongoing process. Review recommendations regularly for continuous savings.</li>
            </ul>
        </div>
        
        <p>For detailed information, please refer to the attached Excel report which contains:</p>
        <ul>
            <li>Summary sheet with aggregated savings by resource type</li>
            <li>All recommendations with complete details</li>
            <li>Separate sheets grouped by resource type for easier analysis</li>
        </ul>
        
        <p>If you have any questions or need assistance with implementation, please don't hesitate to reach out.</p>
        
        <p>Best regards,<br>AWS Cost Optimization Team</p>
    </body>
    </html>
    """
    
    return html
    return filename


def main():
    """Main function to retrieve AWS Cost Optimization Hub data."""
    try:
        # Check if account_details.json exists
        accounts = load_accounts()
        
        all_summaries = {'items': []}
        all_recommendations = {'items': []}
        
        if accounts:
            logger.info(f"Processing {len(accounts)} accounts from account_details.json")
            for account in accounts:
                logger.info(f"Processing account: {account.get('accountName', '')} ({account.get('accountId', '')})")
                
                session = get_aws_session(account['accountKeys'])
                client = session.client('cost-optimization-hub', region_name='us-east-1')
                
                summaries = list_recommendation_summaries(client, max_results=50)
                recommendations = list_recommendations(client, max_results=50)
                
                # Add account info to items
                for item in summaries.get('items', []):
                    item['accountId'] = account.get('accountId', '')
                    item['accountName'] = account.get('accountName', '')
                
                for item in recommendations.get('items', []):
                    item['accountName'] = account.get('accountName', '')
                
                all_summaries['items'].extend(summaries.get('items', []))
                all_recommendations['items'].extend(recommendations.get('items', []))
            
            config = {'awsCredentials': {'account_name': 'Multiple Accounts'}}
            
            # Load email config from input.json if available
            try:
                input_config = load_config()
                if 'smtpCredentials' in input_config:
                    config['smtpCredentials'] = input_config['smtpCredentials']
                if 'emailNotification' in input_config:
                    config['emailNotification'] = input_config['emailNotification']
            except:
                pass
        else:
            logger.info("Processing single account from input.json")
            config = load_config()
            
            session = get_aws_session(config['awsCredentials'])
            client = session.client('cost-optimization-hub', region_name='us-east-1')
            
            all_summaries = list_recommendation_summaries(client, max_results=50)
            all_recommendations = list_recommendations(client, max_results=50)
            
            # Add account info to items
            account_id = config['awsCredentials'].get('account_id', '')
            account_name = config['awsCredentials'].get('account_name', '')
            
            for item in all_summaries.get('items', []):
                item['accountId'] = account_id
                item['accountName'] = account_name
            
            for item in all_recommendations.get('items', []):
                item['accountName'] = account_name
        
        logger.info(f"Total recommendations: {len(all_recommendations.get('items', []))}")
        
        # Create Excel report
        report_file = create_excel_report(all_summaries, all_recommendations, config)
        
        # Send email notification
        if config.get('smtpCredentials') and config.get('emailNotification'):
            try:
                email_content = create_email_content(all_summaries, all_recommendations)
                email_details = config['emailNotification'].copy()
                email_details['attachments'] = [report_file]
                
                send_email(config['smtpCredentials'], email_details, email_content)
                logger.info("Email notification sent successfully")
            except Exception as e:
                logger.error(f"Failed to send email notification: {str(e)}")
        else:
            logger.info("Email notification skipped - SMTP or email configuration not provided")
        
        logger.info("Cost optimization data retrieval completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise


if __name__ == "__main__":
    main()
