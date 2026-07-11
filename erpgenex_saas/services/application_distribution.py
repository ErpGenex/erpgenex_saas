from __future__ import annotations

import subprocess

import frappe
from frappe.utils import get_bench_path, now_datetime

from erpgenex_saas.services.audit import AuditService
from erpgenex_saas.services.license_manager import LicenseManager


class ApplicationDistributionService:
	"""Install and update private Frappe apps only through the SaaS platform."""

	@staticmethod
	def _ensure_allowed(tenant: str, application: str):
		if not LicenseManager.is_application_enabled(tenant, application):
			frappe.throw("Application is not enabled for this tenant")
		app = frappe.get_doc("SaaS Application", application)
		if app.repository_url and not app.repository_is_private:
			frappe.throw("Application repositories must remain private")
		return app

	@staticmethod
	def install_application(tenant: str, application: str):
		app = ApplicationDistributionService._ensure_allowed(tenant, application)
		tenant_doc = frappe.get_doc("SaaS Tenant", tenant)
		site = tenant_doc.site_folder or tenant_doc.site_name
		if not site:
			frappe.throw("Tenant site is not provisioned")
		cmd = ["bench", "--site", site, "install-app", app.app_slug]
		result = subprocess.run(cmd, cwd=get_bench_path(), capture_output=True, text=True, timeout=1800)
		AuditService.log("application.install", application, {"tenant": tenant, "site": site, "returncode": result.returncode})
		if result.returncode != 0:
			frappe.throw(result.stderr or "Application installation failed")
		return {"tenant": tenant, "application": application, "installed_on": now_datetime(), "output": result.stdout}

	@staticmethod
	def update_application(tenant: str, application: str):
		app = ApplicationDistributionService._ensure_allowed(tenant, application)
		tenant_doc = frappe.get_doc("SaaS Tenant", tenant)
		site = tenant_doc.site_folder or tenant_doc.site_name
		if not site:
			frappe.throw("Tenant site is not provisioned")
		cmd = ["bench", "--site", site, "migrate"]
		result = subprocess.run(cmd, cwd=get_bench_path(), capture_output=True, text=True, timeout=1800)
		AuditService.log("application.update", application, {"tenant": tenant, "site": site, "returncode": result.returncode})
		if result.returncode != 0:
			frappe.throw(result.stderr or "Application update failed")
		return {"tenant": tenant, "application": application, "updated_on": now_datetime(), "output": result.stdout}
