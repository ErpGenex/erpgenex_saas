from __future__ import annotations

import frappe

from erpgenex_saas.services import BillingService, CatalogService, LicenseManager, PaymentService, PricingService, ApplicationDistributionService
from erpgenex_saas.services.activity_bundles import get_user_business_activity
from erpgenex_saas.services.subscription import SubscriptionService
from erpgenex_saas.services.applications_portal import (
	get_applications_portal_state as build_applications_portal_state,
	reveal_license_key,
)
from erpgenex_saas.services.subscription_fulfillment import SubscriptionFulfillmentService
from erpgenex_saas.services.audit import AuditService
from erpgenex_saas.services.notification import NotificationService
from erpgenex_saas.constants import PRICING_TIERS


@frappe.whitelist(allow_guest=True)
def get_marketing_context():
	"""Public SaaS marketing payload for Next.js light sites."""
	db_plans = frappe.get_all(
		"SaaS Plan",
		filters={"is_active": 1},
		fields=["name", "plan_name", "base_price", "billing_cycle", "max_sites", "description"],
		order_by="base_price asc",
	)
	tiers = []
	if db_plans:
		for plan in db_plans:
			name = plan.plan_name or plan.name
			monthly = float(plan.base_price or 0)
			tiers.append(
				{
					"slug": (name or "").lower().replace(" ", "-"),
					"name": name.replace(" Monthly", "").strip(),
					"plan": plan.name,
					"monthly": monthly,
					"yearly": round(monthly * 12 * 0.8, 2) if monthly else 0,
					"featured": "professional" in (name or "").lower() or "business" in (name or "").lower(),
					"description": plan.description or "",
					"max_sites": plan.max_sites,
				}
			)
	else:
		for tier in PRICING_TIERS:
			tiers.append(
				{
					"slug": tier.get("slug") or tier.get("name", "").lower().replace(" ", "-"),
					"name": tier.get("name"),
					"plan": tier.get("plan"),
					"monthly": tier.get("monthly") or tier.get("price") or 0,
					"yearly": tier.get("yearly") or 0,
					"featured": bool(tier.get("featured")),
					"description": "",
					"features": tier.get("features") or [],
				}
			)

	app_count = 0
	try:
		app_count = len(CatalogService.list_marketplace_applications() or [])
	except Exception:
		app_count = 50

	return {
		"brand_name_en": "ERPGenex SaaS",
		"brand_name_ar": "ERPGenex SaaS",
		"tagline_en": "Enterprise multi-tenant ERP — register, provision, and grow",
		"tagline_ar": "منصة ERP متعددة المستأجرين — سجّل، جهّز، وتوسّع",
		"hero_text_en": "Plans, billing, app marketplace, and a live customer dashboard.",
		"hero_text_ar": "باقات، فوترة، سوق تطبيقات، ولوحة عميل مباشرة.",
		"tiers": tiers,
		"stats": {
			"modules": app_count or 50,
			"verticals": 15,
			"uptime": "99.9%",
			"support": "24/7",
		},
		"features": [
			{"icon": "🏢", "title_en": "Multi-Branch", "title_ar": "فروع متعددة", "desc_en": "Assets, sectors, activities", "desc_ar": "أصول وقطاعات وأنشطة"},
			{"icon": "⚖️", "title_en": "Vertical Packs", "title_ar": "حزم قطاعية", "desc_en": "Legal, healthcare, tourism & more", "desc_ar": "قانون ورعاية وصحية وسياحة والمزيد"},
			{"icon": "🔐", "title_en": "Enterprise Security", "title_ar": "أمن مؤسسي", "desc_en": "Roles, audit, compliance", "desc_ar": "أدوار وتدقيق وامتثال"},
			{"icon": "🤖", "title_en": "AI Ready", "title_ar": "جاهز للذكاء", "desc_en": "Intelligence core integration", "desc_ar": "تكامل نواة الذكاء"},
			{"icon": "📱", "title_en": "Customer Portals", "title_ar": "بوابات العملاء", "desc_en": "Full tools for every client", "desc_ar": "أدوات كاملة لكل عميل"},
			{"icon": "📊", "title_en": "Live Dashboards", "title_ar": "لوحات حية", "desc_en": "KPIs and operational boards", "desc_ar": "مؤشرات ولوحات تشغيل"},
		],
		"links": {
			"register": "/saas/register",
			"dashboard": "/saas/dashboard",
			"pricing": "/saas/pricing",
			"applications": "/saas/applications",
			"login": "/login?redirect-to=/saas/dashboard",
		},
	}


