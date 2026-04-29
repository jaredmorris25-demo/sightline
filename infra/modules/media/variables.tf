variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "database_url" {
  type        = string
  sensitive   = true
  description = "Full DATABASE_URL passed as an app setting to the Function App."
}
