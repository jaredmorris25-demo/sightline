# Sightline — Terraform root module
# Placeholder. Infrastructure defined in Phase 1 (IaC scaffolding).

terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  # Remote state backend — configured per environment
  # backend "azurerm" {}
}

provider "azurerm" {
  features {}
}
