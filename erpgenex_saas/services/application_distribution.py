from __future__ import annotations

import subprocess

import frappe
from frappe.utils import get_bench_path, now_datetime

from erpgenex_saas.services.audit import AuditService
from erpgenex_saas.services.license_manager import LicenseManager
from erpgenex_saas.services.provisioning import ProvisioningService


class ApplicationDistributionService:
	"""Install and update private Frappe apps only through the SaaS platform."""

	@staticmethod
	def _ensure_allowed(tenant: str, application: str):
		app = ApplicationDistributionService._resolve_application(application)
		if not LicenseManager.is_application_enabled(tenant, app.name):
			frappe.throw("Application is not enabled for this tenant")
		if app.repository_url and not app.repository_is_private:
			frappe.throw("Application repositories must remain private")
		return app

	@staticmethod
	def _resolve_application(application: str):
		try:
			return frappe.get_doc("SaaS Application", application)
		except Exception:
			pass

		docname = frappe.db.get_value("SaaS Application", {"app_slug": application}, "name")
		if docname:
			return frappe.get_doc("SaaS Application", docname)

		docname = frappe.db.get_value("SaaS Application", {"application_name": application}, "name")
		if docname:
			return frappe.get_doc("SaaS Application", docname)

		docname = frappe.db.get_value("SaaS Application", {"title": application}, "name")
		if docname:
			return frappe.get_doc("SaaS Application", docname)

		frappe.throw("Application not found")

	@staticmethod
	def _tenant_site(tenant: str) -> str:
		tenant_doc = frappe.get_doc("SaaS Tenant", tenant)
		site = tenant_doc.site_folder or tenant_doc.site_name
		if not site:
			frappe.throw("Tenant site is not provisioned")
		return site

	@staticmethod
	def install_application(tenant: str, application: str):
		app = ApplicationDistributionService._ensure_allowed(tenant, application)
		site = ApplicationDistributionService._tenant_site(tenant)
		with ProvisioningService._site_lock(site):
			installed_apps = ProvisioningService._list_installed_apps(site)
			if app.app_slug in installed_apps:
				AuditService.log(
					"application.install",
					application,
					{"tenant": tenant, "site": site, "returncode": 0, "skipped": True},
				)
				return {
					"tenant": tenant,
					"application": application,
					"installed_on": now_datetime(),
					"output": f"{app.app_slug} already installed",
					"skipped": True,
				}

			cmd = ["bench", "--site", site, "install-app", app.app_slug]
			result = subprocess.run(cmd, cwd=get_bench_path(), capture_output=True, text=True, timeout=1800)
			if result.returncode != 0 and app.app_slug not in ProvisioningService._list_installed_apps(site):
				AuditService.log(
					"application.install",
					application,
					{"tenant": tenant, "site": site, "returncode": result.returncode},
				)
				frappe.throw(result.stderr or "Application installation failed")

			ProvisioningService.migrate_site(site)
			ProvisioningService.restore_tenant_desk(site)
			AuditService.log(
				"application.install",
				application,
				{"tenant": tenant, "site": site, "returncode": result.returncode},
			)
			return {
				"tenant": tenant,
				"application": application,
				"installed_on": now_datetime(),
				"output": result.stdout,
			}

	@staticmethod
	def update_application(tenant: str, application: str):
		app = ApplicationDistributionService._ensure_allowed(tenant, application)
		site = ApplicationDistributionService._tenant_site(tenant)
		with ProvisioningService._site_lock(site):
			cmd = ["bench", "--site", site, "migrate"]
			result = subprocess.run(cmd, cwd=get_bench_path(), capture_output=True, text=True, timeout=1800)
			ProvisioningService.restore_tenant_desk(site)
			AuditService.log(
				"application.update",
				application,
				{"tenant": tenant, "site": site, "returncode": result.returncode},
			)
			if result.returncode != 0:
				frappe.throw(result.stderr or "Application update failed")
			return {
				"tenant": tenant,
				"application": application,
				"updated_on": now_datetime(),
				"output": result.stdout,
			}
