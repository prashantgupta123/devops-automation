"""Control Catalog Controls fetcher and Excel generator."""

import json
import logging
import sys
import xlsxwriter
from datetime import datetime
from typing import List, Dict, Any
from AWSSession import get_aws_session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def fetch_all_controls(input_file: str = "input.json") -> List[Dict[str, Any]]:
    """
    Fetch all controls from AWS Control Catalog and generate Excel report.
    
    Args:
        input_file: Path to input JSON file containing AWS credentials
        
    Returns:
        List of all controls with detailed information
    """
    logger.info(f"Loading credentials from {input_file}")
    # Load credentials
    with open(input_file, 'r') as f:
        config = json.load(f)
    
    session = get_aws_session(config["awsCredentials"])
    client = session.client('controlcatalog')
    max_results = 100
    
    logger.info("Fetching all controls from Control Catalog")
    # Fetch all controls
    controls = []
    next_token = None
    
    while True:
        params = {'MaxResults': max_results}
        if next_token:
            params['NextToken'] = next_token
            
        response = client.list_controls(**params)
        controls.extend(response['Controls'])
        logger.info(f"Fetched {len(response['Controls'])} controls, total: {len(controls)}")
        
        next_token = response.get('NextToken')
        if not next_token:
            break
    
    logger.info(f"Getting detailed information for {len(controls)} controls")
    # Get detailed info for each control
    detailed_controls = []
    for i, control in enumerate(controls, 1):
        logger.info(f"Processing control {i}/{len(controls)}: {control.get('Name', 'Unknown')}")
        try:
            detail = client.get_control(ControlArn=control['Arn'])
            
            # Get related controls
            mappings = []
            mapping_token = None
            while True:
                map_params = {
                    'MaxResults': max_results,
                    'Filter': {
                        'ControlArns': [control['Arn']],
                        'MappingTypes': ['RELATED_CONTROL']
                    }
                }
                if mapping_token:
                    map_params['NextToken'] = mapping_token
                    
                map_response = client.list_control_mappings(**map_params)
                mappings.extend(map_response['ControlMappings'])
                
                mapping_token = map_response.get('NextToken')
                if not mapping_token:
                    break
            
            # Get common control mappings
            common_mappings = []
            mapping_token = None
            while True:
                map_params = {
                    'MaxResults': max_results,
                    'Filter': {
                        'ControlArns': [control['Arn']],
                        'MappingTypes': ['COMMON_CONTROL']
                    }
                }
                if mapping_token:
                    map_params['NextToken'] = mapping_token
                    
                map_response = client.list_control_mappings(**map_params)
                common_mappings.extend(map_response['ControlMappings'])
                
                mapping_token = map_response.get('NextToken')
                if not mapping_token:
                    break
            
            detail['RelatedControls'] = mappings
            detail['CommonControls'] = common_mappings
            detailed_controls.append(detail)
            
        except Exception as e:
            logger.error(f"Error processing control {control.get('Name', 'Unknown')}: {str(e)}")
            # Add basic control info even if detailed fetch fails
            control['RelatedControls'] = []
            control['CommonControls'] = []
            detailed_controls.append(control)
    
    logger.info("Fetching domains")
    # Fetch domains
    domains = []
    next_token = None
    
    while True:
        params = {'MaxResults': max_results}
        if next_token:
            params['NextToken'] = next_token
            
        response = client.list_domains(**params)
        domains.extend(response['Domains'])
        logger.info(f"Fetched {len(response['Domains'])} domains, total: {len(domains)}")
        
        next_token = response.get('NextToken')
        if not next_token:
            break
    
    logger.info("Fetching objectives")
    # Fetch objectives
    objectives = []
    next_token = None
    
    while True:
        params = {'MaxResults': max_results}
        if next_token:
            params['NextToken'] = next_token
            
        response = client.list_objectives(**params)
        objectives.extend(response['Objectives'])
        logger.info(f"Fetched {len(response['Objectives'])} objectives, total: {len(objectives)}")
        
        next_token = response.get('NextToken')
        if not next_token:
            break
    
    logger.info("Fetching common controls")
    # Fetch common controls
    common_controls = []
    next_token = None
    
    while True:
        params = {'MaxResults': max_results}
        if next_token:
            params['NextToken'] = next_token
            
        response = client.list_common_controls(**params)
        common_controls.extend(response['CommonControls'])
        logger.info(f"Fetched {len(response['CommonControls'])} common controls, total: {len(common_controls)}")
        
        next_token = response.get('NextToken')
        if not next_token:
            break
    
    # Enrich common controls with domain and objective details
    domains_dict = {domain['Arn']: domain for domain in domains}
    objectives_dict = {objective['Arn']: objective for objective in objectives}
    
    for control in common_controls:
        domain_arn = control.get('Domain', {}).get('Arn')
        if domain_arn and domain_arn in domains_dict:
            control['Domain'] = domains_dict[domain_arn]
        
        objective_arn = control.get('Objective', {}).get('Arn')
        if objective_arn and objective_arn in objectives_dict:
            control['Objective'] = objectives_dict[objective_arn]
    
    logger.info("Generating Excel report")
    output_file = "detailed_controls.json"
    with open(output_file, 'w') as f:
        json.dump(detailed_controls, f, indent=4, default=str)
    # Generate Excel report
    generate_excel_report(detailed_controls, common_controls)
    
    return detailed_controls


