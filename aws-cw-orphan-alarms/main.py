"""CloudWatch Orphan Alarm Detector.

Identifies and optionally deletes CloudWatch alarms monitoring non-existent AWS resources.
Supports EC2, RDS, ECS, Lambda, ALB, Target Groups, and SQS services.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml
import xlsxwriter
from boto3.session import Session

import AWSSession
from Notification import EmailNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
MAX_RESULTS = 100
CONFIG_FILE = "inputs.yml"
SERVICE_CONFIG_FILE = "input.json"
OUTPUT_FILE = "output.json"
REPORT_FILE = "Inventory.xlsx"


class ResourceDiscovery:
    """Discovers active AWS resources across multiple services."""
    
    def __init__(self, session: Session, region: str):
        """
        Initialize resource discovery with AWS session.
        
        Args:
            session: Configured boto3 session
            region: AWS region name
        """
        self.session = session
        self.region = region
        self.clients = self._initialize_clients()
    
    def _initialize_clients(self) -> Dict[str, Any]:
        """Initialize AWS service clients."""
        return {
            'ec2': self.session.client('ec2', region_name=self.region),
            'elbv2': self.session.client('elbv2', region_name=self.region),
            'rds': self.session.client('rds', region_name=self.region),
            'ecs': self.session.client('ecs', region_name=self.region),
            'lambda': self.session.client('lambda', region_name=self.region),
            'sqs': self.session.client('sqs', region_name=self.region),
            'cloudwatch': self.session.client('cloudwatch', region_name=self.region)
        }
    
    def discover_all_resources(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Discover all active resources across supported services.
        
        Returns:
            Dictionary mapping service names to lists of resource identifiers
        """
        logger.info("Starting resource discovery across all services")
        
        return {
            "EC2Instance": self._get_ec2_instances(),
            "RDSCluster": self._get_rds_clusters(),
            "RDSInstance": self._get_rds_instances(),
            "TargetGroup": self._get_target_groups(),
            "LoadBalancerTargetGroup": self._get_load_balancer_target_groups(),
            "LoadBalancer": self._get_load_balancers(),
            "ECSService": self._get_ecs_services(),
            "ECSCluster": self._get_ecs_clusters(),
            "Lambda": self._get_lambda_functions(),
            "LambdaResource": self._get_lambda_versions(),
            "SQS": self._get_sqs_queues()
        }
    
    def _paginate_api_call(
        self, 
        api_func: callable, 
        result_key: str,
        token_key: str = 'NextToken',
        **kwargs
    ) -> List[Any]:
        """
        Generic pagination handler for AWS API calls.
        
        Args:
            api_func: AWS API function to call
            result_key: Key in response containing results
            token_key: Key for pagination token
            **kwargs: Additional arguments for API call
        
        Returns:
            List of all paginated results
        """
        results = []
        next_token = None
        
        while True:
            try:
                if next_token:
                    kwargs[token_key] = next_token
                
                response = api_func(**kwargs)
                results.extend(response.get(result_key, []))
                
                next_token = response.get(token_key)
                if not next_token:
                    break
                    
            except Exception as e:
                logger.error("API pagination error: %s", e)
                break
        
        return results
    
    def _get_ec2_instances(self) -> List[Dict[str, str]]:
        """Get all EC2 instance IDs."""
        logger.info("Discovering EC2 instances")
        instances = []
        
        reservations = self._paginate_api_call(
            self.clients['ec2'].describe_instances,
            'Reservations',
            MaxResults=MAX_RESULTS
        )
        
        for reservation in reservations:
            for instance in reservation.get('Instances', []):
                instances.append({"InstanceId": instance['InstanceId']})
        
        logger.info("Found %d EC2 instances", len(instances))
        return instances
    
    def _get_rds_clusters(self) -> List[Dict[str, str]]:
        """Get all RDS cluster identifiers."""
        logger.info("Discovering RDS clusters")
        
        filters = [{
            'Name': 'engine',
            'Values': ['mysql', 'aurora-mysql', 'postgres', 'aurora-postgresql']
        }]
        
        clusters = self._paginate_api_call(
            self.clients['rds'].describe_db_clusters,
            'DBClusters',
            token_key='Marker',
            MaxRecords=MAX_RESULTS,
            Filters=filters
        )
        
        result = [{"DBClusterIdentifier": c['DBClusterIdentifier']} for c in clusters]
        logger.info("Found %d RDS clusters", len(result))
        return result
    
    def _get_rds_instances(self) -> List[Dict[str, str]]:
        """Get all RDS instance identifiers."""
        logger.info("Discovering RDS instances")
        
        filters = [{
            'Name': 'engine',
            'Values': ['mysql', 'aurora-mysql', 'postgres', 'aurora-postgresql']
        }]
        
        instances = self._paginate_api_call(
            self.clients['rds'].describe_db_instances,
            'DBInstances',
            token_key='Marker',
            MaxRecords=MAX_RESULTS,
            Filters=filters
        )
        
        result = [{"DBInstanceIdentifier": i['DBInstanceIdentifier']} for i in instances]
        logger.info("Found %d RDS instances", len(result))
        return result
    
    def _get_load_balancers(self) -> List[Dict[str, str]]:
        """Get all load balancer ARNs."""
        logger.info("Discovering load balancers")
        
        load_balancers = self._paginate_api_call(
            self.clients['elbv2'].describe_load_balancers,
            'LoadBalancers',
            token_key='Marker',
            PageSize=MAX_RESULTS
        )
        
        result = [
            {"LoadBalancer": lb['LoadBalancerArn'].split("loadbalancer/")[1]}
            for lb in load_balancers
        ]
        logger.info("Found %d load balancers", len(result))
        return result
    
    def _get_target_groups(self) -> List[Dict[str, str]]:
        """Get all target group ARNs."""
        logger.info("Discovering target groups")
        
        target_groups = self._paginate_api_call(
            self.clients['elbv2'].describe_target_groups,
            'TargetGroups',
            token_key='Marker',
            PageSize=MAX_RESULTS
        )
        
        result = [
            {"TargetGroup": f"targetgroup/{tg['TargetGroupArn'].split('targetgroup/')[1]}"}
            for tg in target_groups
        ]
        logger.info("Found %d target groups", len(result))
        return result
    
    def _get_load_balancer_target_groups(self) -> List[Dict[str, str]]:
        """Get target groups with their associated load balancers."""
        logger.info("Discovering load balancer target group associations")
        
        target_groups = self._paginate_api_call(
            self.clients['elbv2'].describe_target_groups,
            'TargetGroups',
            token_key='Marker',
            PageSize=MAX_RESULTS
        )
        
        result = []
        for tg in target_groups:
            tg_arn = f"targetgroup/{tg['TargetGroupArn'].split('targetgroup/')[1]}"
            for lb_arn in tg.get("LoadBalancerArns", []):
                result.append({
                    "LoadBalancer": lb_arn.split("loadbalancer/")[1],
                    "TargetGroup": tg_arn
                })
        
        logger.info("Found %d load balancer-target group associations", len(result))
        return result
    
    def _get_ecs_clusters(self) -> List[Dict[str, str]]:
        """Get all ECS cluster names."""
        logger.info("Discovering ECS clusters")
        
        cluster_arns = self._paginate_api_call(
            self.clients['ecs'].list_clusters,
            'clusterArns',
            token_key='nextToken',
            maxResults=MAX_RESULTS
        )
        
        result = [
            {"ClusterName": arn.split("cluster/")[1]}
            for arn in cluster_arns
        ]
        logger.info("Found %d ECS clusters", len(result))
        return result
    
    def _get_ecs_services(self) -> List[Dict[str, str]]:
        """Get all ECS services across all clusters."""
        logger.info("Discovering ECS services")
        
        cluster_arns = self._paginate_api_call(
            self.clients['ecs'].list_clusters,
            'clusterArns',
            token_key='nextToken',
            maxResults=MAX_RESULTS
        )
        
        services = []
        for cluster_arn in cluster_arns:
            cluster_name = cluster_arn.split("cluster/")[1]
            
            service_arns = self._paginate_api_call(
                self.clients['ecs'].list_services,
                'serviceArns',
                token_key='nextToken',
                cluster=cluster_arn,
                maxResults=MAX_RESULTS
            )
            
            for service_arn in service_arns:
                services.append({
                    "ClusterName": cluster_name,
                    "ServiceName": service_arn.split("/")[-1]
                })
        
        logger.info("Found %d ECS services", len(services))
        return services
    
    def _get_lambda_functions(self) -> List[Dict[str, str]]:
        """Get all Lambda function names."""
        logger.info("Discovering Lambda functions")
        
        functions = self._paginate_api_call(
            self.clients['lambda'].list_functions,
            'Functions',
            token_key='Marker',
            MaxItems=MAX_RESULTS
        )
        
        result = [{"FunctionName": f["FunctionName"]} for f in functions]
        logger.info("Found %d Lambda functions", len(result))
        return result
    
    def _get_lambda_versions(self) -> List[Dict[str, str]]:
        """Get all Lambda function versions and aliases."""
        logger.info("Discovering Lambda function versions")
        
        functions = self._paginate_api_call(
            self.clients['lambda'].list_functions,
            'Functions',
            token_key='Marker',
            MaxItems=MAX_RESULTS
        )
        
        versions = []
        for function in functions:
            function_name = function["FunctionName"]
            
            version_list = self._paginate_api_call(
                self.clients['lambda'].list_versions_by_function,
                'Versions',
                token_key='Marker',
                FunctionName=function_name,
                MaxItems=MAX_RESULTS
            )
            
            for version in version_list:
                resource = (
                    version["FunctionName"] if version["Version"] == "$LATEST"
                    else f"{version['FunctionName']}:{version['Version']}"
                )
                versions.append({
                    "FunctionName": version["FunctionName"],
                    "Resource": resource
                })
        
        logger.info("Found %d Lambda function versions", len(versions))
        return versions
    
    def _get_sqs_queues(self) -> List[Dict[str, str]]:
        """Get all SQS queue names."""
        logger.info("Discovering SQS queues")
        
        queue_urls = self._paginate_api_call(
            self.clients['sqs'].list_queues,
            'QueueUrls',
            MaxResults=MAX_RESULTS
        )
        
        result = [{"QueueName": url.split("/")[-1]} for url in queue_urls]
        logger.info("Found %d SQS queues", len(result))
        return result


