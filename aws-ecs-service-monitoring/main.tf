resource "aws_sns_topic" "sns_topic" {
  display_name = "${local.common["project"]} | ${local.workspace["sns"]["display_name"]}"
  name         = "${local.service_name_prefix}-${local.workspace["sns"]["names"]}"
  tags = merge(local.common_tags, {
    "Name" : "${local.service_name_prefix}-${local.workspace["sns"]["names"]}"
  })
}

data "template_file" "policy_sns_temp" {
  template = file("${path.module}/lambdaPolicy.tpl")
  vars = {
    topic_arn  = aws_sns_topic.sns_topic.arn
    region     = local.workspace["aws"]["region"]
    account_id = local.workspace["aws"]["account_id"]
  }
}

resource "aws_iam_role" "aws_ecs_role" {
  name        = "${local.service_name_prefix}-${local.workspace["lambda"]["app_name"]}"
  description = "lambda ecs service role access"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": "AllowLambdaToAssumeRole"
    }
  ]
}
EOF

  tags = merge(local.common_tags, {
    "Name" = "${local.service_name_prefix}-${local.workspace["lambda"]["app_name"]}"
  })
}

resource "aws_iam_policy" "policy_sns" {
  name        = "${local.service_name_prefix}-${local.workspace["lambda"]["app_name"]}"
  description = "A policy to publish sns topic"
  policy      = data.template_file.policy_sns_temp.rendered
}

resource "aws_iam_role_policy_attachment" "sns_publish_attach" {
  role       = aws_iam_role.aws_ecs_role.name
  policy_arn = aws_iam_policy.policy_sns.arn
}

data "archive_file" "archive_function_obj" {
  type        = "zip"
  source_dir  = "${path.module}/function"
  output_path = "${path.module}/lambda-function.zip"
}

data "template_file" "template-pattern" {
  template = jsonencode({
    source = ["aws.ecs"]
    resources = flatten([for cluster, services in local.workspace["lambda"]["cluster"] : [
      for service in services : "arn:aws:ecs:${local.workspace["aws"]["region"]}:${local.workspace["aws"]["account_id"]}:service/${cluster}/${cluster}-${service}"
    ]])
    "detail-type" = [
      "ECS Service Action",
      "ECS Deployment State Change",
    ]
  })
}

resource "aws_lambda_function" "lambda_function_service" {
  filename         = "lambda-function.zip"
  source_code_hash = data.archive_file.archive_function_obj.output_base64sha256
  function_name    = "${local.service_name_prefix}-${local.workspace["lambda"]["app_name"]}"
  role             = aws_iam_role.aws_ecs_role.arn
  handler          = local.workspace["lambda"]["handler"]
  runtime          = local.workspace["lambda"]["runtime"]
  timeout          = local.workspace["lambda"]["timeout"]
  memory_size      = local.workspace["lambda"]["memory_size"]
  description      = "Sending notification when ecs service container is down."
  environment {
    variables = {
      ALERT_TOPIC_ARN = aws_sns_topic.sns_topic.arn
      ENV             = terraform.workspace
      REGION          = local.workspace["aws"]["region"]
      PROJECT_NAME    = local.common["project"]
    }
  }
  tags = merge(local.common_tags, {
    "Name" = "${local.service_name_prefix}-${local.workspace["lambda"]["app_name"]}"
  })
}

resource "aws_cloudwatch_log_group" "global_cloudwatch_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.lambda_function_service.function_name}"
  retention_in_days = local.workspace["lambda"]["retention_in_days"]
  tags = merge(local.common_tags, {
    "Name" = "${local.service_name_prefix}-${local.workspace["lambda"]["app_name"]}"
  })
}

resource "aws_lambda_function_event_invoke_config" "lambda_function_event_invoke_config" {
  function_name                = aws_lambda_function.lambda_function_service.function_name
  maximum_event_age_in_seconds = local.workspace["lambda"]["maximum_event_age_in_seconds"]
  maximum_retry_attempts       = local.workspace["lambda"]["maximum_retry_attempts"]
}

resource "aws_cloudwatch_event_rule" "event_rule_service" {
  name          = "${local.service_name_prefix}-${local.workspace["lambda"]["app_name"]}"
  description   = "Running lambda for ecs event"
  event_pattern = data.template_file.template-pattern.rendered
  state         = local.workspace["lambda"]["state"]
  tags = merge(local.common_tags, {
    "Name" = "${local.service_name_prefix}-${local.workspace["lambda"]["app_name"]}"
  })
}

resource "aws_cloudwatch_event_target" "lambda_function_event_service" {
  rule      = aws_cloudwatch_event_rule.event_rule_service.name
  target_id = "LambdaFunction"
  arn       = aws_lambda_function.lambda_function_service.arn
}

resource "aws_lambda_permission" "allow_cloudwatch_event_service" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = local.workspace["lambda"]["action"]
  function_name = aws_lambda_function.lambda_function_service.function_name
  principal     = local.workspace["lambda"]["principal"]
  source_arn    = aws_cloudwatch_event_rule.event_rule_service.arn
}
