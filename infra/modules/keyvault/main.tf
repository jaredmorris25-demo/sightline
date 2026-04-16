variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

data "azurerm_client_config" "current" {}

# ---------------------------------------------------------------------------
# Azure Key Vault — standard SKU, 7 day soft delete
# Name must be globally unique, 3-24 chars, alphanumeric + hyphens.
# ---------------------------------------------------------------------------
resource "azurerm_key_vault" "this" {
  name                = "kv-sightline-dev"
  resource_group_name = var.resource_group_name
  location            = var.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  soft_delete_retention_days = 7
  purge_protection_enabled   = false  # dev — allow purge without waiting

  # Grant the deploying principal full access so secrets can be set via CI/CD
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Purge", "Recover",
    ]
  }
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "vault_uri" {
  value = azurerm_key_vault.this.vault_uri
}

output "vault_id" {
  value = azurerm_key_vault.this.id
}
