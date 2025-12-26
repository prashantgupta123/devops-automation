output "lambda_arn" {
  value = aws_lambda_function.lambda_function_service.arn
}

output "function_name" {
  value = aws_lambda_function.lambda_function_service.function_name
}

output "cw_event_rule_service_arn" {
  value = aws_cloudwatch_event_rule.event_rule_service.arn
}

output "cw_event_rule_service_id" {
  value = aws_cloudwatch_event_rule.event_rule_service.id
}