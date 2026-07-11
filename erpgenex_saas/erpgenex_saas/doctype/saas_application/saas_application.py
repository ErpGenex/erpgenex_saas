from frappe.model.document import Document


class SaaSApplication(Document):
	def validate(self):
		if self.is_core:
			self.distribution_type = "Core Free"
			self.monthly_price = 0
			self.annual_price = 0
		if self.repository_url:
			self.repository_is_private = 1
		self.update_available = int(bool(self.latest_version and self.current_version and self.latest_version != self.current_version))
