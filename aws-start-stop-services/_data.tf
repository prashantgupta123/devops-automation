data "aws_vpc" "selected" {
  filter {
    name   = "vpc-id"
    values = [local.workspace_aws["vpc"]["id"]]
  }
  filter {
    name   = "tag:Name"
    values = [local.workspace_aws["vpc"]["name"]]
  }
}

# Subnets private
data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.selected.id]
  }
  filter {
    name   = "subnet-id"
    values = local.workspace_aws["vpc"]["subnet_ids"]["private"]
  }
  filter {
    name   = "tag:Name"
    values = local.workspace_aws["vpc"]["subnet"]["private"]
  }
}

data "aws_subnet" "private" {
  for_each = toset(data.aws_subnets.private.ids)
  id       = each.value
}

data "aws_ec2_managed_prefix_list" "s3_prefix" {
  name = "com.amazonaws.${local.workspace_aws["region"]}.s3"
}
