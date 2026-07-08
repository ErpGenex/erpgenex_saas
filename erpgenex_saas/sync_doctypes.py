"""Ensure all erpgenex_saas DocTypes are synced after migrate."""

import frappe
from frappe.modules.import_file import import_file_by_path
from frappe.utils import get_bench_path
from pathlib import Path

SAAS_DOCTYPES = [
	"saas_plan",
	"saas_tenant",
	"saas_subscription",
	"provisioning_request",
	"saas_application",
	"saas_package_application",
	"saas_package",
	"saas_invoice",
	"saas_payment",
	"saas_domain",
	"saas_settings",
	"saas_audit_log",
	"saas_notification_log",
	"saas_usage_snapshot",
	"saas_customer_account",
]


def sync_all_doctypes():
	base = Path(get_bench_path()) / "apps" / "erpgenex_saas" / "erpgenex_saas" / "erpgenex_saas" / "doctype"
	for slug in SAAS_DOCTYPES:
		json_path = base / slug / f"{slug}.json"
		if json_path.exists():
			import_file_by_path(str(json_path), force=True, ignore_version=True)
	frappe.clear_cache()
