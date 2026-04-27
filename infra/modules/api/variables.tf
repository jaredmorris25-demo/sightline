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