@frappe.whitelist()
def get_subscription_quote(
	base_amount: float,
	apps_amount: float = 0,
	extra_users_amount: float = 0,
	extra_storage_amount: float = 0,
	extra_services_amount: float = 0,
):
	breakdown = PricingService.calculate(
		base_amount=base_amount,
		apps_amount=apps_amount,
		extra_users_amount=extra_users_amount,
		extra_storage_amount=extra_storage_amount,
		extra_services_amount=extra_services_amount,
	)
	return breakdown.__dict__


@frappe.whitelist()
def create_tenant_and_subscription(
	customer_name: str,
	company_email: str,
	plan: str,
	billing_cycle: str,
	extra_users: int = 0,
	extra_storage_gb: float = 0,
):
	plan_doc = frappe.get_doc("SaaS Plan", plan)
	settings = frappe.get_single("SaaS Settings")
	extra_users = int(extra_users or 0)
	extra_storage_gb = float(extra_storage_gb or 0)
	extra_users_amount = extra_users * float(settings.extra_user_price or 0)
	extra_storage_amount = extra_storage_gb * float(settings.extra_storage_price_per_gb or 0)
	tenant = frappe.get_doc(
		{
			"doctype": "SaaS Tenant",
			"tenant_name": customer_name,
			"company_email": company_email,
			"status": "Draft"
	}
	)
	tenant.insert(ignore_permissions=True)

	subscription = frappe.get_doc(
		{
			"doctype": "SaaS Subscription",
			"tenant": tenant.name,
			"plan": plan,
			"billing_cycle": billing_cycle,
			"status": "Draft",
			"starts_on": frappe.utils.today(),
			"base_amount": plan_doc.base_price,
			"extra_users_amount": extra_users_amount,
			"extra_storage_amount": extra_storage_amount,
			"total_amount": float(plan_doc.base_price or 0) + extra_users_amount + extra_storage_amount,
	}
	)
	subscription.insert(ignore_permissions=True)

	request = frappe.get_doc(
		{
			"doctype": "Provisioning Request",
			"tenant": tenant.name,
			"subscription": subscription.name,
			"status": "Queued",
			"request_type": "Initial Provisioning"
	}
	)
	request.insert(ignore_permissions=True)
	subscription.provisioning_request = request.name
	subscription.save(ignore_permissions=True)
	invoice = BillingService.create_invoice_for_subscription(subscription.name)
	return {
		"tenant": tenant.name,
		"subscription": subscription.name,
		"provisioning_request": request.name,
		"invoice": invoice.name,
	}


@frappe.whitelist()
def list_marketplace_applications():
	return CatalogService.list_marketplace_applications()


@frappe.whitelist(allow_guest=True)
def get_applications_portal_state():
	return build_applications_portal_state()


@frappe.whitelist()
def reveal_application_license_key(tenant: str, application: str):
	return reveal_license_key(tenant, application)


@frappe.whitelist()
def list_application_updates():
	return CatalogService.list_updates(get_user_business_activity())


