from __future__ import annotations

import re

import frappe

from erpgenex_saas.api import portal
from erpgenex_saas.bootstrap import ensure_roles
from erpgenex_saas.runtime_config import get_email_domain
from erpgenex_saas.services.activity_bundles import CORE_PLATFORM_APPS, normalize_app_entry
from erpgenex_saas.services.catalog import CatalogService
from erpgenex_saas.services.deployment import DeploymentService
from erpgenex_saas.services.deployment_settings import get_deployment_config
from erpgenex_saas.services.password_manager import PasswordManager
from erpgenex_saas.services.provisioning import ProvisioningService

SITE_LIMITS_BY_PLAN = {
	"free": 1,
	"trial": 1,
	"starter": 1,
	"business": 3,
	"professional": 10,
	"enterprise": None,
	"unlimited": None
	}


def _normalize_email_address(email: str | None) -> str:
	email = (email or "").strip().lower()
	email = (
		email.replace("\u200f", "")
		.replace("\u200e", "")
		.replace("\u200b", "")
		.replace("＠", "@")
		.replace("﹫", "@")
	)
	email = re.sub(r"\s+", "", email)
	if "@" not in email:
		return email
	local_part, domain = email.rsplit("@", 1)
	try:
		domain = domain.encode("idna").decode("ascii")
	except Exception:
		pass
	return f"{local_part}@{domain}"


def _is_valid_email_address(email: str | None) -> bool:
	email = _normalize_email_address(email)
	return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email or ""))


def _safe_contact_email_for_user(user: str | None = None) -> str:
	user = user or frappe.session.user
	email = _normalize_email_address(frappe.db.get_value("User", user, "email") or user)
	if _is_valid_email_address(email):
		return email
	safe_user = re.sub(r"[^a-zA-Z0-9._%+-]+", ".", (user or "customer").lower()).strip(".") or "customer"
	return f"{safe_user}@{get_email_domain()}"


def _require_customer_user(user: str | None = None) -> str:
	user = user or frappe.session.user
	if user == "Guest":
		frappe.throw("Login required", frappe.PermissionError)
	return user


def _plan_site_limit(plan_name: str | None) -> int | None:
	if not plan_name:
		return 1
	try:
		max_sites = frappe.db.get_value("SaaS Plan", plan_name, "max_sites")
		if max_sites is not None and max_sites != "":
			return int(max_sites) if max_sites > 0 else None
	except Exception:
		pass
	# Fallback to old dictionary-based logic
	plan = plan_name.lower()
	for key, limit in SITE_LIMITS_BY_PLAN.items():
		if key in plan:
			return limit
	return 1


def _user_tenant_names(user: str | None = None) -> list[str]:
	user = _require_customer_user(user)
	names: list[str] = []
	linked = frappe.get_all(
		"SaaS Customer Account",
		filters={"user": user
	},
		pluck="tenant",
		ignore_permissions=True,
	)
	for tenant in linked:
		if tenant and tenant not in names:
			names.append(tenant)

	by_email = frappe.get_all(
		"SaaS Tenant",
		filters={"company_email": user
	},
		pluck="name",
		ignore_permissions=True,
	)
	for tenant in by_email:
		if tenant and tenant not in names:
			names.append(tenant)
	return names


def _get_customer_tenant(user: str | None = None, tenant: str | None = None) -> str | None:
	names = _user_tenant_names(user)
	if tenant:
		if tenant not in names:
			frappe.throw("Not permitted for this tenant", frappe.PermissionError)
		return tenant
	return names[0] if names else None


