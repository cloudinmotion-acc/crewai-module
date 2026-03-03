terraform {
  required_version = ">= 1.0.1, < 2.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.83.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5.2"
    }
    template = {
      source  = "hashicorp/template"
      version = "~> 2.2"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2.3"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0.6"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6.3"
    }
    external = {
      source  = "hashicorp/external"
      version = "~> 2.3.4"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.17.0"
    }
    http = {
      source  = "hashicorp/http"
      version = "~> 3.4.5"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.12.1"
    }
    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = "1.25.0"
    }
    confluent = {
      source  = "confluentinc/confluent"
      version = "2.12.0"
    }
  }
}