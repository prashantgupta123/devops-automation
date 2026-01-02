terraform {
  backend "s3" {
    bucket  = "test-infra-terraform"
    key     = "project/app/lambda/start-stop-services/main.tfstate"
    region  = "ap-south-1"
    encrypt = true
  }
}

data "terraform_remote_state" "sns" {
  backend = "s3"
  workspace = "${local.workspace_common["environment"]}_${local.workspace_common["region"]}"
  config = {
    bucket  = "test-infra-terraform"
    key     = "project/shared/sns/main.tfstate"
    region  = "ap-south-1"
    encrypt = true
  }
}
