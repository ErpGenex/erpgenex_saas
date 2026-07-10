"""Run construction tenant onboarding E2E test."""
from __future__ import annotations

import json

import frappe

from erpgenex_saas.api.activity_wizard import create_wizard


def run():
	suffix = frappe.generate_hash(length=6).lower()
	data = {
		"tenant_name": f"Construction Co {suffix}",
		"company_email": f"construction-{suffix}@example.com",
		"customer_password": "TestPass123!",
		"subdomain": f"construction-{suffix}",
		"business_activity": "مقاولات",
		"server_type": "سيرفر مشترك",
	}
	print("START", json.dumps(data, ensure_ascii=False))
	result = create_wizard(data)
	print("RESULT", json.dumps(result, ensure_ascii=False, default=str))

	if not result.get("success"):
		raise SystemExit(1)

	tenant = frappe.get_doc("SaaS Tenant", result["tenant"])
	print("TENANT_STATUS", tenant.status)
	print("ACCESS_URL", tenant.access_url)
	print("APPS_REQUEST", frappe.parse_json(
		frappe.db.get_value(
			"Activity Selection Wizard",
			result.get("wizard_name"),
			"selected_apps",
		)
	))

	site_folder = tenant.site_folder
	if site_folder:
		from pathlib import Path
		from frappe.utils import get_bench_path

		apps_file = Path(get_bench_path()) / "sites" / site_folder / "apps.txt"
		if apps_file.exists():
			print("INSTALLED_APPS", apps_file.read_text(encoding="utf-8"))

	return result
