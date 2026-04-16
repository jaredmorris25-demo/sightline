variable "resource_group_name" {
  type    = string
  default = "rg-sightline"
}

variable "location" {
  type    = string
  default = "australiaeast"
}

variable "db_admin_password" {
  type      = string
  sensitive = true
}

variable "developer_ip" {
  type        = string
  description = "Developer's public IP address for PostgreSQL firewall rule."
}

variable "api_image" {
  type        = string
  description = "Full ACR image reference, e.g. acrsightline.azurecr.io/sightline-api:latest"
}

variable "auth0_domain" {
  type = string
}

variable "auth0_api_audience" {
  type = string
}
