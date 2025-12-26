terraform {
  required_version = ">= 1.14.3"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.27.0"
    }
    template = {
      source  = "hashicorp/template"
      version = ">= 2.2.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">= 2.7.1"
    }
  }
}
