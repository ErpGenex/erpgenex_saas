"""Activate an existing construction tenant site (migrate + port deploy + health)."""
from __future__ import annotations

import json
import subprocess

import frappe

from erpgenex_saas.services.deployment import DeploymentService
from erpgenex_saas.services.deployment_settings import normalize_subdomain
from erpgenex_saas.services.provisioning import ProvisioningService
from frappe.utils import get_bench_path


def run(tenant_name: str = "Construction Co 63220e"):
	tenant = frappe.get_doc("SaaS Tenant", tenant_name)
	site_folder = tenant.site_folder or normalize_subdomain(tenant.subdomain or tenant.name)
	request_name = frappe.db.get_value(
		"Provisioning Request",
		{"tenant": tenant_name
	},
		"name",
		order_by="creation desc",
	)
	bench_path = get_bench_path()

	print("MIGRATE", site_folder)
	result = subprocess.run(
		["bench", "--site", site_folder, "migrate"],
		cwd=bench_path,
		capture_output=True,
		text=True,
		timeout=3600,
		check=False,
	)
	if result.returncode != 0:
		print("MIGRATE_STDERR", result.stderr[-2000:])
		raise RuntimeError("Migration failed")

	print("DEPLOY", tenant_name)
	deploy_result = DeploymentService.deploy_tenant(
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
		frappe.db.set_value(
			"Provisioning Request",
			request_name,
			{"status": "Completed", "last_message": "Site activated"
	},
		)

	frappe.db.commit()
	tenant.reload()

	access_url = tenant.access_url or tenant.site_url
	healthy = DeploymentService.health_check_url(f"http://127.0.0.1:{tenant.port_number}") if tenant.port_number else False

	print(
		json.dumps(
			{
				"success": tenant.status == "Active" and bool(access_url) and healthy,
				"tenant": tenant.name,
				"status": tenant.status,
				"access_url": access_url,
				"port_number": tenant.port_number,
				"healthy": healthy,
				"deploy": deploy_result
	},
			ensure_ascii=False,
			default=str,
		)
	)

	if tenant.status != "Active" or not access_url or not healthy:
		raise SystemExit(1)
