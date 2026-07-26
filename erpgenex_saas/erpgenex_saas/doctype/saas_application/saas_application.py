from frappe.model.document import Document

from erpgenex_saas.constants import PAID_LICENSED_APPS


class SaaSApplication(Document):
	def validate(self):
		app_name = getattr(self, "application_name", None) or self.name
		is_paid_app = app_name in PAID_LICENSED_APPS
		if self.is_core:
			self.distribution_type = "Core Free"
			self.monthly_price = 0
			self.annual_price = 0
		self.repository_is_private = 1 if is_paid_app else 0
		self.update_available = int(bool(self.latest_version and self.current_version and self.latest_version != self.current_version))
