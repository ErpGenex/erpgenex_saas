from __future__ import annotations

import frappe

from erpgenex_saas.services import BillingService, CatalogService, PaymentService, PricingService
from erpgenex_saas.services.audit import AuditService
from erpgenex_saas.services.notification import NotificationService


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
def create_tenant_and_subscription(customer_name: str, company_email: str, plan: str, billing_cycle: str):
	plan_doc = frappe.get_doc("SaaS Plan", plan)
	tenant = frappe.get_doc(
		{
			"doctype": "SaaS Tenant",
			"tenant_name": customer_name,
			"company_email": company_email,
			"status": "Draft",
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
		}
	)
	subscription.insert(ignore_permissions=True)

	request = frappe.get_doc(
		{
			"doctype": "Provisioning Request",
			"tenant": tenant.name,
			"subscription": subscription.name,
			"status": "Queued",
			"request_type": "Initial Provisioning",
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
	return CatalogService.list_active_applications()


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
	return {"package": doc.name}


@frappe.whitelist()
def register_invoice_payment(invoice: str, provider: str, transaction_id: str, amount: float, payload=None):
	verification = PaymentService.verify_webhook(provider=provider, payload=payload or {}, signature=None)
	payment = BillingService.register_payment(
		invoice_name=invoice,
		amount=amount,
		provider=provider,
		transaction_id=transaction_id,
	)
	tenant = frappe.db.get_value("SaaS Invoice", invoice, "tenant")
	if tenant:
		NotificationService.notify(
			tenant,
			"payment",
			"Payment received",
			f"Payment {payment.name} registered via {provider}.",
		)
		AuditService.log("payment.registered", payment.name, {"invoice": invoice, "provider": provider})
	return {"payment": payment.name, "verification": verification}


@frappe.whitelist(allow_guest=True)
def register_customer(
	customer_name: str,
	company_email: str,
	password: str,
	plan: str,
	billing_cycle: str,
):
	from erpgenex_saas.bootstrap import ensure_roles

	ensure_roles()
	if not frappe.db.exists("User", company_email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": company_email,
				"first_name": customer_name,
				"send_welcome_email": 0,
				"user_type": "Website User",
				"new_password": password,
				"roles": [{"role": "SaaS Customer"}],
			}
		)
		user.insert(ignore_permissions=True)
	else:
		user = frappe.get_doc("User", company_email)
		if "SaaS Customer" not in frappe.get_roles(user.name):
			user.add_roles("SaaS Customer")

	result = create_tenant_and_subscription(customer_name, company_email, plan, billing_cycle)
	if not frappe.db.exists("SaaS Customer Account", user.name):
		frappe.get_doc(
			{
				"doctype": "SaaS Customer Account",
				"user": user.name,
				"tenant": result["tenant"],
				"is_primary_contact": 1,
			}
		).insert(ignore_permissions=True)

	subdomain = customer_name.lower().replace(" ", "-")
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
