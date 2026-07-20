from __future__ import annotations

import frappe
import json
from frappe.model.document import Document

from erpgenex_saas.services.activity_bundles import get_apps_for_activity, normalize_selected_apps


class ActivitySelectionWizard(Document):
	def validate(self):
		self.validate_server_configuration()
		self.update_selected_apps()

	def validate_server_configuration(self):
		if self.server_type == "سيرفر مخصص":
			if not self.server_ip:
				frappe.throw("عنوان IP السيرفر مطلوب للسيرفر المخصص")
			if not self.domain_name:
				frappe.throw("اسم النطاق مطلوب للسيرفر المخصص")
			if self.enable_ssl:
				if not self.ssl_certificate:
					frappe.throw("شهادة SSL مطلوبة عند تفعيل SSL")
				if not self.ssl_key:
					frappe.throw("مفتاح SSL مطلوب عند تفعيل SSL")

	def update_selected_apps(self):
		apps = normalize_selected_apps(self.selected_apps, self.business_activity)
		self.selected_apps = json.dumps(apps, ensure_ascii=False)

	def on_submit(self):
		self.create_tenant()
		self.create_provisioning_request()

	def create_tenant(self):
		if frappe.db.exists("SaaS Tenant", self.tenant_name):
			tenant = frappe.get_doc("SaaS Tenant", self.tenant_name)
		else:
			tenant = frappe.new_doc("SaaS Tenant")
			tenant.tenant_name = self.tenant_name
			tenant.company_email = self.company_email
			tenant.subdomain = self.subdomain

		tenant.status = "Draft"

		if self.server_type == "سيرفر مخصص":
			tenant.custom_domain = self.domain_name
			server_config = {
				"server_type": "dedicated",
				"server_ip": self.server_ip,
				"domain_name": self.domain_name,
				"enable_ssl": self.enable_ssl
	}
			tenant.notes = json.dumps(server_config, ensure_ascii=False)

		tenant.save(ignore_permissions=True)
		self.tenant = tenant.name

	def create_provisioning_request(self):
		provisioning_request = frappe.new_doc("Provisioning Request")
		provisioning_request.tenant = self.tenant or self.tenant_name
		provisioning_request.request_type = "Initial Provisioning"
		provisioning_request.status = "Queued"
		provisioning_request.requested_by = frappe.session.user

		try:
			apps_to_install = json.loads(self.selected_apps or "[]")
		except Exception:
			apps_to_install = get_apps_for_activity(self.business_activity)

		payload = {
			"business_activity": self.business_activity,
			"apps_to_install": apps_to_install,
			"server_type": self.server_type
	}
		if self.server_type == "سيرفر مخصص":
			payload["server_config"] = {
				"server_ip": self.server_ip,
				"domain_name": self.domain_name,
				"enable_ssl": self.enable_ssl
	}

		provisioning_request.execution_log = json.dumps(payload, ensure_ascii=False)
		provisioning_request.insert(ignore_permissions=True)

		frappe.db.set_value(
			"Activity Selection Wizard",
			self.name,
			{
				"status": "قيد المعالجة",
				"provisioning_status": "تم إنشاء طلب التجهيز"
	},
			update_modified=False,
		)
