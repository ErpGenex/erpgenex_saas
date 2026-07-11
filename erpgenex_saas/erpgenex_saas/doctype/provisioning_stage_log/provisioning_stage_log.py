import frappe
from frappe.model.document import Document


class ProvisioningStageLog(Document):
	def on_trash(self):
		"""Clean up related data when stage log is deleted"""
		self.cleanup_stage_log()

	def cleanup_stage_log(self):
		"""Clean up related provisioning request when stage log is deleted"""
		try:
			# Update provisioning request if this stage log was linked
			if self.provisioning_request:
				# Check if provisioning request exists before trying to update it
				if frappe.db.exists("Provisioning Request", self.provisioning_request):
					provisioning_request = frappe.get_doc("Provisioning Request", self.provisioning_request)
					# Clear any reference to this stage log in provisioning request
					# (assuming there's a field like 'stage_log' or similar)
					if hasattr(provisioning_request, 'stage_log') and provisioning_request.stage_log == self.name:
						provisioning_request.stage_log = None
						provisioning_request.save()

		except Exception as e:
			frappe.log_error(f"Error cleaning up stage log {self.name}: {str(e)}")
			frappe.msgprint(f"Warning: Some cleanup failed. Check error logs for details.")
