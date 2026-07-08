from __future__ import annotations

import frappe

from erpgenex_saas.services.audit import AuditService
from erpgenex_saas.services.domain import DomainService
from erpgenex_saas.services.notification import NotificationService


class ProvisioningService:
	@staticmethod
	def enqueue_request(request_name: str):
		frappe.enqueue(
			"erpgenex_saas.tasks.run_provisioning_request",
			queue="long",
			request_name=request_name,
		)

	@staticmethod
	def run(request_name: str):
		logger = frappe.logger("erpgenex_saas")
		request = frappe.get_doc("Provisioning Request", request_name)
		request.status = "Running"
		request.last_message = "Provisioning started"
		request.execution_log = "Queued request picked up by worker\n"
		request.save(ignore_permissions=True)

		try:
			# This is the safe initial implementation layer: record intent and prepare
			# future site creation/dns/ssl/install hooks without touching existing apps.
			tenant = frappe.get_doc("SaaS Tenant", request.tenant)
			tenant.status = "Provisioning"
			if not tenant.site_name:
				tenant.site_name = f"{(tenant.subdomain or tenant.name).lower().replace(' ', '-')}.erpgenex.local"
			tenant.save(ignore_permissions=True)

			request.last_message = "Provisioning blueprint created. Site automation pending next phase."
			request.execution_log += (
				f"Tenant set to Provisioning\nReserved site placeholder: {tenant.site_name}\n"
			)
			request.status = "Completed"
			request.save(ignore_permissions=True)

			tenant.status = "Active"
			tenant.provisioned_on = frappe.utils.now_datetime()
			tenant.save(ignore_permissions=True)

			subdomain = (tenant.subdomain or tenant.name).lower().replace(" ", "-")
			domain_name = f"{subdomain}.erpgenex.local"
			if not frappe.db.exists("SaaS Domain", {"domain_name": domain_name}):
				DomainService.create_domain(tenant.name, domain_name, "Subdomain")

			if request.subscription:
				subscription = frappe.get_doc("SaaS Subscription", request.subscription)
				subscription.provisioned = 1
				subscription.status = "Active" if subscription.status == "Draft" else subscription.status
				subscription.save(ignore_permissions=True)

			NotificationService.notify(
				tenant.name,
				"registration",
				"Tenant provisioned",
				f"Your tenant site {tenant.site_name} is ready.",
			)
			AuditService.log(
				"provisioning.completed",
				request.name,
				{"tenant": tenant.name, "site_name": tenant.site_name},
			)
			logger.info("Provisioning completed for tenant %s", tenant.name)
		except Exception:
			request.status = "Failed"
			request.last_message = frappe.get_traceback(with_context=True)
			request.save(ignore_permissions=True)
			logger.error("Provisioning failed for request %s", request_name)
			raise
