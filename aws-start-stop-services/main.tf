data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda_function.py"
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_sns_topic" "lambda_notifications" {
  name = "${local.service_name_prefix}-${local.workspace["lambda"]["name"]}"
  display_name = local.workspace["sns"]["display_name"]
  tags = merge(
    local.common_tags,
    {
      "Name" = "${local.service_name_prefix}-${local.workspace["lambda"]["name"]}"
    }
  )
}

resource "aws_security_group" "lambda_sg" {
  name        = "${local.service_name_prefix}-${local.workspace["lambda"]["name"]}"
  description = "Security Group for Lambda"
  vpc_id      = data.aws_vpc.selected.id
  tags = merge(
    local.common_tags,
    {
      "Name" = "${local.service_name_prefix}-${local.workspace["lambda"]["name"]}"
    }
  )

  dynamic "egress" {
    for_each = local.workspace["security_group"]["outbound"]
    iterator = each
    content {
      description     = each.value["description"]
      from_port       = each.value["from_port"]
      to_port         = each.value["to_port"]
      protocol        = each.value["protocol"]
      cidr_blocks     = contains(keys(each.value), "cidr_blocks") ? each.value["cidr_blocks"] : []
      security_groups = contains(keys(each.value), "security_groups") ? each.value["security_groups"] : []
      prefix_list_ids = contains(keys(each.value), "prefix_list_ids") ? each.value["prefix_list_ids"] : []
    }
  }
  dynamic "ingress" {
    for_each = local.workspace["security_group"]["inbound"]
    iterator = each
    content {
      description     = each.value["description"]
      from_port       = each.value["from_port"]
      to_port         = each.value["to_port"]
      protocol        = each.value["protocol"]
      cidr_blocks     = contains(keys(each.value), "cidr_blocks") ? each.value["cidr_blocks"] : []
      security_groups = contains(keys(each.value), "security_groups") ? each.value["security_groups"] : []
      prefix_list_ids = contains(keys(each.value), "prefix_list_ids") ? each.value["prefix_list_ids"] : []
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "${local.service_name_prefix}-${local.workspace["lambda"]["name"]}"
  assume_role_policy = local.workspace["role"]["assume_role_policy"]
  tags = merge(
    local.common_tags,
    {
      "Name" = "${local.service_name_prefix}-${local.workspace["lambda"]["name"]}"
    }
  )
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${local.service_name_prefix}-${local.workspace["lambda"]["name"]}"
  role = aws_iam_role.lambda_role.id
  policy = local.workspace["role"]["policy"]
}

resource "aws_lambda_function" "lambda_function" {
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  role            = aws_iam_role.lambda_role.arn
  function_name    = "${local.service_name_prefix}-${local.workspace["lambda"]["name"]}"
  description = local.workspace["lambda"]["description"]
  handler         = local.workspace["lambda"]["handler"]
  runtime         = local.workspace["lambda"]["runtime"]
  timeout         = local.workspace["lambda"]["timeout"]
  memory_size     = local.workspace["lambda"]["memory_size"]
  tags            = merge(
    local.common_tags,
    {
      "Name" = "${local.service_name_prefix}-${local.workspace["lambda"]["name"]}"
    }
  )
  environment {
    variables = merge(
      local.workspace["lambda"]["environment_variables"],
      {
        "ACCOUNT_ID"     = local.account_id
        "AWS_REGION_NAME"      = local.region
        "SNS_TOPIC_ARN" = aws_sns_topic.lambda_notifications.arn
        "SNS_SUBJECT_PREFIX" = local.workspace["sns"]["subject_prefix"]
      }
    )
  }
  vpc_config {
    subnet_ids = data.aws_subnets.private.ids
    security_group_ids = [aws_security_group.lambda_sg.id]
  }
}

resource "aws_cloudwatch_log_group" "cloudwatch_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.lambda_function.function_name}"
  retention_in_days = local.workspace["lambda"]["log_retention_in_days"]
  tags = merge(
    local.common_tags,
    {
      "Name" = "${local.service_name_prefix}-${local.workspace["lambda"]["name"]}"
    }
  )
}

resource "aws_lambda_function_event_invoke_config" "event_invoke_config" {
  function_name = aws_lambda_function.lambda_function.function_name
  maximum_retry_attempts = local.workspace["lambda"]["event_invoke_config"]["maximum_retry_attempts"]
  maximum_event_age_in_seconds = local.workspace["lambda"]["event_invoke_config"]["maximum_event_age_in_seconds"]
}

resource "aws_cloudwatch_event_rule" "scheduled_events" {
  for_each            = local.workspace["event"]
  name                = "${local.service_name_prefix}-${each.key}"
  description         = each.value.description
  schedule_expression = each.value.schedule_expression
  tags                = merge(
    local.common_tags,
    {
      "Name" = "${local.service_name_prefix}-${each.key}"
    }
  )
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  for_each = local.workspace["event"]
  rule     = aws_cloudwatch_event_rule.scheduled_events[each.key].name
  arn      = aws_lambda_function.lambda_function.arn
  input    = jsonencode(each.value.event_input)
}

resource "aws_lambda_permission" "allow_eventbridge" {
  for_each      = local.workspace["event"]
  statement_id  = "AllowExecutionFromEventBridge-${each.key}"
  action        = local.workspace["lambda"]["action"]
  function_name = aws_lambda_function.lambda_function.function_name
  principal     = local.workspace["lambda"]["principal"]
  source_arn    = aws_cloudwatch_event_rule.scheduled_events[each.key].arn
}

resource "aws_cloudwatch_metric_alarm" "lambda_error_alarm" {
  for_each = merge([
    for key, alarm in local.workspace["cloudwatch"] : {
      for function_name in alarm.function_name :
      "${function_name}-${key}" => merge(alarm, { function_name = function_name, alarm_key = key })
    }
  ]...)

  alarm_name          = "${local.service_name_prefix}-${each.value.function_name}-${each.value.metric_name}"
  comparison_operator = each.value.comparison_operator
  evaluation_periods  = each.value.evaluation_periods
  metric_name         = each.value.metric_name
  namespace           = each.value.namespace
  period              = each.value.period
  statistic           = each.value.statistic
  threshold           = each.value.threshold

  dimensions = {
    FunctionName = "${local.service_name_prefix}-${each.value.function_name}"
  }

  alarm_description = lookup(each.value, "alarm_description", "No description provided")
  alarm_actions     = [lookup(data.terraform_remote_state.sns.outputs.sns_arn, "infra-alert", "undefined")]

  tags = merge(local.common_tags, {
    "Name" = "${local.service_name_prefix}-${each.value.function_name}-${each.value.metric_name}"
  })
}
