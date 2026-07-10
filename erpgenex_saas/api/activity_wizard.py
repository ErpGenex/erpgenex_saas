import frappe
import json

from erpgenex_saas.services.activity_bundles import (
	get_apps_for_activity,
	get_apps_preview,
	list_selectable_applications,
	normalize_selected_apps,
)
from erpgenex_saas.services.customer_onboarding import (
	ensure_trial_subscription,
	link_subscription_to_provisioning,
)
from erpgenex_saas.services.provisioning import ProvisioningService


@frappe.whitelist(allow_guest=True)
def get_site_distribution_settings():
	from erpgenex_saas.services.deployment_settings import get_deployment_config

	config = get_deployment_config()
	return {
		"deployment_mode": config.deployment_mode,
		"site_distribution_method": config.deployment_mode,
		"start_port": config.start_port,
		"end_port": config.end_port,
		"base_port": config.start_port,
		"server_host": config.server_host,
		"use_https": config.use_https,
		"root_domain": config.root_domain,
		"subdomain_pattern": config.subdomain_pattern,
		"platform_domain": config.root_domain,
	}


@frappe.whitelist(allow_guest=True)
def get_activity_apps(activity: str):
	return get_apps_preview(activity)


@frappe.whitelist(allow_guest=True)
def list_available_applications():
	return list_selectable_applications()


def _start_wizard_provisioning(wizard) -> str:
	"""Create tenant + provisioning request without doc submit conflicts."""
	wizard.create_tenant()
	wizard.create_provisioning_request()
	frappe.db.set_value(
		"Activity Selection Wizard",
		wizard.name,
		{"status": "قيد المعالجة", "provisioning_status": "جاري التجهيز"},
		update_modified=False,
	)
	frappe.db.commit()
	return frappe.db.get_value(
		"Provisioning Request",
		{"tenant": wizard.tenant_name},
		"name",
		order_by="creation desc",
	)


@frappe.whitelist()
def create_wizard(data):
	"""Create one tenant site for the logged-in customer, without installing optional apps."""
	import re
	from erpgenex_saas.api.customer import get_site_limit
	
	try:
		if isinstance(data, str):
			data = json.loads(data)

		if frappe.session.user == "Guest":
			return {"success": False, "message": "يجب تسجيل الدخول أولاً قبل إنشاء موقع", "redirect_url": "/saas/register"}

		limit_info = get_site_limit()
		if not limit_info.get("can_create_site"):
			return {"success": False, "message": "وصلت للحد الأقصى للمواقع في خطتك الحالية. قم بترقية الخطة لإضافة مواقع أكثر."}

		# Input validation and sanitization
		account_user = frappe.session.user
		tenant_name = data.get("tenant_name", "").strip()
		from erpgenex_saas.api.customer import _safe_contact_email_for_user
		company_email = _safe_contact_email_for_user(account_user)
		subdomain = data.get("subdomain", "").strip()
		business_activity = data.get("business_activity", "عام").strip()

		# Validate required fields
		if not tenant_name or len(tenant_name) < 2:
			return {"success": False, "message": "اسم المستأجر مطلوب (حرفين على الأقل)"}
		
		if not subdomain or len(subdomain) < 3:
			return {"success": False, "message": "النطاق الفرعي مطلوب (3 أحرف على الأقل)"}
		
		if not business_activity:
			return {"success": False, "message": "النشاط التجاري مطلوب"}
		
		# Sanitize tenant name and subdomain
		tenant_name = re.sub(r'[^a-zA-Z0-9\s\-_]', '', tenant_name)[:100]
		subdomain = re.sub(r'[^a-zA-Z0-9\-]', '-', subdomain.lower()).strip('-')[:50]

		if frappe.db.exists("SaaS Tenant", tenant_name):
			return {"success": False, "message": f"المستأجر '{tenant_name}' موجود بالفعل"}

		wizard = frappe.new_doc("Activity Selection Wizard")
		wizard.tenant_name = tenant_name
		wizard.company_email = company_email
		wizard.subdomain = subdomain
		wizard.business_activity = business_activity
		wizard.selected_apps = json.dumps([], ensure_ascii=False)
		wizard.server_type = data.get("server_type", "سيرفر مشترك")

		if wizard.server_type == "سيرفر مخصص":
			wizard.server_ip = data.get("server_ip", "").strip()
			wizard.domain_name = data.get("domain_name", "").strip()
			wizard.enable_ssl = data.get("enable_ssl", False)
			if wizard.enable_ssl:
				wizard.ssl_certificate = data.get("ssl_certificate", "").strip()
				wizard.ssl_key = data.get("ssl_key", "").strip()

		wizard.insert(ignore_permissions=True)
		frappe.db.commit()

		request_name = _start_wizard_provisioning(wizard)
		# Link first created site to the logged-in account. Additional sites are resolved by company_email.
		if not frappe.db.exists("SaaS Customer Account", account_user):
			frappe.get_doc({
				"doctype": "SaaS Customer Account",
				"user": account_user,
				"tenant": tenant_name,
				"is_primary_contact": 1,
			}).insert(ignore_permissions=True)
		sub_info = ensure_trial_subscription(tenant_name, company_email)
		if request_name:
			link_subscription_to_provisioning(tenant_name, request_name)
			ProvisioningService.enqueue_request(request_name)

		tenant = frappe.get_doc("SaaS Tenant", tenant_name)

		return {
			"success": True,
			"queued": True,
			"message": "تم بدء إنشاء الموقع. تابع شريط التقدم حتى اكتمال التشغيل.",
			"wizard_name": wizard.name,
			"provisioning_request": request_name,
			"tenant": tenant.name,
			"access_url": tenant.access_url or tenant.site_url,
			"port_number": tenant.port_number,
			"deployment_mode": tenant.deployment_mode,
			"service_status": tenant.service_status,
			"health_status": tenant.health_status,
			"subscription": sub_info.get("subscription"),
			"login_email": company_email,
			"apps": [],
			"site_limit": get_site_limit(),
			"redirect_url": None,
		}

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Activity Wizard Creation Error")
		return {"success": False, "message": f"حدث خطأ: {str(e)}"}


