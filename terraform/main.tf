resource "kubernetes_secret_v1" "crewai_secrets" {
  metadata {
    name      = "crewai-secrets"
    namespace = var.model_router_output.namespace
  }
  type = "Opaque"
  data = {
    MODEL_ROUTER_URL = "http://${var.model_router_output.server_service_name}.${var.model_router_output.namespace}.svc.cluster.local:${tostring(var.model_router_output.server_service_port)}"
    REDIS_HOST       = var.caching_output.configuration_endpoint_address
    REDIS_PORT       = tostring(var.caching_output.port)
    REDIS_PASSWORD   = var.caching_output.password
  }
}
resource "kubernetes_deployment_v1" "crew" {
  metadata {
    name      = "crew-server"
    namespace = var.model_router_output.namespace
    labels = {
      app = "crew-server"
    }
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

          port {
            container_port = var.pod_port
            name           = "http"
          }

          env_from {
            secret_ref {
              name = kubernetes_secret_v1.crewai_secrets.metadata[0].name
            }
          }

          resources {
            requests = {
              cpu    = var.resource_requests.cpu
              memory = var.resource_requests.memory
            }
            limits = {
              cpu    = var.resource_limits.cpu
              memory = var.resource_limits.memory
            }
          }
        }
      }
    }
  }

  depends_on = [kubernetes_secret_v1.crewai_secrets]
}

resource "kubernetes_service_v1" "crew" {
  metadata {
    name      = "crew-service"
    namespace = var.model_router_output.namespace
    labels = {
      app = "crew-server"
    }
  }

  spec {
    selector = {
      app = "crew-server"
    }
    port {
      port        = var.server_port
      target_port = var.pod_port
      protocol    = "TCP"
      name        = "http"
    }
    type = var.service_type
  }

  depends_on = [kubernetes_deployment_v1.crew]
}
