from __future__ import annotations

import frappe

from erpgenex_saas.bootstrap import ensure_default_plans, ensure_roles
from erpgenex_saas.services.billing import BillingService


def ensure_customer_user(
	email: str,
	full_name: str,
	password: str,
	tenant_name: str,
) -> str:
	ensure_roles()
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": full_name,
				"send_welcome_email": 0,
				"user_type": "Website User",
				"new_password": password,
				"roles": [{"role": "SaaS Customer"}]
	}
		)
		user.insert(ignore_permissions=True)
	else:
		user = frappe.get_doc("User", email)
		if "SaaS Customer" not in frappe.get_roles(user.name):
			user.add_roles("SaaS Customer")

	if not frappe.db.exists("SaaS Customer Account", email):
		frappe.get_doc(
			{
				"doctype": "SaaS Customer Account",
				"user": email,
				"tenant": tenant_name,
				"is_primary_contact": 1
	}
		).insert(ignore_permissions=True)

	return email


def ensure_trial_subscription(tenant_name: str, company_email: str) -> dict:
	ensure_default_plans()
	plan = frappe.db.get_value(
		"SaaS Plan",
		{"is_active": 1
	},
		"name",
		order_by="base_price asc",
	)
	if not plan:
		frappe.throw("No active SaaS Plan found")

	if frappe.db.exists("SaaS Subscription", {"tenant": tenant_name, "status": ("!=", "Cancelled")}):
		sub_name = frappe.db.get_value(
			"SaaS Subscription",
			{"tenant": tenant_name
	},
			"name",
			order_by="creation desc",
		)
		return {"subscription": sub_name, "created": False
	}

	subscription = frappe.get_doc(
		{
			"doctype": "SaaS Subscription",
			"tenant": tenant_name,
			"plan": plan,
			"billing_cycle": "Trial",
			"status": "Draft",
			"starts_on": frappe.utils.today(),
			"base_amount": frappe.db.get_value("SaaS Plan", plan, "base_price") or 0}
	)
	subscription.insert(ignore_permissions=True)
	invoice = BillingService.create_invoice_for_subscription(subscription.name)
	frappe.db.set_value("SaaS Tenant", tenant_name, "company_email", company_email, update_modified=False)
	return {
		"subscription": subscription.name,
		"invoice": invoice.name,
		"created": True
	}


def link_subscription_to_provisioning(tenant_name: str, provisioning_request: str):
	sub_name = frappe.db.get_value(
		"SaaS Subscription",
		{"tenant": tenant_name
	},
		"name",
		order_by="creation desc",
	)
	if not sub_name:
		return
	frappe.db.set_value("SaaS Subscription", sub_name, "provisioning_request", provisioning_request)
	frappe.db.set_value("SaaS Tenant", tenant_name, "active_subscription", sub_name, update_modified=False)
