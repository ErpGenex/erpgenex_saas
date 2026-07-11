import frappe
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

	def on_trash(self):
		"""Clean up related data when subscription is deleted"""
		self.cleanup_subscription()

	def cleanup_subscription(self):
		"""Clean up related provisioning requests when subscription is deleted"""
		try:
			# Delete related provisioning requests
			frappe.db.delete("Provisioning Request", {"subscription": self.name})

			# Delete related invoices
			frappe.db.delete("SaaS Invoice", {"subscription": self.name})

			# Update tenant's active subscription if this was the active one
			if self.tenant:
				# Check if tenant exists before trying to update it
				if frappe.db.exists("SaaS Tenant", self.tenant):
					tenant = frappe.get_doc("SaaS Tenant", self.tenant)
					if tenant.active_subscription == self.name:
						tenant.active_subscription = None
						tenant.save()

		except Exception as e:
			frappe.log_error(f"Error cleaning up subscription {self.name}: {str(e)}")
			frappe.msgprint(f"Warning: Some cleanup failed. Check error logs for details.")