@frappe.whitelist()
def get_wizard_status(wizard_name):
	try:
		if not frappe.db.exists("Activity Selection Wizard", wizard_name):
			return {"success": False, "message": "المعالج غير موجود"}

		wizard = frappe.get_doc("Activity Selection Wizard", wizard_name)
		tenant = None
		if frappe.db.exists("SaaS Tenant", wizard.tenant_name):
			tenant = frappe.get_doc("SaaS Tenant", wizard.tenant_name)

		progress = {}
		request_status = None
		stage_logs = []
		if tenant:
			raw_progress = getattr(tenant, "provisioning_progress", None)
			if raw_progress:
				try:
					progress = json.loads(raw_progress)
				except Exception:
					progress = {}
			request_name = frappe.db.get_value(
				"Provisioning Request",
				{"tenant": tenant.name},
				"name",
				order_by="creation desc",
			)
			if request_name:
				request_status = frappe.db.get_value("Provisioning Request", request_name, "status")
				stage_logs = frappe.get_all(
					"Provisioning Stage Log",
					filters={"provisioning_request": request_name},
					fields=["stage", "status", "duration_seconds", "start_time"],
					order_by="creation asc",
					limit=20,
					ignore_permissions=True,
				)

		percent = int(progress.get("progress") or 0)
		if request_status in {"Queued", "Running"} and percent <= 0:
			percent = 5
		if tenant and tenant.status == "Active":
			percent = 100
		failed = bool(
			request_status == "Failed"
			or progress.get("status") == "failed"
			or (tenant and tenant.status == "Archived")
			or wizard.status == "فشل"
		)
		error_message = wizard.error_message
		if failed and not error_message:
			error_message = "فشل إنشاء الموقع وتم تنظيف الملفات تلقائيًا. يمكنك المحاولة مرة أخرى."

		return {
			"success": True,
			"status": wizard.status,
			"provisioning_status": wizard.provisioning_status,
			"error_message": error_message,
			"tenant_name": wizard.tenant_name,
			"access_url": tenant and (tenant.access_url or tenant.site_url),
			"tenant_status": tenant and tenant.status,
			"service_status": tenant and tenant.service_status,
			"health_status": tenant and tenant.health_status,
			"request_status": request_status,
			"progress": {**progress, "progress": percent},
			"stage_logs": stage_logs,
			"completed": bool(tenant and tenant.status == "Active" and (tenant.access_url or tenant.site_url)),
			"failed": failed,
		}

	except Exception as e:
		return {"success": False, "message": f"حدث خطأ: {str(e)}"}
