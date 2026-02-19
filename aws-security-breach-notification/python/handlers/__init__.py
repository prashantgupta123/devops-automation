"""AWS security event handlers."""

from handlers.security_group_handler import handle_security_group_ingress, handle_security_group_egress
from handlers.ec2_handler import (
    handle_ec2_public_instance, handle_ec2_public_snapshot,
    handle_ec2_public_ami, handle_ec2_public_security_group,
)
from handlers.rds_handler import handle_rds_public_instance, handle_rds_public_snapshot
from handlers.alb_handler import handle_alb_public
from handlers.iam_handler import (
    handle_access_key_creation, handle_access_key_deletion,
    handle_console_login, handle_iam_user_create, handle_iam_user_delete,
)
from handlers.s3_handler import handle_s3_public_access
from handlers.cloudtrail_handler import handle_cloudtrail_event
from handlers.lambda_handler import handle_lambda_function_event
from handlers.vpc_handler import (
    handle_vpc_creation, handle_vpc_deletion,
    handle_subnet_creation, handle_subnet_deletion,
    handle_nat_gateway_creation, handle_nat_gateway_deletion,
    handle_route_table_creation, handle_route_table_deletion,
    handle_network_acl_creation, handle_network_acl_deletion,
    handle_elastic_ip_allocation, handle_elastic_ip_release,
    handle_vpc_peering_creation, handle_vpc_peering_deletion,
    handle_vpc_endpoint_deletion,
)
from handlers.route53_handler import handle_hosted_zone_deletion, handle_record_set_change
from handlers.secretsmanager_handler import handle_secret_deletion
from handlers.backup_handler import handle_backup_plan_deletion, handle_backup_vault_deletion
from handlers.ecr_handler import handle_repository_creation

__all__ = [
    # Security Group handlers
    'handle_security_group_ingress', 'handle_security_group_egress',
    
    # EC2 handlers
    'handle_ec2_public_instance', 'handle_ec2_public_snapshot',
    'handle_ec2_public_ami', 'handle_ec2_public_security_group',
    
    # RDS handlers
    'handle_rds_public_instance', 'handle_rds_public_snapshot',
    
    # ALB handlers
    'handle_alb_public',
    
    # IAM handlers
    'handle_access_key_creation', 'handle_access_key_deletion',
    'handle_console_login', 'handle_iam_user_create', 'handle_iam_user_delete',
    
    # S3 handlers
    'handle_s3_public_access',
    
    # CloudTrail handlers
    'handle_cloudtrail_event',
    
    # Lambda handlers
    'handle_lambda_function_event',
    
    # VPC handlers
    'handle_vpc_creation', 'handle_vpc_deletion',
    'handle_subnet_creation', 'handle_subnet_deletion',
    'handle_nat_gateway_creation', 'handle_nat_gateway_deletion',
    'handle_route_table_creation', 'handle_route_table_deletion',
    'handle_network_acl_creation', 'handle_network_acl_deletion',
    'handle_elastic_ip_allocation', 'handle_elastic_ip_release',
    'handle_vpc_peering_creation', 'handle_vpc_peering_deletion',
    'handle_vpc_endpoint_deletion',
    
    # Route53 handlers
    'handle_hosted_zone_deletion', 'handle_record_set_change',
    
    # Secrets Manager handlers
    'handle_secret_deletion',
    
    # Backup handlers
    'handle_backup_plan_deletion', 'handle_backup_vault_deletion',
    
    # ECR handlers
    'handle_repository_creation',
]
