from frappe.model.document import Document
import frappe
import os
import shutil


class SaaSTenant(Document):
	def on_trash(self):
		"""Clean up related data when tenant is deleted"""
		self.cleanup_site()

	def cleanup_site(self):
		"""Clean up site folder and database when tenant is deleted"""
		try:
			# Delete related subscriptions
			frappe.db.delete("SaaS Subscription", {"tenant": self.name})

			# Delete related provisioning requests
			frappe.db.delete("Provisioning Request", {"tenant": self.name})

			# Delete site folder if exists
			if self.site_folder:
				site_path = frappe.utils.get_bench_path("sites", self.site_folder)
				if os.path.exists(site_path):
					shutil.rmtree(site_path)
					frappe.msgprint(f"Site folder {self.site_folder} deleted")

			# Drop database if exists
			if self.site_name:
				try:
					frappe.db.sql(f"DROP DATABASE IF EXISTS `{self.site_name}`")
					frappe.msgprint(f"Database {self.site_name} dropped")
				except Exception as e:
					frappe.log_error(f"Failed to drop database {self.site_name}: {str(e)}")

		except Exception as e:
			frappe.log_error(f"Error cleaning up tenant {self.name}: {str(e)}")
			frappe.msgprint(f"Warning: Some cleanup failed. Check error logs for details.")
