from __future__ import annotations

import frappe

from erpgenex_saas.services.deployment import DeploymentService


class TenantHealthMonitor:
	@staticmethod
	def run_all():
		tenants = frappe.get_all(
			"SaaS Tenant",
			filters={"status": ("in", ["Active", "Provisioning"]), "access_url": ("is", "set")},
			pluck="name",
		)
		results = []
		for tenant_name in tenants:
			try:
				results.append(DeploymentService.check_tenant_health(tenant_name))
			except Exception as exc:
				frappe.logger("erpgenex_saas").error(
					"Health monitor failed for %s: %s", tenant_name, exc
				)
				results.append({"tenant": tenant_name, "healthy": False, "error": str(exc)})
		return results
