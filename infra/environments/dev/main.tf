terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
  backend "azurerm" {
    resource_group_name  = "rg-sightline"
    storage_account_name = "stsightlinetfstate"
    container_name       = "tfstate"
    key                  = "dev.terraform.tfstate"
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

# ---------------------------------------------------------------------------
# Azure Container Registry
# ---------------------------------------------------------------------------
module "registry" {
  source = "../../modules/registry"

  resource_group_name = var.resource_group_name
  location            = var.location
}

# ---------------------------------------------------------------------------
# PostgreSQL Flexible Server + PostGIS
# ---------------------------------------------------------------------------
module "database" {
  source = "../../modules/database"

  resource_group_name = var.resource_group_name
  location            = var.location
  db_admin_password   = var.db_admin_password
  developer_ip        = var.developer_ip
}

# ---------------------------------------------------------------------------
# Key Vault
# ---------------------------------------------------------------------------
module "keyvault" {
  source = "../../modules/keyvault"

  resource_group_name = var.resource_group_name
  location            = var.location
}

# ---------------------------------------------------------------------------
# Container App (API)
# DATABASE_URL assembled from database module outputs + password variable
# ---------------------------------------------------------------------------
locals {
  database_url = "postgresql+asyncpg://sightline_admin:${var.db_admin_password}@${module.database.fqdn}:5432/${module.database.database_name}?ssl=require"
}

module "api" {
  source = "../../modules/api"

  resource_group_name = var.resource_group_name
  location            = var.location
  api_image           = var.api_image
  acr_login_server    = module.registry.login_server
  acr_username        = module.registry.admin_username
  acr_password        = module.registry.admin_password
  database_url        = local.database_url
  auth0_domain        = var.auth0_domain
  auth0_api_audience  = var.auth0_api_audience
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "acr_login_server" {
  value = module.registry.login_server
}

output "api_url" {
  value       = "https://${module.api.fqdn}"
  description = "Public URL of the Sightline API on Azure Container Apps."
}

output "db_fqdn" {
  value = module.database.fqdn
}

output "keyvault_uri" {
  value = module.keyvault.vault_uri
}
