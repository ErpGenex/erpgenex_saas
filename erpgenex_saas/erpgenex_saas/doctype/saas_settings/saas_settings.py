from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from erpgenex_saas.runtime_config import get_root_domain
from erpgenex_saas.services.payment import PaymentService


class SaaSSettings(Document):
	def validate(self):
		self._sync_deployment_fields()
		self._validate_deployment_settings()
		self._validate_paypal_settings()
		self._validate_github_settings()
		self._enforce_single_payment_provider()

	def _sync_deployment_fields(self):
		if not self.deployment_mode:
			self.deployment_mode = self.site_distribution_method or "Port"

		self.site_distribution_method = self.deployment_mode
		self.base_port = self.start_port or self.base_port or 8000
		self.max_port = self.end_port or self.max_port or 8999
		self.server_ip = self.server_host or self.server_ip or "localhost"
		self.platform_domain = self.root_domain or self.platform_domain or get_root_domain()
		if not self.root_domain:
			self.root_domain = self.platform_domain

	def _validate_deployment_settings(self):
		if self.deployment_mode == "Port":
			start = int(self.start_port or 8000)
			end = int(self.end_port or 8999)
			if start >= end:
				frappe.throw(_("Start Port must be less than End Port"))
			if start < 1024 and start != 80:
				frappe.throw(_("Start Port must be 1024 or higher (except reserved port 80)"))
		elif self.deployment_mode == "Subdomain":
			if not self.root_domain:
				frappe.throw(_("Root Domain is required in Subdomain mode"))
			if not self.subdomain_pattern:
				frappe.throw(_("Subdomain Pattern is required in Subdomain mode"))

	def _validate_paypal_settings(self):
		if not self.paypal_enabled:
			return
		environment = (self.paypal_environment or "Live").strip().title()
		self.paypal_environment = environment if environment in ("Live", "Sandbox") else "Live"
		required_email = PaymentService.REQUIRED_PAYPAL_BUSINESS_EMAIL
		if self.paypal_environment == "Sandbox":
			current_email = (self.paypal_sandbox_business_email or "").strip()
			if not current_email:
				frappe.throw(_("Sandbox PayPal Business Email is required in Sandbox mode"))
		else:
			current_email = (self.paypal_business_email or "").strip().lower()
			if not current_email:
				self.paypal_business_email = required_email
			elif current_email != required_email:
				frappe.throw(_("PayPal Business Email must be {0}").format(required_email))

	def _validate_github_settings(self):
		if not int(self.require_private_repositories or 0):
			return
		from frappe.utils.password import get_decrypted_password

		token = get_decrypted_password(
			"SaaS Settings",
			"SaaS Settings",
			"github_access_token",
			raise_exception=False,
		)
		if not token:
			frappe.msgprint(
				_("GitHub Access Token is recommended when private source-code downloads are enabled."),
				indicator="orange",
				alert=True,
			)

	def _enforce_single_payment_provider(self):
		if self.paypal_enabled:
			self.stripe_ready = 0
			self.moyasar_ready = 0
