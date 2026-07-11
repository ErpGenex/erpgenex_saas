import frappe
from frappe.model.document import Document


class SaaSInvoice(Document):
	def on_trash(self):
		"""Clean up related data when invoice is deleted"""
		self.cleanup_invoice()

	def cleanup_invoice(self):
		"""Clean up related subscription when invoice is deleted"""
		try:
			# Update subscription if this invoice was linked
			if self.subscription:
				# Check if subscription exists before trying to update it
				if frappe.db.exists("SaaS Subscription", self.subscription):
					subscription = frappe.get_doc("SaaS Subscription", self.subscription)
					# Clear any reference to this invoice in subscription
					# (assuming there's a field like 'invoice' in subscription)
					if hasattr(subscription, 'invoice') and subscription.invoice == self.name:
						subscription.invoice = None
						subscription.save()

		except Exception as e:
			frappe.log_error(f"Error cleaning up invoice {self.name}: {str(e)}")
			frappe.msgprint(f"Warning: Some cleanup failed. Check error logs for details.")