def _current_site_limit(user: str | None = None) -> dict:
	user = _require_customer_user(user)
	tenant_names = _user_tenant_names(user)
	active_site_names = [
		tenant
		for tenant in tenant_names
		if frappe.db.get_value("SaaS Tenant", tenant, "status") != "Archived"
	]
	best_limit = 1
	best_plan = "Free"
	unlimited = False
	if tenant_names:
		subscriptions = frappe.get_all(
			"SaaS Subscription",
			filters={"tenant": ["in", tenant_names], "status": ["in", ["Trial", "Grace Period", "Active", "Draft"]]},
			fields=["plan", "status"],
			ignore_permissions=True,
		)
		for sub in subscriptions:
			limit = _plan_site_limit(sub.plan)
			if limit is None:
				unlimited = True
				best_plan = sub.plan
				break
			if limit > best_limit:
				best_limit = limit
				best_plan = sub.plan
	limit = None if unlimited else best_limit
	used = len(active_site_names)
	return {
		"plan": best_plan,
		"limit": limit,
		"used": used,
		"remaining": None if limit is None else max(limit - used, 0),
		"can_create_site": True if limit is None else used < limit
	}


def _latest_selected_apps(tenant_name: str) -> list[str]:
	request = frappe.db.get_value(
		"Provisioning Request",
		{"tenant": tenant_name
	},
		["name", "execution_log"],
		order_by="creation desc",
		as_dict=True,
	)
	if not request or not request.get("execution_log"):
		return []
	log = request.execution_log or ""
	try:
		import json

		payload = json.loads(log)
		apps = payload.get("apps_to_install", [])
		return [slug for slug in (normalize_app_entry(app) for app in apps) if slug]
	except Exception:
		pass
	for line in log.splitlines():
		if line.startswith("Apps to install:"):
			return [part.strip() for part in line.split(":", 1)[1].split(",") if part.strip()]
	return []


def _application_details(app_slugs: list[str]) -> list[dict]:
	items = []
	for slug in app_slugs:
		payload = CatalogService._application_payload(slug)
		items.append(
			{
				"name": payload["application_name"],
				"app_slug": payload["app_slug"],
				"display_name": payload["display_name"],
				"description": payload["description"],
				"category": payload["category"],
				"monthly_price": payload["monthly_price"],
				"status": "Installed"
	}
		)
	return items


def _tenant_summary(tenant_name: str) -> dict:
	tenant = frappe.get_doc("SaaS Tenant", tenant_name)
	data = tenant.as_dict()
	data["installed_apps"] = _application_details(_latest_selected_apps(tenant_name))
	data["custom_fields"] = {
		"brand_name": tenant.get("brand_name"),
		"custom_domain": tenant.get("custom_domain"),
		"notes": tenant.get("notes")
	}
	# Add credentials for dashboard display
	try:
		from frappe.utils.password import get_decrypted_password
		data["admin_password"] = get_decrypted_password("SaaS Tenant", tenant_name, "admin_password", raise_exception=False) or tenant.admin_password or ""
	except Exception:
		data["admin_password"] = tenant.admin_password or ""
	return data


@frappe.whitelist(allow_guest=True)
def register_account(customer_name: str, company_email: str, password: str):
	from frappe.auth import LoginManager
	from erpgenex_saas.services.password_manager import PasswordManager

	customer_name = (customer_name or "").strip()
	company_email = _normalize_email_address(company_email)
	password = (password or "").strip()
	if len(customer_name) < 2:
		return {"success": False, "message": "اسم العميل مطلوب"
	}
	if not _is_valid_email_address(company_email):
		return {"success": False, "message": "البريد الإلكتروني غير صالح. اكتب البريد بصيغة مثل name@company.com بدون مسافات."
	}
	password_validation = PasswordManager().validate_password_strength(password)
	if not password_validation["valid"]:
		return {"success": False, "message": ", ".join(password_validation["errors"])}
	if frappe.db.exists("User", company_email):
		return {"success": False, "message": "هذا البريد مسجل بالفعل. سجّل الدخول للمتابعة."
	}

	ensure_roles()
	user = frappe.get_doc(
		{
			"doctype": "User",
			"email": company_email,
			"first_name": customer_name[:100],
			"send_welcome_email": 0,
			"user_type": "Website User",
			"new_password": password,
			"roles": [{"role": "SaaS Customer"}]
	}
	)
	user.insert(ignore_permissions=True)
	frappe.db.commit()
	LoginManager().login_as(company_email)
	return {
		"success": True,
		"message": "تم إنشاء الحساب بنجاح. يمكنك الآن إدارة مواقعك من لوحة التحكم.",
		"redirect_url": "/saas/dashboard"
	}


