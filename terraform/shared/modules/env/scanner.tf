locals {
  scanner_name = "fac-file-scanner"
}

module "fac-file-scanner" {
  source            = "../scanner"
  name              = local.scanner_name
  cf_org_name       = var.cf_org_name
  cf_space_name     = var.cf_space_name
  cf_space_id       = var.cf_space_id
  https_proxy       = module.https-proxy.https_proxy
  s3_id             = module.s3-private.bucket_id
  logdrain_id       = module.cg-logshipper.logdrain_service_id
  scanner_instances = 1
  scanner_memory    = 512
  disk_quota        = 512
}

resource "cloudfoundry_network_policy" "scanner-network-policy" {
  provider = cloudfoundry-community
  policy {
    source_app      = module.fac-file-scanner.app_id
    destination_app = module.https-proxy.app_id
    port            = "61443"
    protocol        = "tcp"
  }
}
