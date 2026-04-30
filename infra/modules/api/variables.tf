variable "azure_search_endpoint" {
  type        = string
  description = "Azure AI Search service endpoint, e.g. https://search-sightline-dev.search.windows.net"
  default     = ""
}

variable "azure_search_api_key" {
  type        = string
  sensitive   = true
  description = "Azure AI Search admin API key."
  default     = ""
}

variable "azure_storage_connection_string" {
  type      = string
  sensitive = true
  default   = ""
}

variable "azure_storage_container_raw" {
  type    = string
  default = "media-raw"
}

variable "azure_storage_container_processed" {
  type    = string
  default = "media-processed"
}
