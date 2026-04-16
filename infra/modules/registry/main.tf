variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

# ---------------------------------------------------------------------------
# Azure Container Registry
# Name must be globally unique, lowercase alphanumeric, no hyphens.
# ---------------------------------------------------------------------------
resource "azurerm_container_registry" "this" {
  name                = "acrsightline"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "Basic"
  admin_enabled       = true
}

output "login_server" {
  value = azurerm_container_registry.this.login_server
}

output "admin_username" {
  value     = azurerm_container_registry.this.admin_username
  sensitive = true
}

output "admin_password" {
  value     = azurerm_container_registry.this.admin_password
  sensitive = true
}
