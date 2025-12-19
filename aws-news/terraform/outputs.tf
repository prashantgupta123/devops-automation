output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.aws_news_notifier.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.aws_news_notifier.arn
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.lambda_logs.name
}

output "eventbridge_rule_name" {
  description = "EventBridge rule name"
  value       = aws_cloudwatch_event_rule.daily_trigger.name
}

output "schedule_expression" {
  description = "Schedule expression for the EventBridge rule"
  value       = aws_cloudwatch_event_rule.daily_trigger.schedule_expression
}