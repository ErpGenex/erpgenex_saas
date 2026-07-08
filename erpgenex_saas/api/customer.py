from __future__ import annotations

import frappe

from erpgenex_saas.api import portal


def _get_customer_tenant(user: str | None = None):
	user = user or frappe.session.user
	if user == "Guest":
		frappe.throw("Login required", frappe.PermissionError)
	return frappe.db.get_value("SaaS Customer Account", {"user": user}, "tenant")


@frappe.whitelist()
def get_dashboard():
	tenant_name = _get_customer_tenant()
	if not tenant_name:
		frappe.throw("No tenant linked to this user")
	tenant = frappe.get_doc("SaaS Tenant", tenant_name)
	subscription = tenant.active_subscription and frappe.get_doc("SaaS Subscription", tenant.active_subscription)
	invoices = frappe.get_all(
		"SaaS Invoice",
		filters={"tenant": tenant_name},
		fields=["name", "status", "amount_due", "paid_amount", "invoice_date"],
		order_by="creation desc",
		limit=10,
	)
	payments = frappe.get_all(
		"SaaS Payment",
		filters={"tenant": tenant_name},
		fields=["name", "provider", "amount", "status", "creation"],
		order_by="creation desc",
		limit=10,
	)
	domains = frappe.get_all(
		"SaaS Domain",
		filters={"tenant": tenant_name},
		fields=["name", "domain_name", "status", "ssl_status"],
	)
	return {
		"tenant": tenant.as_dict(),
		"subscription": subscription.as_dict() if subscription else None,
		"invoices": invoices,
		"payments": payments,
		"domains": domains,
	}


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
