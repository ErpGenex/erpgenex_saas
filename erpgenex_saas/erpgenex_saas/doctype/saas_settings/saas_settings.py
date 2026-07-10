from __future__ import annotations

import frappe
from frappe.model.document import Document


class SaaSSettings(Document):
	def validate(self):
		self._sync_deployment_fields()
		self._validate_deployment_settings()

	def _sync_deployment_fields(self):
		if not self.deployment_mode:
			self.deployment_mode = self.site_distribution_method or "Port"

		self.site_distribution_method = self.deployment_mode
		self.base_port = self.start_port or self.base_port or 8000
		self.max_port = self.end_port or self.max_port or 8999
		self.server_ip = self.server_host or self.server_ip or "localhost"
		self.platform_domain = self.root_domain or self.platform_domain or "erpgenex.com"
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