class OrphanAlarmDetector:
    """Detects orphan CloudWatch alarms by comparing with active resources."""
    
    def __init__(self, cloudwatch_client: Any):
        """
        Initialize orphan alarm detector.
        
        Args:
            cloudwatch_client: Boto3 CloudWatch client
        """
        self.cloudwatch_client = cloudwatch_client
    
    def get_all_alarms(self) -> List[Dict[str, Any]]:
        """
        Retrieve all CloudWatch alarms.
        
        Returns:
            List of alarm dictionaries with name, namespace, and dimensions
        """
        logger.info("Retrieving all CloudWatch alarms")
        alarms = []
        next_token = None
        
        while True:
            try:
                kwargs = {'MaxRecords': MAX_RESULTS}
                if next_token:
                    kwargs['NextToken'] = next_token
                
                response = self.cloudwatch_client.describe_alarms(**kwargs)
                
                for alarm in response.get('MetricAlarms', []):
                    alarms.extend(self._extract_alarm_metrics(alarm))
                
                next_token = response.get('NextToken')
                if not next_token:
                    break
                    
            except Exception as e:
                logger.error("Error retrieving alarms: %s", e)
                break
        
        logger.info("Found %d CloudWatch alarms", len(alarms))
        return alarms
    
    @staticmethod
    def _extract_alarm_metrics(alarm: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract metrics from alarm definition.
        
        Handles both simple metric alarms and metric math alarms.
        
        Args:
            alarm: CloudWatch alarm definition
        
        Returns:
            List of alarm metric dictionaries
        """
        alarm_metrics = []
        
        try:
            if "Namespace" in alarm:
                # Simple metric alarm
                alarm_metrics.append({
                    "AlarmName": alarm["AlarmName"],
                    "Namespace": alarm["Namespace"],
                    "Dimensions": alarm.get("Dimensions", [])
                })
            elif "Metrics" in alarm:
                # Metric math alarm
                for metric in alarm["Metrics"]:
                    if "MetricStat" in metric:
                        alarm_metrics.append({
                            "AlarmName": alarm["AlarmName"],
                            "Namespace": metric["MetricStat"]["Metric"]["Namespace"],
                            "Dimensions": metric["MetricStat"]["Metric"].get("Dimensions", [])
                        })
            else:
                logger.warning("Alarm has no metrics: %s", alarm["AlarmName"])
                
        except Exception as e:
            logger.error("Error extracting metrics from alarm %s: %s", 
                        alarm.get("AlarmName", "unknown"), e)
        
        return alarm_metrics
    
    def find_orphan_alarms(
        self,
        service_config: Dict[str, Any],
        alarms: List[Dict[str, Any]],
        resources: Dict[str, List[Dict[str, str]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Identify orphan alarms across all services.
        
        Args:
            service_config: Service dimension configuration
            alarms: List of all CloudWatch alarms
            resources: Dictionary of active resources by service
        
        Returns:
            Dictionary mapping service names to lists of orphan alarms
        """
        logger.info("Analyzing alarms for orphans")
        orphan_alarms = {}
        
        for service_name, config in service_config.items():
            logger.info("Checking %s for orphan alarms", service_name)
            
            if service_name not in resources:
                logger.warning("No resources found for service: %s", service_name)
                continue
            
            service_orphans = []
            for namespace in config['Namespace']:
                service_orphans.extend(
                    self._check_service_orphans(
                        config, namespace, alarms, resources[service_name]
                    )
                )
            
            if service_orphans:
                orphan_alarms[service_name] = service_orphans
                logger.info("Found %d orphan alarms for %s", 
                           len(service_orphans), service_name)
        
        return orphan_alarms
    
    @staticmethod
    def _check_service_orphans(
        resource_config: Dict[str, List[str]],
        namespace: str,
        alarms: List[Dict[str, Any]],
        service_resources: List[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """
        Check for orphan alarms for a specific service.
        
        Args:
            resource_config: Service dimension configuration
            namespace: CloudWatch namespace to check
            alarms: List of all alarms
            service_resources: List of active resources for this service
        
        Returns:
            List of orphan alarms for this service
        """
        orphans = []
        required_dimensions = resource_config['Dimension']
        excluded_dimensions = resource_config.get('ExcludeDimension', [])
        
        for alarm in alarms:
            if alarm['Namespace'] != namespace:
                continue
            
            # Check if alarm has required dimensions
            alarm_dims = {d['Name']: d['Value'] for d in alarm['Dimensions']}
            
            if not OrphanAlarmDetector._has_required_dimensions(
                alarm_dims, required_dimensions, excluded_dimensions
            ):
                continue
            
            # Check if alarm matches any active resource
            if not OrphanAlarmDetector._matches_any_resource(
                alarm_dims, required_dimensions, service_resources
            ):
                orphans.append(alarm)
        
        return orphans
    
    @staticmethod
    def _has_required_dimensions(
        alarm_dims: Dict[str, str],
        required: List[str],
        excluded: List[str]
    ) -> bool:
        """Check if alarm has all required dimensions and no excluded ones."""
        has_all_required = all(dim in alarm_dims for dim in required)
        has_no_excluded = not any(dim in alarm_dims for dim in excluded if dim)
        return has_all_required and has_no_excluded
    
    @staticmethod
    def _matches_any_resource(
        alarm_dims: Dict[str, str],
        required_dims: List[str],
        resources: List[Dict[str, str]]
    ) -> bool:
        """Check if alarm dimensions match any active resource."""
        for resource in resources:
            if all(alarm_dims.get(dim) == resource.get(dim) for dim in required_dims):
                return True
        return False
    
    def delete_orphan_alarms(
        self, 
        orphan_alarms: Dict[str, List[Dict[str, Any]]]
    ) -> None:
        """
        Delete identified orphan alarms.
        
        Args:
            orphan_alarms: Dictionary of orphan alarms by service
        """
        for service, alarms in orphan_alarms.items():
            alarm_names = [alarm["AlarmName"] for alarm in alarms]
            
            if not alarm_names:
                continue
            
            try:
                self.cloudwatch_client.delete_alarms(AlarmNames=alarm_names)
                logger.info("Deleted %d orphan alarms for %s", 
                           len(alarm_names), service)
            except Exception as e:
                logger.error("Error deleting alarms for %s: %s", service, e)


class ReportGenerator:
    """Generates Excel reports for orphan alarms."""
    
    @staticmethod
    def create_excel_report(
        service_config: Dict[str, Any],
        orphan_alarms: Dict[str, List[Dict[str, Any]]],
        output_path: str = REPORT_FILE
    ) -> None:
        """
        Create Excel report with orphan alarm details.
        
        Args:
            service_config: Service dimension configuration
            orphan_alarms: Dictionary of orphan alarms by service
            output_path: Path for output Excel file
        """
        logger.info("Generating Excel report: %s", output_path)
        
        workbook = xlsxwriter.Workbook(output_path)
        cell_format = workbook.add_format({'text_wrap': True})
        bold_format = workbook.add_format({'bold': True})
        
        for service, alarms in orphan_alarms.items():
            if not alarms:
                continue
            
            ReportGenerator._create_service_worksheet(
                workbook, service, alarms, 
                service_config[service]['Dimension'],
                cell_format, bold_format
            )
        
        workbook.close()
        logger.info("Excel report generated successfully")
    
    @staticmethod
    def _create_service_worksheet(
        workbook: xlsxwriter.Workbook,
        service_name: str,
        alarms: List[Dict[str, Any]],
        dimensions: List[str],
        cell_format: Any,
        bold_format: Any
    ) -> None:
        """Create worksheet for a specific service."""
        worksheet = workbook.add_worksheet(service_name)
        worksheet.set_row(0, 25)
        
        # Write headers
        headers = ["AlarmName", "Namespace"] + dimensions
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, bold_format)
            worksheet.set_column(col, col, 50 if col > 1 else 70, cell_format)
        
        # Write alarm data
        for row, alarm in enumerate(alarms, start=1):
            alarm_dims = {d['Name']: d['Value'] for d in alarm['Dimensions']}
            
            worksheet.write(row, 0, alarm["AlarmName"])
            worksheet.write(row, 1, alarm["Namespace"])
            
            for col, dim in enumerate(dimensions, start=2):
                worksheet.write(row, col, alarm_dims.get(dim, ""))


def load_configuration(config_path: str) -> Dict[str, Any]:
    """Load YAML configuration file."""
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except Exception as e:
        logger.error("Error loading configuration from %s: %s", config_path, e)
        raise


def load_service_config(config_path: str) -> Dict[str, Any]:
    """Load JSON service configuration file."""
    try:
        with open(config_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        logger.error("Error loading service config from %s: %s", config_path, e)
        raise


def save_json_output(data: Dict[str, Any], output_path: str) -> None:
    """Save results to JSON file."""
    try:
        with open(output_path, 'w') as file:
            json.dump(data, indent=4, fp=file)
        logger.info("Results saved to %s", output_path)
    except Exception as e:
        logger.error("Error saving JSON output: %s", e)


def main() -> None:
    """Main execution function."""
    try:
        logger.info("=" * 60)
        logger.info("CloudWatch Orphan Alarm Detector - Starting")
        logger.info("=" * 60)
        
        # Load configurations
        config = load_configuration(CONFIG_FILE)
        service_config = load_service_config(SERVICE_CONFIG_FILE)
        
        # Create AWS session
        session = AWSSession.get_aws_session(config)
        region = config["region_name"]
        
        # Discover resources
        discovery = ResourceDiscovery(session, region)
        resources = discovery.discover_all_resources()
        
        # Detect orphan alarms
        detector = OrphanAlarmDetector(discovery.clients['cloudwatch'])
        all_alarms = detector.get_all_alarms()
        orphan_alarms = detector.find_orphan_alarms(
            service_config, all_alarms, resources
        )
        
        # Log summary
        total_orphans = sum(len(alarms) for alarms in orphan_alarms.values())
        logger.info("=" * 60)
        logger.info("Detection Summary:")
        logger.info("Total orphan alarms found: %d", total_orphans)
        for service, alarms in orphan_alarms.items():
            logger.info("  - %s: %d orphan alarms", service, len(alarms))
        logger.info("=" * 60)
        
        if not orphan_alarms:
            logger.info("No orphan alarms detected. Exiting.")
            return
        
        # Save results
        save_json_output(orphan_alarms, OUTPUT_FILE)
        ReportGenerator.create_excel_report(service_config, orphan_alarms)
        
        # Delete orphan alarms if enabled
        if config.get("delete", False):
            logger.warning("Deletion mode enabled - removing orphan alarms")
            detector.delete_orphan_alarms(orphan_alarms)
        else:
            logger.info("Deletion mode disabled - orphan alarms preserved")
        
        # Send email notification if enabled
        if config.get("Email", {}).get("enabled", False):
            logger.info("Sending email notification")
            notifier = EmailNotifier(CONFIG_FILE)
            notifier.send_email(
                subject="AWS Orphan Alarms Report",
                body=f"<p>Orphan alarm detection completed.</p>"
                     f"<p>Total orphan alarms found: <strong>{total_orphans}</strong></p>"
                     f"<p>Please review the attached Excel report for details.</p>",
                attachment_path=REPORT_FILE
            )
        
        logger.info("=" * 60)
        logger.info("CloudWatch Orphan Alarm Detector - Completed Successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("Fatal error in main execution: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