def generate_excel_report(controls: List[Dict[str, Any]], common_controls: List[Dict[str, Any]]):
    """Generate Excel report for controls."""
    logger.info("Creating Excel workbook")
    workbook = xlsxwriter.Workbook('aws_controls_report.xlsx')
    
    # Define formats
    header_format = workbook.add_format({
        'bold': True,
        'text_wrap': True,
        "align": "center",
        "valign": "vcenter",
        'fg_color': '#D7E4BC',
        'border': 1
    })
    
    cell_format = workbook.add_format({
        "text_wrap": True,
        "valign": "vcenter",
        "border": 1
    })
    
    # Get unique severities from controls
    unique_severities = sorted(set(control.get('Severity', '') for control in controls if control.get('Severity')))
    logger.info(f"Found unique severities: {unique_severities}")
    
    # Group controls by behavior
    behavior_groups = {}
    for control in controls:
        behavior = control.get('Behavior', 'Unknown')
        if behavior not in behavior_groups:
            behavior_groups[behavior] = []
        behavior_groups[behavior].append(control)
    
    logger.info(f"Grouped controls by behavior: {list(behavior_groups.keys())}")
    
    # Create Summary sheet
    logger.info("Creating Summary sheet")
    summary_sheet = workbook.add_worksheet('Summary')
    summary_sheet.set_row(0, 30)
    summary_sheet.write(0, 0, 'Behavior', header_format)
    summary_sheet.set_column(0, 0, 20)
    summary_sheet.write(0, 1, 'Total Count', header_format)
    summary_sheet.set_column(1, 1, 20)
    
    # Write severity headers dynamically
    for col, severity in enumerate(unique_severities, 2):
        summary_sheet.write(0, col, severity, header_format)
        summary_sheet.set_column(col, col, 20)
    
    row = 1
    for behavior, behavior_controls in behavior_groups.items():
        severity_counts = {severity: 0 for severity in unique_severities}
        for control in behavior_controls:
            severity = control.get('Severity', '')
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        summary_sheet.set_row(row, 20)
        summary_sheet.write(row, 0, behavior, cell_format)
        summary_sheet.write(row, 1, len(behavior_controls), cell_format)
        
        # Write severity counts dynamically
        for col, severity in enumerate(unique_severities, 2):
            summary_sheet.write(row, col, severity_counts[severity], cell_format)
        row += 1
    
    # Create main Controls sheet
    logger.info("Creating main Controls sheet")
    create_controls_sheet(workbook, 'Controls', controls, header_format, cell_format)
    
    # Create Common Controls sheet
    logger.info(f"Creating Common Controls sheet with {len(common_controls)} controls")
    create_common_controls_sheet(workbook, 'Common Controls', common_controls, header_format, cell_format)
    
    # Create behavior-specific sheets
    for behavior, behavior_controls in behavior_groups.items():
        logger.info(f"Creating {behavior} sheet with {len(behavior_controls)} controls")
        create_controls_sheet(workbook, behavior, behavior_controls, header_format, cell_format)
    
    workbook.close()
    logger.info("Excel report generated: aws_controls_report.xlsx")


