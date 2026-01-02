locals {
  config           = yamldecode(file("${path.module}/workspace.yml"))
  common           = local.config["common"]
  env_space        = yamldecode(file("${path.module}/workspace_${terraform.workspace}.yml"))
  workspace        = local.env_space["workspace"]
  workspace_common = local.workspace["common"]
  workspace_aws    = local.workspace["aws"]

  service_name_prefix = "${local.workspace["name"]}-${local.common["project_name_prefix"]}"
  account_name_prefix = "${local.workspace_common["environment"]}-${local.common["project_name_prefix"]}"
  common_tags = merge(
    local.common["tags"],
    local.workspace_common["tags"],
    tomap({
      "Environment" = local.workspace_common["environment"]
      "Workspace"   = terraform.workspace
    })
  )

  account_id = local.workspace_aws["account_id"]
  region     = local.workspace_aws["region"]

  role_enable = local.workspace["aws"]["role"] == "" ? [] : [
    "arn:aws:iam::${local.workspace["aws"]["account_id"]}:role/${local.workspace["aws"]["role"]}"
  ]
  profile_enable = local.workspace_aws["profile"] == "" ? null : local.workspace_aws["profile"]
}

provider "aws" {
  region  = local.workspace_aws["region"]
  profile = local.profile_enable
  dynamic "assume_role" {
    for_each = local.role_enable
    content {
      role_arn = assume_role.value
    }
  }
}

data "aws_caller_identity" "current" {}
