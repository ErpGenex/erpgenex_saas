from __future__ import annotations

import frappe

from erpgenex_saas.services.audit import AuditService


class SiteManagerService:
	@staticmethod
	def suspend_tenant(tenant_name: str, reason: str = ""):
		tenant = frappe.get_doc("SaaS Tenant", tenant_name)
		tenant.status = "Suspended"
		if reason:
			tenant.notes = (tenant.notes or "") + f"\nSuspended: {reason}"
		tenant.save(ignore_permissions=True)
		AuditService.log("tenant.suspended", tenant_name, {"reason": reason
	})
		return tenant

	@staticmethod
	def resume_tenant(tenant_name: str):
		tenant = frappe.get_doc("SaaS Tenant", tenant_name)
		tenant.status = "Active"
		tenant.save(ignore_permissions=True)
		AuditService.log("tenant.resumed", tenant_name, {})
		return tenant

	@staticmethod
	def health_check(tenant_name: str):
		tenant = frappe.get_doc("SaaS Tenant", tenant_name)
		return {
			"tenant": tenant.name,
			"status": tenant.status,
			"site_name": tenant.site_name,
			"provisioned_on": str(tenant.provisioned_on or ""),
			"healthy": tenant.status == "Active"
	}
