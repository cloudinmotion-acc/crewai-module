variable "kubeconfig" {
  description = "Path to kubeconfig file"
  type        = string
  default     = "~/.kube/config"
}

variable "namespace" {
  description = "Kubernetes namespace to deploy into"
  type        = string
  default     = "default"
}

variable "image" {
  description = "Container image (including tag) to run for crew-server"
  type        = string
}

variable "replicas" {
  description = "Number of pod replicas"
  type        = number
  default     = 1
}

variable "model_router_url" {
  description = "URL of the model-router service"
  type        = string
  default     = ""
}

variable "redis_host" {
  description = "Redis host for memory backend"
  type        = string
  default     = ""
}

variable "redis_port" {
  description = "Redis port"
  type        = string
  default     = "6379"
}

variable "redis_password" {
  description = "Redis password (optional)"
  type        = string
  default     = ""
}
