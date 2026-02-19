"""Main Lambda handler for AWS security monitoring."""

from typing import Dict, Any, Callable, List
from core.event_types import EventDetail
from core.exceptions import HandlerError, ConfigurationError
from services.notification_service import NotificationService
from utils.logger import setup_logger

logger = setup_logger(__name__)

EVENT_HANDLERS: Dict[str, Callable[[Dict[str, Any], Any], List[EventDetail]]] = {}


def register_handler(event_name: str) -> Callable:
    """
    Decorator to register event handlers.
    
    Args:
        event_name: CloudTrail event name to handle
    
    Returns:
        Decorator function
    """
    def decorator(func: Callable[[Dict[str, Any], Any], List[EventDetail]]) -> Callable:
        EVENT_HANDLERS[event_name] = func
        logger.debug(f"Registered handler for event: {event_name}")
        return func
    return decorator


# Import handlers to trigger registration
from handlers.security_group_handler import handle_security_group_ingress, handle_security_group_egress
from handlers.ec2_handler import handle_ec2_public_instance, handle_ec2_public_snapshot, handle_ec2_public_ami, handle_ec2_public_security_group
from handlers.rds_handler import handle_rds_public_instance, handle_rds_public_snapshot
from handlers.alb_handler import handle_alb_public
from handlers.iam_handler import handle_access_key_creation, handle_access_key_deletion, handle_console_login, handle_iam_user_create, handle_iam_user_delete
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
    handle_vpc_endpoint_deletion
)
from handlers.route53_handler import handle_hosted_zone_deletion, handle_record_set_change
from handlers.secretsmanager_handler import handle_secret_deletion
from handlers.backup_handler import handle_backup_plan_deletion, handle_backup_vault_deletion
from handlers.ecr_handler import handle_repository_creation

# Import new handlers
from handlers.config_handler import (
    handle_delete_configuration_recorder, handle_stop_configuration_recorder,
    handle_delete_delivery_channel, handle_delete_config_rule,
    handle_delete_aggregation_authorization, handle_delete_configuration_aggregator,
    handle_delete_remediation_configuration, handle_put_config_rule
)
from handlers.iam_policy_handler import (
    handle_put_user_policy, handle_put_role_policy,
    handle_attach_user_policy, handle_attach_role_policy,
    handle_create_policy, handle_update_assume_role_policy
)
from handlers.iam_role_handler import (
    handle_create_role, handle_delete_role,
    handle_detach_role_policy, handle_delete_role_policy
)
from handlers.cloudwatch_handler import (
    handle_delete_log_group, handle_delete_log_stream,
    handle_delete_metric_alarm, handle_disable_alarm_actions,
    handle_delete_metric_filter, handle_delete_subscription_filter,
    handle_put_retention_policy
)
from handlers.kms_handler import (
    handle_schedule_key_deletion, handle_disable_key,
    handle_put_key_policy, handle_delete_alias, handle_cancel_key_deletion
)
from handlers.ebs_handler import (
    handle_create_volume, handle_modify_volume_attribute, handle_delete_volume
)
from handlers.network_interface_handler import (
    handle_create_network_interface, handle_associate_address,
    handle_modify_network_interface_attribute
)

# Register Security Group handlers
register_handler('AuthorizeSecurityGroupIngress')(handle_security_group_ingress)
register_handler('AuthorizeSecurityGroupEgress')(handle_security_group_egress)

# Register EC2 handlers
register_handler('RunInstances')(handle_ec2_public_instance)
register_handler('ModifySnapshotAttribute')(handle_ec2_public_snapshot)
register_handler('ModifyImageAttribute')(handle_ec2_public_ami)
register_handler('CreateSecurityGroup')(handle_ec2_public_security_group)

# Register RDS/ALB handlers
register_handler('CreateDBInstance')(handle_rds_public_instance)
register_handler('ModifyDBClusterSnapshotAttribute')(handle_rds_public_snapshot)
register_handler('ModifyDBSnapshotAttribute')(handle_rds_public_snapshot)
register_handler('CreateLoadBalancer')(handle_alb_public)

# Register IAM handlers
register_handler('CreateAccessKey')(handle_access_key_creation)
register_handler('DeleteAccessKey')(handle_access_key_deletion)
register_handler('ConsoleLogin')(handle_console_login)
register_handler('CreateUser')(handle_iam_user_create)
register_handler('DeleteUser')(handle_iam_user_delete)

# Register S3 handlers
register_handler('PutBucketPublicAccessBlock')(handle_s3_public_access)
register_handler('PutBucketAcl')(handle_s3_public_access)

# Register CloudTrail handlers
register_handler('StopLogging')(handle_cloudtrail_event)
register_handler('DeleteTrail')(handle_cloudtrail_event)

# Register Lambda handlers
# register_handler('CreateFunction20150331')(handle_lambda_function_event)
# register_handler('UpdateFunctionConfiguration20150331v2')(handle_lambda_function_event)
# register_handler('UpdateFunctionCode20150331v2')(handle_lambda_function_event)

# Register VPC handlers
register_handler('CreateVpc')(handle_vpc_creation)
register_handler('DeleteVpc')(handle_vpc_deletion)
register_handler('CreateSubnet')(handle_subnet_creation)
register_handler('DeleteSubnet')(handle_subnet_deletion)
register_handler('CreateNatGateway')(handle_nat_gateway_creation)
register_handler('DeleteNatGateway')(handle_nat_gateway_deletion)
register_handler('CreateRouteTable')(handle_route_table_creation)
register_handler('DeleteRouteTable')(handle_route_table_deletion)
register_handler('CreateNetworkAcl')(handle_network_acl_creation)
register_handler('DeleteNetworkAcl')(handle_network_acl_deletion)
register_handler('AllocateAddress')(handle_elastic_ip_allocation)
register_handler('ReleaseAddress')(handle_elastic_ip_release)
register_handler('CreateVpcPeeringConnection')(handle_vpc_peering_creation)
register_handler('DeleteVpcPeeringConnection')(handle_vpc_peering_deletion)
register_handler('DeleteVpcEndpoints')(handle_vpc_endpoint_deletion)

