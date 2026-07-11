from frappe.model.document import Document

from erpgenex_saas.services.license_manager import LicenseManager


class SaaSSubscription(Document):
	def validate(self):
		enabled = self.status in ("Trial", "Active", "Grace Period")
		self.features_enabled = int(enabled)
		self.disabled_reason = "" if enabled else f"Subscription {self.status}"

	def on_update(self):
		if self.application:
			LicenseManager.ensure_subscription_license(self.name)
