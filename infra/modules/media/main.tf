# ---------------------------------------------------------------------------
# Media Storage Account — stsightlinemedia
# allow_nested_items_to_be_public enables container-level public access (CDN).
# ---------------------------------------------------------------------------
resource "azurerm_storage_account" "media" {
  name                            = "stsightlinemedia"
  resource_group_name             = var.resource_group_name
  location                        = var.location
  account_tier                    = "Standard"
  account_replication_type        = "LRS"
  account_kind                    = "StorageV2"
  allow_nested_items_to_be_public = true

  blob_properties {
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["PUT", "GET", "HEAD", "OPTIONS"]
      allowed_origins    = ["http://localhost:3000", "https://*.azurestaticapps.net"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 3600
    }
  }
}

resource "azurerm_storage_container" "media_raw" {
  name                  = "media-raw"
  storage_account_name  = azurerm_storage_account.media.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "media_processed" {
  name                  = "media-processed"
  storage_account_name  = azurerm_storage_account.media.name
  container_access_type = "blob"
}

resource "azurerm_storage_container" "media_private" {
  name                  = "media-private"
  storage_account_name  = azurerm_storage_account.media.name
  container_access_type = "private"
}

# ---------------------------------------------------------------------------
# Front Door Profile (replaces deprecated classic CDN profile)
# ---------------------------------------------------------------------------
resource "azurerm_cdn_frontdoor_profile" "this" {
  name                = "cdn-sightline-dev"
  resource_group_name = var.resource_group_name
  sku_name            = "Standard_AzureFrontDoor"
}

# ---------------------------------------------------------------------------
# Front Door Endpoint
# Origin group, origin, and route resources are required to wire this endpoint
# to stsightlinemedia — add them in a follow-up before enabling traffic.
# ---------------------------------------------------------------------------
resource "azurerm_cdn_frontdoor_endpoint" "this" {
  name                     = "cdnep-sightline-media"
  cdn_frontdoor_profile_id = azurerm_cdn_frontdoor_profile.this.id
}

# ---------------------------------------------------------------------------
# Function App Storage Account — stsightlinefunc (separate from media)
# ---------------------------------------------------------------------------
resource "azurerm_storage_account" "func" {
  name                     = "stsightlinefunc"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
}

# ---------------------------------------------------------------------------
# Log Analytics Workspace — backing store for Application Insights
# Classic App Insights is deprecated; workspace-based is the current standard.
# ---------------------------------------------------------------------------
resource "azurerm_log_analytics_workspace" "func" {
  name                = "law-sightline-func"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

# ---------------------------------------------------------------------------
# Application Insights
# ---------------------------------------------------------------------------
resource "azurerm_application_insights" "this" {
  name                = "appi-sightline-dev"
  resource_group_name = var.resource_group_name
  location            = var.location
  workspace_id        = azurerm_log_analytics_workspace.func.id
  application_type    = "web"
  retention_in_days   = 30
}

# ---------------------------------------------------------------------------
# Service Plan — Linux Consumption (Y1)
# ---------------------------------------------------------------------------
resource "azurerm_service_plan" "this" {
  name                = "asp-sightline-func"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "Y1"
}

# ---------------------------------------------------------------------------
# Function App — Python 3.11
# NOTE: AzureWebJobsStorage is also wired via storage_account_name +
# storage_account_access_key at the resource level. If the provider raises a
# conflict during plan, remove "AzureWebJobsStorage" from app_settings —
# the resource-level attributes already set it in the Functions runtime.
# ---------------------------------------------------------------------------
resource "azurerm_linux_function_app" "this" {
  name                       = "func-sightline-media"
  resource_group_name        = var.resource_group_name
  location                   = var.location
  service_plan_id            = azurerm_service_plan.this.id
  storage_account_name       = azurerm_storage_account.func.name
  storage_account_access_key = azurerm_storage_account.func.primary_access_key

  site_config {
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "AzureWebJobsStorage"            = azurerm_storage_account.func.primary_connection_string
    "APPINSIGHTS_INSTRUMENTATIONKEY" = azurerm_application_insights.this.instrumentation_key
    "MEDIA_STORAGE_CONNECTION"       = azurerm_storage_account.media.primary_connection_string
    "MEDIA_CONTAINER_RAW"            = "media-raw"
    "MEDIA_CONTAINER_PROCESSED"      = "media-processed"
    "DATABASE_URL"                   = var.database_url
    "CDN_ENDPOINT"                   = azurerm_cdn_frontdoor_endpoint.this.host_name
  }
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "media_storage_account_name" {
  value = azurerm_storage_account.media.name
}

output "media_storage_connection_string" {
  value     = azurerm_storage_account.media.primary_connection_string
  sensitive = true
}

output "cdn_endpoint_hostname" {
  value = azurerm_cdn_frontdoor_endpoint.this.host_name
}

output "function_app_name" {
  value = azurerm_linux_function_app.this.name
}

output "function_app_default_hostname" {
  value = azurerm_linux_function_app.this.default_hostname
}
