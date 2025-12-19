variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
  default     = "aws-news-notifier"
}

variable "webhook_url" {
  description = "Google Chat webhook URL"
  type        = string
  sensitive   = true
}

variable "schedule_expression" {
  description = "EventBridge schedule expression for daily execution"
  type        = string
  default     = "cron(0 9 * * ? *)"
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 14
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "aws-news-notifier"
    Environment = "production"
    ManagedBy   = "terraform"
  }
}