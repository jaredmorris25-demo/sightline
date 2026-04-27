variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

# ---------------------------------------------------------------------------
# Azure AI Search — free tier (1 index, 50MB, no SLA)
# Name must be globally unique, 2-60 chars, lowercase alphanumeric + hyphens.
# Free SKU does not support private endpoints or managed identity.
# ---------------------------------------------------------------------------
resource "azurerm_search_service" "this" {
  name                = "search-sightline-dev"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "free"
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "endpoint" {
  value       = "https://${azurerm_search_service.this.name}.search.windows.net"
  description = "Azure AI Search service endpoint."
}

output "primary_key" {
  value       = azurerm_search_service.this.primary_key
  sensitive   = true
  description = "Admin API key for the search service."
}
