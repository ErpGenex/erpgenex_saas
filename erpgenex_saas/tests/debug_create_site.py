"""Direct site creation test."""
from __future__ import annotations

import frappe

from erpgenex_saas.services.provisioning import ProvisioningService


def run():
	suffix = frappe.generate_hash(length=6).lower()
	folder = f"construction-{suffix}"
	print("Creating site", folder)
	ok = ProvisioningService.create_site(folder, f"Test Tenant {suffix}")
	print("RESULT", ok)
	if not ok:
		raise SystemExit(1)
