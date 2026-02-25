# Kubernetes deployment for crew-server
# Usage: set provider configuration (e.g. KUBECONFIG env variable or
# `kubeconfig` variable) and specify `image` when invoking terraform.

provider "kubernetes" {
  config_path = var.kubeconfig
}

resource "kubernetes_namespace" "app" {
  metadata {
    name = var.namespace
  }
}

resource "kubernetes_deployment" "crew" {
  metadata {
    name      = "crew-server"
    namespace = kubernetes_namespace.app.metadata[0].name
  }
  spec {
    replicas = var.replicas
    selector {
      match_labels = {
        app = "crew-server"
      }
    }
    template {
      metadata {
        labels = {
          app = "crew-server"
        }
      }
      spec {
        container {
          name  = "crew"
          image = var.image
          ports {
            container_port = 9100
          }
          env = [
            {
              name  = "MODEL_ROUTER_URL"
              value = var.model_router_url
            },
            {
              name  = "REDIS_HOST"
              value = var.redis_host
            },
            {
              name  = "REDIS_PORT"
              value = var.redis_port
            },
            {
              name  = "REDIS_PASSWORD"
              value = var.redis_password
            }
          ]
        }
      }
    }
  }
}

resource "kubernetes_service" "crew" {
  metadata {
    name      = "crew-service"
    namespace = kubernetes_namespace.app.metadata[0].name
  }

  spec {
    selector = {
      app = kubernetes_deployment.crew.spec[0].template[0].metadata[0].labels.app
    }
    port {
      port        = 9100
      target_port = 9100
      protocol    = "TCP"
    }
    type = "ClusterIP"
  }
}
