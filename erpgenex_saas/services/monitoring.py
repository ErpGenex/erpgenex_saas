from __future__ import annotations

import frappe


class MonitoringService:
	@staticmethod
	def platform_snapshot():
		return {
			"tenants": frappe.db.count("SaaS Tenant"),
			"active_tenants": frappe.db.count("SaaS Tenant", {"status": "Active"}),
			"subscriptions": frappe.db.count("SaaS Subscription"),
			"active_subscriptions": frappe.db.count("SaaS Subscription", {"status": "Active"}),
			"queued_provisioning": frappe.db.count("Provisioning Request", {"status": "Queued"}),
			"failed_provisioning": frappe.db.count("Provisioning Request", {"status": "Failed"}),
			"open_invoices": frappe.db.count("SaaS Invoice", {"status": ("in", ["Draft", "Issued", "Partially Paid"])}),
		}

	@staticmethod
	def record_usage_snapshot():
		snapshot = MonitoringService.platform_snapshot()
		doc = frappe.get_doc({"doctype": "SaaS Usage Snapshot", **snapshot})
		doc.insert(ignore_permissions=True)
		return doc
