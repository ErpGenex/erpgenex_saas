from frappe.model.document import Document
import frappe


class ProvisioningRequest(Document):
	def on_trash(self):
		"""Clean up related data when provisioning request is deleted"""
		self.cleanup_provisioning_request()

	def cleanup_provisioning_request(self):
		"""Clean up related data when provisioning request is deleted"""
		try:
			# Delete related provisioning stage logs
			frappe.db.delete("Provisioning Stage Log", {"provisioning_request": self.name
	})

			# Update subscription's provisioning request if this was linked
			if self.subscription:
				# Check if subscription exists before trying to update it
				if frappe.db.exists("SaaS Subscription", self.subscription):
					subscription = frappe.get_doc("SaaS Subscription", self.subscription)
					if subscription.provisioning_request == self.name:
						subscription.provisioning_request = None
						subscription.save()

		except Exception as e:
			frappe.log_error(f"Error cleaning up provisioning request {self.name}: {str(e)}")
			frappe.msgprint(f"Warning: Some cleanup failed. Check error logs for details.")
