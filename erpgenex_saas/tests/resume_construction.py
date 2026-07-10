"""Resume provisioning from migrate/deployment for an existing site folder."""
from __future__ import annotations

import json

import frappe

from erpgenex_saas.services.activity_bundles import get_apps_for_activity
from erpgenex_saas.services.deployment import DeploymentService
from erpgenex_saas.services.deployment_settings import normalize_subdomain
from erpgenex_saas.services.provisioning import ProvisioningService


def run(tenant_name: str | None = None):
	if not tenant_name:
		tenant_name = frappe.db.get_value(
			"SaaS Tenant",
			{"subdomain": ("like", "construction-%")},
			"name",
			order_by="creation desc",
		)
	tenant = frappe.get_doc("SaaS Tenant", tenant_name)
	request_name = frappe.db.get_value(
		"Provisioning Request",
		{"tenant": tenant_name},
		"name",
		order_by="creation desc",
	)
	site_folder = tenant.site_folder or normalize_subdomain(tenant.subdomain or tenant.name)
	activity = "مقاولات"
	apps = get_apps_for_activity(activity)

	ProvisioningService.install_tenant_apps(site_folder, apps)
	ProvisioningService.migrate_site(site_folder)
	result = DeploymentService.deploy_tenant(
		tenant.name,
		site_folder,
		request_name,
		subdomain_slug=normalize_subdomain(tenant.subdomain or tenant.name),
	)

	tenant.reload()
	tenant.status = "Active"
	tenant.provisioned_on = frappe.utils.now_datetime()
	tenant.flags.ignore_version = True
	tenant.save(ignore_permissions=True)

	if request_name:
		frappe.db.set_value("Provisioning Request", request_name, "status", "Completed")

	tenant.reload()
	print(
		json.dumps(
			{
				"tenant": tenant.name,
				"status": tenant.status,
				"access_url": tenant.access_url or tenant.site_url,
				"port_number": tenant.port_number,
				"deployment": result,
			},
			ensure_ascii=False,
			default=str,
		)
	)