# Register Route53 handlers
register_handler('DeleteHostedZone')(handle_hosted_zone_deletion)
register_handler('ChangeResourceRecordSets')(handle_record_set_change)

# Register Secrets Manager handlers
register_handler('DeleteSecret')(handle_secret_deletion)

# Register Backup handlers
register_handler('DeleteBackupPlan')(handle_backup_plan_deletion)
register_handler('DeleteBackupVault')(handle_backup_vault_deletion)

# Register ECR handlers
# register_handler('CreateRepository')(handle_repository_creation)

# Register AWS Config handlers
register_handler('DeleteConfigurationRecorder')(handle_delete_configuration_recorder)
register_handler('StopConfigurationRecorder')(handle_stop_configuration_recorder)
register_handler('DeleteDeliveryChannel')(handle_delete_delivery_channel)
register_handler('DeleteConfigRule')(handle_delete_config_rule)
register_handler('DeleteAggregationAuthorization')(handle_delete_aggregation_authorization)
register_handler('DeleteConfigurationAggregator')(handle_delete_configuration_aggregator)
register_handler('DeleteRemediationConfiguration')(handle_delete_remediation_configuration)
register_handler('PutConfigRule')(handle_put_config_rule)

# Register IAM Policy handlers
register_handler('PutUserPolicy')(handle_put_user_policy)
# register_handler('PutRolePolicy')(handle_put_role_policy)
register_handler('AttachUserPolicy')(handle_attach_user_policy)
# register_handler('AttachRolePolicy')(handle_attach_role_policy)
# register_handler('CreatePolicy')(handle_create_policy)
# register_handler('UpdateAssumeRolePolicy')(handle_update_assume_role_policy)

# Register IAM Role handlers
# register_handler('CreateRole')(handle_create_role)
# register_handler('DeleteRole')(handle_delete_role)
# register_handler('DetachRolePolicy')(handle_detach_role_policy)
# register_handler('DeleteRolePolicy')(handle_delete_role_policy)

# Register CloudWatch handlers
# register_handler('DeleteLogGroup')(handle_delete_log_group)
# register_handler('DeleteLogStream')(handle_delete_log_stream)
# register_handler('DeleteAlarms')(handle_delete_metric_alarm)
# register_handler('DisableAlarmActions')(handle_disable_alarm_actions)
# register_handler('DeleteMetricFilter')(handle_delete_metric_filter)
# register_handler('DeleteSubscriptionFilter')(handle_delete_subscription_filter)
# register_handler('PutRetentionPolicy')(handle_put_retention_policy)

# Register KMS handlers
register_handler('ScheduleKeyDeletion')(handle_schedule_key_deletion)
register_handler('DisableKey')(handle_disable_key)
# register_handler('PutKeyPolicy')(handle_put_key_policy)
register_handler('DeleteAlias')(handle_delete_alias)
register_handler('CancelKeyDeletion')(handle_cancel_key_deletion)

# Register EBS handlers
# register_handler('CreateVolume')(handle_create_volume)
# register_handler('ModifyVolumeAttribute')(handle_modify_volume_attribute)
# register_handler('DeleteVolume')(handle_delete_volume)

# Register Network Interface handlers
# register_handler('CreateNetworkInterface')(handle_create_network_interface)
# register_handler('AssociateAddress')(handle_associate_address)
# register_handler('ModifyNetworkInterfaceAttribute')(handle_modify_network_interface_attribute)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda entry point for AWS security monitoring.
    
    Args:
        event: CloudTrail event from EventBridge
        context: Lambda context object
    
    Returns:
        Response dictionary with statusCode and body
    """
    try:
        event_name = event['detail']['eventName']
        logger.info(f"Processing event: {event_name}", extra={
            'event_name': event_name,
            'event_id': event.get('id'),
            'region': event['detail'].get('awsRegion')
        })
        
        handler = EVENT_HANDLERS.get(event_name)
        if not handler:
            logger.warning(f"No handler registered for event: {event_name}")
            return {'statusCode': 200, 'body': 'No handler'}
        
        event_details = handler(event, context)
        if not event_details:
            logger.info("No violations detected")
            return {'statusCode': 200, 'body': 'No violations'}
        
        logger.info(f"Found {len(event_details)} violation(s)")
        notification = NotificationService(event, event_details)
        success = notification.send_email()
        
        if success:
            logger.info("Notification sent successfully")
            return {'statusCode': 200, 'body': 'Notification sent'}
        else:
            logger.error("Notification failed to send")
            return {'statusCode': 500, 'body': 'Notification failed'}
    
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}", exc_info=True)
        return {'statusCode': 500, 'body': f'Configuration error: {str(e)}'}
    
    except HandlerError as e:
        logger.error(f"Handler error: {e}", exc_info=True)
        return {'statusCode': 500, 'body': f'Handler error: {str(e)}'}
    
    except KeyError as e:
        logger.error(f"Missing required field in event: {e}", exc_info=True)
        return {'statusCode': 400, 'body': f'Invalid event structure: {str(e)}'}
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        try:
            arn = context.invoked_function_arn
            logger.error(f"Function ARN: {arn}")
        except:
            pass
        return {'statusCode': 500, 'body': f'Error: {str(e)}'}


# Alias for backward compatibility
main = lambda_handler