@frappe.whitelist()
def subscribe_to_application(tenant: str, application: str, billing_cycle: str = "Monthly"):
	subscription = SubscriptionService.subscribe_to_application(tenant, application, billing_cycle)
	invoice = BillingService.create_invoice_for_subscription(subscription.name)
	AuditService.log("application.subscribed", application, {"tenant": tenant, "subscription": subscription.name})
	return {
		"subscription": subscription.name,
		"invoice": invoice.name,
		"amount_due": float(invoice.amount_due or 0),
		"billing_cycle": billing_cycle,
		"status": subscription.status,
		"license_key": None,
		"message": "Complete payment to generate the activation key and enable installation.",
	}


@frappe.whitelist()
def is_application_enabled(tenant: str, application: str):
	return {"enabled": LicenseManager.is_application_enabled(tenant, application)}


@frappe.whitelist()
def buy_source_code(application: str, customer_email: str, tenant: str | None = None):
	purchase = LicenseManager.create_source_purchase(tenant=tenant, customer_email=customer_email, application=application)
	invoice = BillingService.create_invoice_for_source_purchase(purchase.name)
	AuditService.log("source.purchase.created", purchase.name, {"application": application, "tenant": tenant})
	return {
		"source_purchase": purchase.name,
		"invoice": invoice.name,
		"amount_due": float(invoice.amount_due or 0),
		"customer_email": purchase.customer_email,
	}


@frappe.whitelist()
def fulfill_source_purchase(source_purchase: str, grant_github_access: int = 0, github_username: str | None = None):
	purchase = LicenseManager.fulfill_source_purchase(source_purchase, bool(int(grant_github_access or 0)), github_username)
	link = LicenseManager.create_download_link(purchase.name)
	AuditService.log("source.purchase.fulfilled", purchase.name, {"download_link": link.get("download_link")})
	return {"source_purchase": purchase.name,
		**link}


@frappe.whitelist()
def download_source_code(token: str):
	"""Download purchased application source via server-side GitHub token."""
	from erpgenex_saas.services.github_distribution import stream_application_source_archive

	verification = LicenseManager.verify_download_token(token)
	AuditService.log(
		"source.download.started",
		verification["download_link"],
		{"application": verification["application"]},
	)
	stream_application_source_archive(verification["application"])


@frappe.whitelist()
def revoke_source_download_link(download_link: str):
	doc = LicenseManager.revoke_download_link(download_link)
	AuditService.log("source.download.revoked", doc.name, {"application": doc.application})
	return {"download_link": doc.name,
		"status": doc.status
	}


@frappe.whitelist()
def install_application(tenant: str, application: str):
	if frappe.session.user not in ("Guest", "Administrator") and "System Manager" not in frappe.get_roles():
		from erpgenex_saas.api.customer import _get_customer_tenant

		tenant = _get_customer_tenant(tenant=tenant) or tenant
	return ApplicationDistributionService.install_application(tenant, application)


@frappe.whitelist()
def update_application(tenant: str, application: str):
	return ApplicationDistributionService.update_application(tenant, application)


@frappe.whitelist()
def create_package(package_name: str, base_plan: str, support_level: str = "Business"):
	doc = frappe.get_doc(
		{
			"doctype": "SaaS Package",
			"package_name": package_name,
			"base_plan": base_plan,
			"support_level": support_level,
			"is_active": 1,
	}
	)
	doc.insert(ignore_permissions=True)
	return {"package": doc.name
	}


