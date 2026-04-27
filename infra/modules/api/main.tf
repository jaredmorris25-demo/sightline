variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "api_image" {
  type        = string
  description = "Full ACR image reference, e.g. acrsightline.azurecr.io/sightline-api:latest"
}

variable "acr_login_server" {
  type = string
}

variable "acr_username" {
  type      = string
  sensitive = true
}

variable "acr_password" {
  type      = string
  sensitive = true
}

variable "database_url" {
  type      = string
  sensitive = true
  description = "Full asyncpg DATABASE_URL for the FastAPI app."
}

variable "auth0_domain" {
  type = string
}

variable "auth0_api_audience" {
  type = string
}

variable "environment" {
  type    = string
  default = "dev"
}

# ---------------------------------------------------------------------------
# Log Analytics Workspace — required by Container Apps Environment
# ---------------------------------------------------------------------------
resource "azurerm_log_analytics_workspace" "this" {
  name                = "law-sightline-dev"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# ---------------------------------------------------------------------------
# Container Apps Environment
# ---------------------------------------------------------------------------
resource "azurerm_container_app_environment" "this" {
  name                       = "cae-sightline-dev"
  resource_group_name        = var.resource_group_name
  location                   = var.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id
}

# ---------------------------------------------------------------------------
# Container App — FastAPI
# ---------------------------------------------------------------------------
resource "azurerm_container_app" "api" {
  name                         = "ca-sightline-api"
  resource_group_name          = var.resource_group_name
  container_app_environment_id = azurerm_container_app_environment.this.id
  revision_mode                = "Single"

  registry {
    server               = var.acr_login_server
    username             = var.acr_username
    password_secret_name = "acr-password"
  }

  secret {
    name  = "acr-password"
    value = var.acr_password
  }

  secret {
    name  = "database-url"
    value = var.database_url
  }

  secret {
    name  = "azure-search-api-key"
    value = var.azure_search_api_key
  }

  template {
    min_replicas = 1
    max_replicas = 3

    container {
      name   = "sightline-api"
      image  = var.api_image
      cpu    = 0.5
      memory = "1Gi"

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
      env {
        name        = "DATABASE_URL"
        secret_name = "database-url"
      }
      env {
        name  = "AUTH0_DOMAIN"
        value = var.auth0_domain
      }
      env {
        name  = "AUTH0_API_AUDIENCE"
        value = var.auth0_api_audience
      }
      env {
        name  = "PYTHONPATH"
        value = "/app"
      }
      env {
        name  = "AZURE_SEARCH_ENDPOINT"
        value = var.azure_search_endpoint
      }
      env {
        name        = "AZURE_SEARCH_API_KEY"
        secret_name = "azure-search-api-key"
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8000

    traffic_weight {
      percentage      = 100
      latest_revision = true
    }
  }
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "fqdn" {
  value = azurerm_container_app.api.latest_revision_fqdn
}