@frappe.whitelist()
def get_site_limit():
	return _current_site_limit()


@frappe.whitelist()
def get_dashboard():
	user = _require_customer_user()
	tenant_names = _user_tenant_names(user)
	visible_tenant_names = [
		name
		for name in tenant_names
		if frappe.db.get_value("SaaS Tenant", name, "status") != "Archived"
	]
	tenants = [_tenant_summary(name) for name in visible_tenant_names]
	tenant = tenants[0] if tenants else None
	tenant_filters = {"tenant": ["in", tenant_names]} if tenant_names else {"tenant": "__no_tenant__"
	}
	subscription = None
	if tenant and tenant.get("active_subscription"):
		subscription = frappe.get_doc("SaaS Subscription", tenant["active_subscription"]).as_dict()
	invoices = frappe.get_all(
		"SaaS Invoice",
		filters=tenant_filters,
		fields=["name", "tenant", "status", "amount_due", "paid_amount", "invoice_date"],
		order_by="creation desc",
		limit=10,
		ignore_permissions=True,
	)
	payments = frappe.get_all(
		"SaaS Payment",
		filters=tenant_filters,
		fields=["name", "tenant", "provider", "amount", "status", "creation"],
		order_by="creation desc",
		limit=10,
		ignore_permissions=True,
	)
	domains = frappe.get_all(
		"SaaS Domain",
		filters=tenant_filters,
		fields=["name", "tenant", "domain_name", "status", "ssl_status"],
		ignore_permissions=True,
	)
	logs = frappe.get_all(
		"Provisioning Stage Log",
		filters=tenant_filters,
		fields=["tenant", "stage", "status", "start_time", "duration_seconds"],
		order_by="creation desc",
		limit=10,
		ignore_permissions=True,
	)
	installed_apps = tenant.get("installed_apps", []) if tenant else []
	marketplace_apps = CatalogService.list_active_applications()
	limit_info = _current_site_limit(user)
	return {
		"tenant": tenant,
		"tenants": tenants,
		"subscription": subscription,
		"invoices": invoices,
		"payments": payments,
		"domains": domains,
		"deployment_logs": logs,
		"installed_apps": installed_apps,
		"marketplace_apps": marketplace_apps,
		"site_limit": limit_info,
		"account": {
			"user": user,
			"full_name": frappe.db.get_value("User", user, "full_name")},
		"stats": {
			"sites": len(tenants),
			"applications": len(installed_apps),
			"pending_invoices": len([invoice for invoice in invoices if invoice.status in {"Unpaid", "Overdue", "Draft"}]),
			"marketplace_apps": len(marketplace_apps)}
	}


@frappe.whitelist()
def install_application(app_slug: str, tenant: str | None = None):
	tenant_name = _get_customer_tenant(tenant=tenant)
	if not tenant_name:
		frappe.throw("Create a site before installing applications")
	tenant_doc = frappe.get_doc("SaaS Tenant", tenant_name)
	if tenant_doc.status != "Active" or not (tenant_doc.site_folder or tenant_doc.site_name):
		frappe.throw("Site must be active before installing applications")
	app_slug = normalize_app_entry(app_slug)
	if not app_slug:
		frappe.throw("Application is required")
	available = {app.get("app_slug") for app in CatalogService.list_active_applications()}
	is_core_bundle = app_slug == "core_bundle"
	if app_slug not in available and not is_core_bundle:
		frappe.throw("Application is not available")
	current = _latest_selected_apps(tenant_name)
	if not is_core_bundle and app_slug in current:
		return {"success": True, "message": "التطبيق مثبت بالفعل", "installed_apps": _application_details(current)
	}

	install_plan = list(CORE_PLATFORM_APPS) if "omnexa_core" not in current or is_core_bundle else []
	if not is_core_bundle and app_slug not in install_plan:
		install_plan.append(app_slug)
	install_plan = [app for index, app in enumerate(install_plan) if app and app not in install_plan[:index]]
	if not install_plan:
		return {"success": True, "message": "كل التطبيقات الأساسية مثبتة بالفعل", "installed_apps": _application_details(current)
	}

	site_folder = tenant_doc.site_folder or tenant_doc.site_name
	ProvisioningService.install_tenant_apps(site_folder, install_plan)
	ProvisioningService.migrate_site(site_folder)
	ProvisioningService.restore_tenant_desk(site_folder)
	apps = current + [app for app in install_plan if app not in current]
	request_name = frappe.db.get_value(
		"Provisioning Request",
		{"tenant": tenant_name
	},
		"name",
		order_by="creation desc",
	)
	if request_name:
		import json

		frappe.db.set_value(
			"Provisioning Request",
			request_name,
			"execution_log",
			json.dumps({"apps_to_install": apps, "installed_after_site_ready": True
	}, ensure_ascii=False),
			update_modified=False,
		)
	frappe.db.commit()
	return {"success": True, "message": "تم تثبيت التطبيقات المطلوبة بنجاح", "installed_apps": _application_details(apps)
	}


