variable "platform_output" {
  description = "User provided inputs for myPlatform deployment"
  type = object({
    name             = string
    system_name      = string
    environment_type = string
    owner            = string
    tags             = map(string)
  })
  default = null
}

variable "bastion_host_output" {
  description = "Not used, placeholder to satisfy auto-generated main.tf.json"
  type        = any
  default     = null
}

variable "initialization_output" {
  description = "Not used, placeholder to satisfy auto-generated main.tf.json"
  type        = any
  default     = null
}

variable "kubernetes_cluster_output" {
  description = "Not used, placeholder to satisfy auto-generated main.tf.json"
  type        = any
  default     = null
}

variable "model_router_output" {
  description = "model_router_output for fastapi deployment"
  type = object({
    namespace           = string
    server_service_name = string
    server_service_port = number
  })
}

variable "caching_output" {
  description = "redis for fastapi deployment"
  type = object({
    configuration_endpoint_address = string
    password                       = string
    port                           = number
  })
}

variable "fastapi_output" {
  description = "FastAPI output"
  type = object({
  })
  default = null
}

variable "image" {
  description = "Docker image URI from ECR for the fastapi application"
  type        = string
  default     = ""
  nullable    = false
}

variable "replicas" {
  description = "Number of pod replicas"
  type        = number
  default     = 2
  validation {
    condition     = var.replicas > 0
    error_message = "Replicas must be greater than 0"
  }
}

variable "pod_port" {
  description = "Port exposed by the container inside the pod"
  type        = number
  default     = 9100
  validation {
    condition     = var.pod_port >= 1 && var.pod_port <= 65535
    error_message = "Pod port must be between 1 and 65535"
  }
}

variable "server_port" {
  description = "Kubernetes service port"
  type        = number
  default     = 9100
  validation {
    condition     = var.server_port >= 1 && var.server_port <= 65535
    error_message = "Server port must be between 1 and 65535"
  }
}

variable "service_type" {
  description = "Kubernetes service type (ClusterIP, NodePort, LoadBalancer)"
  type        = string
  default     = "ClusterIP"
  validation {
    condition     = contains(["ClusterIP", "NodePort", "LoadBalancer"], var.service_type)
    error_message = "Service type must be one of: ClusterIP, NodePort, LoadBalancer"
  }
}

variable "resource_requests" {
  description = "Resource requests for the container (cpu, memory)"
  type = object({
    cpu    = string
    memory = string
  })
  default = {
    cpu    = "200m"
    memory = "512Mi"
  }
}

variable "resource_limits" {
  description = "Resource limits for the container (cpu, memory)"
  type = object({
    cpu    = string
    memory = string
  })
  default = {
    cpu    = "1000m"
    memory = "1Gi"
  }
}