@frappe.whitelist()
def register_invoice_payment(invoice: str, provider: str, transaction_id: str, amount: float, payload=None):
	verification = PaymentService.verify_webhook(provider=provider, payload=payload or {}, signature=None)
	paypal_account = PaymentService.get_paypal_account()
	if not paypal_account["enabled"]:
		frappe.throw("PayPal payments are disabled")
	if not paypal_account["business_email"]:
		frappe.throw("PayPal Business Email is not configured")
	if provider != "PayPal":
		frappe.throw("Only PayPal payments are accepted")
	payment = BillingService.register_payment(
		invoice_name=invoice,
		amount=amount,
		provider=provider,
		transaction_id=transaction_id,
	)
	for purchase_name in frappe.get_all("SaaS Source Purchase", filters={"invoice": invoice, "status": "Pending Payment"}, pluck="name"):
		purchase = frappe.get_doc("SaaS Source Purchase", purchase_name)
		purchase.status = "Paid"
		purchase.save(ignore_permissions=True)

	fulfillment = SubscriptionFulfillmentService.activate_paid_invoice(invoice)
	tenant = frappe.db.get_value("SaaS Invoice", invoice, "tenant")
	if tenant:
		NotificationService.notify(
			tenant,
			"payment",
			"Payment received",
			f"Payment {payment.name} registered via {provider} to {paypal_account['business_email']}.",
		)
		AuditService.log("payment.registered", payment.name, {"invoice": invoice, "provider": provider})
	return {
		"payment": payment.name,
		"verification": verification,
		"paypal_account": paypal_account,
		"fulfillment": fulfillment,
		"license_key": fulfillment.get("license_key"),
		"invoice": invoice,
	}


def _is_valid_company_email(company_email: str) -> bool:
	import re

	return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', company_email or ''))


@frappe.whitelist(allow_guest=True)
def register_customer(
	customer_name: str,
	company_email: str,
	password: str,
	plan: str,
	billing_cycle: str,
	extra_users: int = 0,
	extra_storage_gb: float = 0,
):
	import re
	from erpgenex_saas.bootstrap import ensure_roles
	from erpgenex_saas.services.password_manager import PasswordManager

	# Input validation and sanitization
	if not customer_name or len(customer_name.strip()) < 2:
		return {"success": False,
			"error": "Customer name must be at least 2 characters"
	}
	
	if not _is_valid_company_email(company_email):
		return {"success": False,
			"error": "Invalid email format"
	}
	
	# Password strength validation
	password_manager = PasswordManager()
	password_validation = password_manager.validate_password_strength(password)
	if not password_validation["valid"]:
		return {"success": False,
			"error": ", ".join(password_validation["errors"])}

	ensure_roles()
	if not frappe.db.exists("User", company_email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": company_email,
				"first_name": customer_name[:100],  # Limit length
				"send_welcome_email": 0,
				"user_type": "Website User",
				"new_password": password,
				"roles": [{"role": "SaaS Customer"}]}
		)
		user.insert(ignore_permissions=True)
	else:
		user = frappe.get_doc("User", company_email)
		if "SaaS Customer" not in frappe.get_roles(user.name):
			user.add_roles("SaaS Customer")

	result = create_tenant_and_subscription(
		customer_name,
		company_email,
		plan,
		billing_cycle,
		extra_users=extra_users,
		extra_storage_gb=extra_storage_gb,
	)
	if not frappe.db.exists("SaaS Customer Account", user.name):
		frappe.get_doc(
			{
				"doctype": "SaaS Customer Account",
				"user": user.name,
				"tenant": result["tenant"],
				"is_primary_contact": 1
	}
		).insert(ignore_permissions=True)

	# Sanitize subdomain
	subdomain = re.sub(r'[^a-zA-Z0-9-]', '-', customer_name.lower()).strip('-')
	subdomain = subdomain[:50]  # Limit length
	frappe.db.set_value("SaaS Tenant", result["tenant"], "subdomain", subdomain)
	NotificationService.notify(
		result["tenant"],
		"registration",
		"Welcome to ERPGenex SaaS",
		f"Your tenant {result['tenant']} has been created.",
	)
	AuditService.log("customer.registered", result["tenant"], {"email": company_email, "plan": plan})

	from frappe.auth import LoginManager

	login_manager = LoginManager()
	login_manager.login_as(user.name)

	return result


def __getattr__(name: str):
	if name == "get_applications_portal_state":
		return build_applications_portal_state
	if name == "reveal_application_license_key":
		return reveal_license_key
	raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
