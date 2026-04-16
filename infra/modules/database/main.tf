variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "db_admin_password" {
  type      = string
  sensitive = true
}

variable "developer_ip" {
  type        = string
  description = "Developer's public IP address — added to PostgreSQL firewall rules."
}

# ---------------------------------------------------------------------------
# Azure PostgreSQL Flexible Server — PostgreSQL 16, Burstable B1ms
# ---------------------------------------------------------------------------
resource "azurerm_postgresql_flexible_server" "this" {
  name                = "psql-sightline-dev"
  resource_group_name = var.resource_group_name
  location            = var.location

  version    = "16"
  sku_name   = "B_Standard_B1ms"

  administrator_login    = "sightline_admin"
  administrator_password = var.db_admin_password

  storage_mb            = 32768   # 32 GB
  backup_retention_days = 7
  zone                  = "1"

  # Zone redundancy disabled — dev tier, single AZ (omit block entirely)
}

# ---------------------------------------------------------------------------
# Enable PostGIS extension via server configuration
# azure.extensions must be set before CREATE EXTENSION runs in migrations.
# ---------------------------------------------------------------------------
resource "azurerm_postgresql_flexible_server_configuration" "postgis" {
  name      = "azure.extensions"
  server_id = azurerm_postgresql_flexible_server.this.id
  value     = "POSTGIS"
}

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
resource "azurerm_postgresql_flexible_server_database" "sightline" {
  name      = "sightline"
  server_id = azurerm_postgresql_flexible_server.this.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# ---------------------------------------------------------------------------
# Firewall rules
# ---------------------------------------------------------------------------

# Allow Azure services (0.0.0.0/0.0.0.0 is the Azure services sentinel range)
resource "azurerm_postgresql_flexible_server_firewall_rule" "azure_services" {
  name             = "allow-azure-services"
  server_id        = azurerm_postgresql_flexible_server.this.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# Allow developer IP for direct access (migrations, psql, pgAdmin)
resource "azurerm_postgresql_flexible_server_firewall_rule" "developer" {
  name             = "allow-developer"
  server_id        = azurerm_postgresql_flexible_server.this.id
  start_ip_address = var.developer_ip
  end_ip_address   = var.developer_ip
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------
output "fqdn" {
  value = azurerm_postgresql_flexible_server.this.fqdn
}

output "server_name" {
  value = azurerm_postgresql_flexible_server.this.name
}

output "database_name" {
  value = azurerm_postgresql_flexible_server_database.sightline.name
}