def create_controls_sheet(workbook, sheet_name, controls, header_format, cell_format):
    """Create a controls sheet with given controls."""
    worksheet = workbook.add_worksheet(sheet_name)
    
    # Headers
    headers = ['Name', 'ARN', 'Aliases', 'Description', 'Behavior', 'Severity', 'Implementation Type', 
               'Implementation ID', 'Scope', 'Deployable Regions', 'Governed Resources', 
               'Parameters', 'Related Controls', 'Common Controls', 'Create Time']
    
    worksheet.set_row(0, 30)
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
        worksheet.set_column(col, col, 20)
    
    # Data rows
    for row, control in enumerate(controls, 1):
        worksheet.write(row, 0, control.get('Name', ''), cell_format)
        worksheet.write(row, 1, control.get('Arn', ''), cell_format)
        worksheet.write(row, 2, ', '.join(control.get('Aliases', [])), cell_format)
        worksheet.write(row, 3, control.get('Description', ''), cell_format)
        worksheet.write(row, 4, control.get('Behavior', ''), cell_format)
        worksheet.write(row, 5, control.get('Severity', ''), cell_format)
        worksheet.write(row, 6, control.get('Implementation', {}).get('Type', ''), cell_format)
        implementation_id = control.get('Implementation', {}).get('Identifier', '')
        if not implementation_id:
            implementation_id = ', '.join(control.get('Aliases', []))
        worksheet.write(row, 7, implementation_id, cell_format)
        worksheet.write(row, 8, control.get('RegionConfiguration', {}).get('Scope', ''), cell_format)
        worksheet.write(row, 9, ', '.join(control.get('RegionConfiguration', {}).get('DeployableRegions', [])), cell_format)
        worksheet.write(row, 10, ', '.join(control.get('GovernedResources', [])), cell_format)
        worksheet.write(row, 11, ', '.join([p.get('Name', '') for p in control.get('Parameters', [])]), cell_format)
        
        related = []
        for mapping in control.get('RelatedControls', []):
            if mapping.get('Mapping', {}).get('RelatedControl'):
                related.append(mapping['Mapping']['RelatedControl']['ControlArn'])
        worksheet.write(row, 12, ', '.join(related), cell_format)
        
        common = []
        for mapping in control.get('CommonControls', []):
            if mapping.get('Mapping', {}).get('CommonControl'):
                common.append(mapping['Mapping']['CommonControl']['CommonControlArn'])
        worksheet.write(row, 13, ', '.join(common), cell_format)
        
        create_time = control.get('CreateTime', '')
        if create_time:
            create_time = create_time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(create_time, datetime) else str(create_time)
        worksheet.write(row, 14, create_time, cell_format)


def create_common_controls_sheet(workbook, sheet_name, common_controls, header_format, cell_format):
    """Create a common controls sheet."""
    worksheet = workbook.add_worksheet(sheet_name)
    
    # Headers
    headers = ['Name', 'ARN', 'Description', 'Domain Name', 'Domain ARN', 'Domain Description',
               'Objective Name', 'Objective ARN', 'Objective Description', 'Create Time', 'Last Update Time']
    
    worksheet.set_row(0, 30)
    for col, header in enumerate(headers):
        worksheet.write(0, col, header, header_format)
        worksheet.set_column(col, col, 20)
    
    # Data rows
    for row, control in enumerate(common_controls, 1):
        worksheet.write(row, 0, control.get('Name', ''), cell_format)
        worksheet.write(row, 1, control.get('Arn', ''), cell_format)
        worksheet.write(row, 2, control.get('Description', ''), cell_format)
        worksheet.write(row, 3, control.get('Domain', {}).get('Name', ''), cell_format)
        worksheet.write(row, 4, control.get('Domain', {}).get('Arn', ''), cell_format)
        worksheet.write(row, 5, control.get('Domain', {}).get('Description', ''), cell_format)
        worksheet.write(row, 6, control.get('Objective', {}).get('Name', ''), cell_format)
        worksheet.write(row, 7, control.get('Objective', {}).get('Arn', ''), cell_format)
        worksheet.write(row, 8, control.get('Objective', {}).get('Description', ''), cell_format)
        
        create_time = control.get('CreateTime', '')
        if create_time:
            create_time = create_time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(create_time, datetime) else str(create_time)
        worksheet.write(row, 9, create_time, cell_format)
        
        update_time = control.get('LastUpdateTime', '')
        if update_time:
            update_time = update_time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(update_time, datetime) else str(update_time)
        worksheet.write(row, 10, update_time, cell_format)


if __name__ == "__main__":
    controls = fetch_all_controls()
    logger.info(f"Found {len(controls)} controls")
