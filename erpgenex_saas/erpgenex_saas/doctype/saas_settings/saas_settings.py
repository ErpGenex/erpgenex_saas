from __future__ import annotations

import frappe
from frappe.model.document import Document

from erpgenex_saas.runtime_config import get_root_domain
from erpgenex_saas.services.payment import PaymentService


class SaaSSettings(Document):
	def validate(self):
		self._sync_deployment_fields()
		self._validate_deployment_settings()
		self._validate_paypal_settings()
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
				frappe.throw("Start Port must be less than End Port")
			if start < 1024 and start != 80:
				frappe.throw("Start Port must be 1024 or higher (except reserved port 80)")
		elif self.deployment_mode == "Subdomain":
			if not self.root_domain:
				frappe.throw("Root Domain is required in Subdomain mode")
			if not self.subdomain_pattern:
				frappe.throw("Subdomain Pattern is required in Subdomain mode")

	def _validate_paypal_settings(self):
		if not self.paypal_enabled:
			return
		required_email = PaymentService.REQUIRED_PAYPAL_BUSINESS_EMAIL
		current_email = (self.paypal_business_email or "").strip().lower()
		if not current_email:
			self.paypal_business_email = required_email
		elif current_email != required_email:
			frappe.throw(f"PayPal Business Email must be {required_email}")

	def _enforce_single_payment_provider(self):
		if self.paypal_enabled:
			self.stripe_ready = 0
			self.moyasar_ready = 0
