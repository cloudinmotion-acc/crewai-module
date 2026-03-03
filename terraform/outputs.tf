output "crewai_output" {
  description = "CrewAI ComponentAsset outputs consumed by other components."
  value = {
    namespace        = var.model_router_output.namespace
    image_used       = var.image
    replica_count    = kubernetes_deployment_v1.crew.spec[0].replicas
    deployment_name  = kubernetes_deployment_v1.crew.metadata[0].name
    service_name     = kubernetes_service_v1.crew.metadata[0].name
    service_ip       = kubernetes_service_v1.crew.spec[0].cluster_ip
    service_port     = kubernetes_service_v1.crew.spec[0].port[0].port
    service_endpoint = "${kubernetes_service_v1.crew.metadata[0].name}.${var.model_router_output.namespace}.svc.cluster.local"
    secret_name      = kubernetes_secret_v1.crewai_secrets.metadata[0].name
  }
}

output "mpp_report" {
  description = "Comprehensive output map for component consumption by other modules"
  value = {
    namespace        = var.model_router_output.namespace
    image_used       = var.image
    replica_count    = kubernetes_deployment_v1.crew.spec[0].replicas
    deployment_name  = kubernetes_deployment_v1.crew.metadata[0].name
    service_name     = kubernetes_service_v1.crew.metadata[0].name
    service_ip       = kubernetes_service_v1.crew.spec[0].cluster_ip
    service_port     = kubernetes_service_v1.crew.spec[0].port[0].port
    service_endpoint = "${kubernetes_service_v1.crew.metadata[0].name}.${var.model_router_output.namespace}.svc.cluster.local"
    secret_name      = kubernetes_secret_v1.crewai_secrets.metadata[0].name
  }
}