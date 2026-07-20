"""Inspect construction tenant provisioning state."""
from __future__ import annotations

import json

import frappe


def run(tenant_name: str | None = None):
	if not tenant_name:
		tenant_name = frappe.db.get_value(
			"SaaS Tenant",
			{"subdomain": ("like", "construction-%")},
			"name",
			order_by="creation desc",
		)
	tenant = frappe.get_doc("SaaS Tenant", tenant_name)
	print(
		json.dumps(
			{
				"name": tenant.name,
				"status": tenant.status,
				"site_folder": tenant.site_folder,
				"access_url": tenant.access_url,
				"port_number": tenant.port_number,
				"service_status": tenant.service_status,
				"health_status": tenant.health_status
	},
			ensure_ascii=False,
		)
	)