@frappe.whitelist()
def archive_site(tenant: str):
	tenant_name = _get_customer_tenant(tenant=tenant)
	if not tenant_name:
		frappe.throw("No tenant linked to this user")
	tenant_doc = frappe.get_doc("SaaS Tenant", tenant_name)
	cleanup = ProvisioningService.cleanup_failed_tenant(
		tenant_name,
		site_folder=tenant_doc.site_folder or tenant_doc.site_name,
		reason="Deleted by customer",
	)
	return {
		"success": cleanup.get("success"),
		"message": "تم حذف الموقع ومجلده وقاعدة بياناته بنجاح",
		"cleanup": cleanup
	}


@frappe.whitelist()
def get_site_credentials(tenant: str):
	tenant_name = _get_customer_tenant(tenant=tenant)
	if not tenant_name:
		frappe.throw("No tenant linked to this user")
	tenant_doc = frappe.get_doc("SaaS Tenant", tenant_name)
	password = ""
	try:
		from frappe.utils.password import get_decrypted_password

		password = get_decrypted_password("SaaS Tenant", tenant_name, "admin_password", raise_exception=False) or ""
	except Exception:
		password = tenant_doc.admin_password or ""
	return {
		"success": True,
		"tenant": tenant_name,
		"site_url": tenant_doc.access_url or tenant_doc.site_url,
		"username": tenant_doc.admin_username or "Administrator",
		"password": password,
		"note": "في وضع البورت على نفس IP، تسجيل الدخول لموقع العميل قد يخرجك من لوحة التحكم. افتحه في نافذة خاصة أو استخدم Subdomain."
	}


@frappe.whitelist(methods=["POST"])
def reset_site_admin_password(tenant: str):
	tenant_name = _get_customer_tenant(tenant=tenant)
	if not tenant_name:
		frappe.throw("No tenant linked to this user")
	tenant_doc = frappe.get_doc("SaaS Tenant", tenant_name)
	site_folder = tenant_doc.site_folder or tenant_doc.site_name
	if not site_folder:
		frappe.throw("Tenant site is not provisioned")
	password = PasswordManager().generate_password(length=16)
	if not ProvisioningService.set_admin_password(site_folder, password):
		frappe.throw("Failed to reset tenant Administrator password")
	frappe.db.set_value(
		"SaaS Tenant",
		tenant_name,
		{"admin_username": "Administrator", "admin_password": password
	},
		update_modified=False,
	)
	frappe.db.commit()
	return {
		"success": True,
		"tenant": tenant_name,
		"site_url": tenant_doc.access_url or tenant_doc.site_url,
		"username": "Administrator",
		"password": password,
		"message": "تمت إعادة ضبط كلمة مرور مدير الموقع ونسخها في لوحة التحكم."
	}


@frappe.whitelist(methods=["POST"])
def update_site_custom_fields(tenant: str, brand_name: str | None = None, custom_domain: str | None = None, notes: str | None = None):
	tenant_name = _get_customer_tenant(tenant=tenant)
	if not tenant_name:
		frappe.throw("No tenant linked to this user")
	doc = frappe.get_doc("SaaS Tenant", tenant_name)
	doc.brand_name = (brand_name or "").strip()
	doc.custom_domain = (custom_domain or "").strip()
	doc.notes = (notes or "").strip()
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"success": True, "message": "تم حفظ الحقول المخصصة", "custom_fields": _tenant_summary(tenant_name)["custom_fields"]
	}


