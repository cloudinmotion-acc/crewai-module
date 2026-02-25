output "namespace" {
  value = kubernetes_namespace.app.metadata[0].name
}

output "service_name" {
  value = kubernetes_service.crew.metadata[0].name
}

output "deployment_name" {
  value = kubernetes_deployment.crew.metadata[0].name
}
