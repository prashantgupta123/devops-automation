import json
import logging
import sys
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


def list_enabled_controls(client, target_identifier: str, max_results: int = 100) -> List[Dict[str, Any]]:
    """Fetch list of enabled controls from AWS Control Tower.
    
    Args:
        client: boto3 controltower client
        target_identifier: Target OU ARN
        max_results: Maximum results per page
        
    Returns:
        List of enabled controls
    """
    logger.info(f"Fetching enabled controls for target: {target_identifier}")
    enabled_controls = []
    next_token = None
    
    while True:
        params = {'targetIdentifier': target_identifier, 'maxResults': max_results}
        if next_token:
            params['nextToken'] = next_token
            
        response = client.list_enabled_controls(**params)
        enabled_controls.extend(response['enabledControls'])
        logger.info(f"Fetched {len(response['enabledControls'])} controls, total: {len(enabled_controls)}")
        
        next_token = response.get('nextToken')
        if not next_token:
            break
    
    logger.info(f"Total enabled controls for {target_identifier}: {len(enabled_controls)}")
    return enabled_controls


def list_organizational_units(client) -> List[Dict[str, Any]]:
    """Fetch list of organizational units from AWS Organizations.
    
    Args:
        client: boto3 organizations client
        
    Returns:
        List of organizational units with parent information
    """
    logger.info("Fetching organizational units")
    
    # Get root
    roots = client.list_roots()['Roots']
    root_id = roots[0]['Id']
    
    # Get all OUs recursively with parent info
    def get_ous_recursive(parent_id, parent_name="Root"):
        ous = []
        next_token = None
        
        while True:
            params = {'ParentId': parent_id}
            if next_token:
                params['NextToken'] = next_token
                
            response = client.list_organizational_units_for_parent(**params)
            current_ous = response['OrganizationalUnits']
            
            for ou in current_ous:
                ou['ParentId'] = parent_id
                ou['ParentName'] = parent_name
                ous.append(ou)
                
                # Get child OUs
                child_ous = get_ous_recursive(ou['Id'], ou['Name'])
                ous.extend(child_ous)
            
            next_token = response.get('NextToken')
            if not next_token:
                break
        
        return ous
    
    ous = get_ous_recursive(root_id)
    return ous


def enable_controls(client, config: Dict[str, Any], controls_by_ou: Dict[str, List[Dict[str, Any]]]):
    """Enable controls on target organizational units.
    
    Args:
        client: boto3 controltower client
        config: Configuration from input.json
        controls_by_ou: Dictionary of enabled controls by OU ID
    """
    logger.info("Starting control enablement process")
    
    enable_config = config["controlTower"]["enableControls"]
    
    for behavior, behavior_config in enable_config.items():
        logger.info(f"Processing behavior: {behavior}")
        
        # Get target identifiers
        target_identifiers = behavior_config.get("targetIdentifiers", config["controlTower"]["organizationalUnits"])
        control_identifiers = behavior_config["controlIdentifiers"]
        
        for target in target_identifiers:
            target_arn = target["Arn"]
            target_id = target["Id"]
            
            for control_config in control_identifiers:
                control_arn = control_config["Arn"]
                
                # Check if control is already enabled
                is_enabled = False
                if target_id in controls_by_ou:
                    for enabled_control in controls_by_ou[target_id]:
                        if enabled_control['controlIdentifier'] == control_arn:
                            is_enabled = True
                            break
                
                if is_enabled:
                    logger.info(f"Control {control_arn} already enabled on {target_arn}")
                    continue
                
                # Enable control
                logger.info(f"Enabling control {control_arn} on {target_arn}")
                try:
                    response = client.enable_control(
                        controlIdentifier=control_arn,
                        targetIdentifier=target_arn
                    )
                    logger.info(f"Successfully enabled control: {response['operationIdentifier']}")
                except Exception as e:
                    logger.error(f"Failed to enable control {control_arn} on {target_arn}: {str(e)}")


def main(input_file: str = "input.json", max_results: int = 100):
    """Main function to load credentials and fetch enabled controls."""
    logger.info(f"Loading credentials from {input_file}")
    with open(input_file, 'r') as f:
        config = json.load(f)
    
    session = get_aws_session(config["awsCredentials"])
    ct_client = session.client('controltower')
    org_client = session.client('organizations')
    catalog_client = session.client('controlcatalog')
    
    # List Organizational Units
    ous = list_organizational_units(org_client)
    logger.info(f"Total organizational units: {len(ous)}")
    with open('organizational_units.json', 'w') as f:
        json.dump(ous, f, indent=4, default=str)
    logger.info("Saved organizational units to organizational_units.json")
    
    # Fetch enabled controls for each OU
    controls_by_ou = {}
    for ou in config["controlTower"]["organizationalUnits"]:
        target_arn = ou["Arn"]
        target_id = ou["Id"]
        controls = list_enabled_controls(ct_client, target_arn, max_results)
        
        # Get control details from control catalog
        for control in controls:
            control_arn = control['controlIdentifier']
            logger.info(f"Fetching control details for: {control_arn}")
            control_detail = catalog_client.get_control(ControlArn=control_arn)
            control_detail.pop('ResponseMetadata', None)
            control['controlDetail'] = control_detail
        
        controls_by_ou[target_id] = controls
    logger.info(f"Found controls for {len(controls_by_ou)} organizational units")
    output_file = "enabled_controls.json"
    with open(output_file, 'w') as f:
        json.dump(controls_by_ou, f, indent=4, default=str)
    logger.info(f"Saved enabled controls to {output_file}")
    
    # Enable controls
    enable_controls(ct_client, config, controls_by_ou)
    
    return controls_by_ou

if __name__ == "__main__":
    main()