@frappe.whitelist()
def restart_site_service(tenant: str | None = None):
	tenant_name = _get_customer_tenant(tenant=tenant)
	if not tenant_name:
		frappe.throw("No tenant linked to this user")
	return DeploymentService.restart_tenant_service(tenant_name)


@frappe.whitelist()
def get_site_logs(tail: int = 200, tenant: str | None = None):
	tenant_name = _get_customer_tenant(tenant=tenant)
	if not tenant_name:
		frappe.throw("No tenant linked to this user")
	return {"logs": DeploymentService.get_tenant_logs(tenant_name, tail=int(tail or 200))}


@frappe.whitelist()
def get_deployment_settings():
	config = get_deployment_config()
	return {
		"deployment_mode": config.deployment_mode,
		"site_distribution_method": config.deployment_mode,
		"start_port": config.start_port,
		"end_port": config.end_port,
		"server_host": config.server_host,
		"use_https": config.use_https,
		"root_domain": config.root_domain,
		"subdomain_pattern": config.subdomain_pattern
	}


@frappe.whitelist()
def get_tenants_for_cleanup(filters=None):
	"""Get tenants with optional filters for cleanup"""
	if frappe.session.user == "Guest":
		frappe.throw("Authentication required", frappe.PermissionError)
	
	# Check if user is System Manager
	if "System Manager" not in frappe.get_roles(frappe.session.user):
		frappe.throw("Only System Managers can access this function", frappe.PermissionError)
	
	filters = filters or {}
	
	# Build query
	query = frappe.db.get_list(
		"SaaS Tenant",
		fields=[
			"name",
			"site_folder",
			"site_name",
			"status",
			"creation",
			"access_url",
			"site_url",
			"subscription_status",
			"subscription_end_date"
		],
		filters=filters,
		order_by="creation desc"
	)
	
	return {"tenants": query
	}


@frappe.whitelist()
def bulk_delete_tenants(tenant_names, delete_folders=True):
	"""Bulk delete tenants with optional folder cleanup"""
	if frappe.session.user == "Guest":
		frappe.throw("Authentication required", frappe.PermissionError)
	
	# Check if user is System Manager
	if "System Manager" not in frappe.get_roles(frappe.session.user):
		frappe.throw("Only System Managers can access this function", frappe.PermissionError)
	
	if isinstance(tenant_names, str):
		import json
		try:
			tenant_names = json.loads(tenant_names)
		except Exception:
			tenant_names = [t.strip() for t in tenant_names.split(",")]
	
	if not tenant_names:
		frappe.throw("No tenants selected for deletion")
	
	results = {
		"success": [],
		"failed": [],
		"total": len(tenant_names)
	}
	
	for tenant_name in tenant_names:
		try:
			tenant_doc = frappe.get_doc("SaaS Tenant", tenant_name)
			
			# Delete site folders if requested
			if delete_folders:
				site_folder = tenant_doc.site_folder or tenant_doc.site_name
				if site_folder:
					try:
						DeploymentService.delete_tenant_site(site_folder)
					except Exception as e:
						frappe.logger("erpgenex_saas").warning(f"Failed to delete site folder {site_folder}: {str(e)}")
			
			# Delete tenant document
			tenant_doc.delete()
			results["success"].append(tenant_name)
			
		except Exception as e:
			results["failed"].append({
				"tenant": tenant_name,
				"error": str(e)
			})
			frappe.logger("erpgenex_saas").error(f"Failed to delete tenant {tenant_name}: {str(e)}")
	
	return results


@frappe.whitelist()
def register_and_subscribe(
	customer_name: str,
	company_email: str,
	password: str,
	plan: str,
	billing_cycle: str,
):
	return portal.register_customer(
		customer_name=customer_name,
		company_email=company_email,
		password=password,
		plan=plan,
		billing_cycle=billing_cycle,
	)
