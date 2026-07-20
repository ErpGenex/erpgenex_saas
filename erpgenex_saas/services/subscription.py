from __future__ import annotations

from datetime import timedelta

import frappe
from frappe.utils import today

from erpgenex_saas.services.license_manager import LicenseManager
from frappe.utils import add_days, add_months, getdate, now_datetime


class SubscriptionService:
	@staticmethod
	def compute_end_date(start_date, billing_cycle: str):
		start = getdate(start_date)
		if billing_cycle == "Monthly":
			return add_months(start, 1)
		if billing_cycle == "Quarterly":
			return add_months(start, 3)
		if billing_cycle == "Semi Annual":
			return add_months(start, 6)
		if billing_cycle == "Annual":
			return add_months(start, 12)
		if billing_cycle == "Trial":
			return add_days(start, 14)
		if billing_cycle == "Lifetime":
			return None
		frappe.throw(f"Unsupported billing cycle: {billing_cycle}")

	@staticmethod
	def mark_due_trials_and_grace_periods():
		today = now_datetime().date()
		for status in ("Trial", "Grace Period", "Active"):
			subscriptions = frappe.get_all(
				"SaaS Subscription",
				filters={"status": status, "ends_on": ("is", "set"), "docstatus": ("!=", 2)},
				fields=["name", "status", "ends_on", "tenant"],
			)
			for row in subscriptions:
				if row.ends_on and row.ends_on < today:
					doc = frappe.get_doc("SaaS Subscription", row.name)
					if row.status == "Active" and doc.grace_period_days:
						doc.status = "Grace Period"
						doc.ends_on = today + timedelta(days=int(doc.grace_period_days))
						doc.features_enabled = 1
						doc.disabled_reason = ""
					else:
						doc.status = "Expired"
						doc.features_enabled = 0
						doc.disabled_reason = "Subscription expired"
					doc.save(ignore_permissions=True)
					LicenseManager.sync_subscription_feature_state(doc.name)

	@staticmethod
	def pause(subscription_name: str, reason: str = ""):
		doc = frappe.get_doc("SaaS Subscription", subscription_name)
		if doc.status not in ("Active", "Trial", "Grace Period"):
			frappe.throw(f"Cannot pause subscription in status: {doc.status}")
		doc.status = "Paused"
		doc.features_enabled = 0
		doc.disabled_reason = reason or "Subscription paused"
		if reason:
			doc.add_comment("Comment", f"Paused: {reason}")
		doc.save(ignore_permissions=True)
		LicenseManager.sync_subscription_feature_state(doc.name)
		return doc

	@staticmethod
	def resume(subscription_name: str):
		doc = frappe.get_doc("SaaS Subscription", subscription_name)
		if doc.status != "Paused":
			frappe.throw(f"Cannot resume subscription in status: {doc.status
	}")
		doc.status = "Active"
		doc.features_enabled = 1
		doc.disabled_reason = ""
		doc.save(ignore_permissions=True)
		LicenseManager.sync_subscription_feature_state(doc.name)
		return doc

	@staticmethod
	def cancel(subscription_name: str, reason: str = ""):
		doc = frappe.get_doc("SaaS Subscription", subscription_name)
		if doc.status == "Cancelled":
			return doc
		doc.status = "Cancelled"
		doc.features_enabled = 0
		doc.disabled_reason = reason or "Subscription cancelled"
		if reason:
			doc.add_comment("Comment", f"Cancelled: {reason}")
		doc.save(ignore_permissions=True)
		tenant = frappe.get_doc("SaaS Tenant", doc.tenant)
		if tenant.status == "Active":
			tenant.status = "Suspended"
			tenant.save(ignore_permissions=True)
		LicenseManager.sync_subscription_feature_state(doc.name)
		return doc

	@staticmethod
	def subscribe_to_application(tenant: str, application: str, billing_cycle: str = "Monthly"):
		app = frappe.get_doc("SaaS Application", application)
		if app.is_core or app.distribution_type == "Core Free":
			frappe.throw("Core applications are free and do not require a paid subscription")
		plan = frappe.db.get_value("SaaS Plan", {"plan_tier": "Free", "billing_cycle": billing_cycle, "is_active": 1
	}, "name")
		if not plan:
			plan = frappe.db.get_value("SaaS Plan", {"billing_cycle": billing_cycle, "is_active": 1
	}, "name")
		if not plan:
			frappe.throw(f"No active {billing_cycle} plan found")
		start = today()
		subscription = frappe.get_doc(
			{
				"doctype": "SaaS Subscription",
				"tenant": tenant,
				"plan": plan,
				"application": application,
				"billing_cycle": billing_cycle,
				"status": "Trial" if app.trial_days else "Active",
				"starts_on": start,
				"ends_on": add_days(start, int(app.trial_days)) if app.trial_days else SubscriptionService.compute_end_date(start, billing_cycle),
				"trial_ends_on": add_days(start, int(app.trial_days)) if app.trial_days else None,
				"apps_amount": app.annual_price if billing_cycle == "Annual" else app.monthly_price,
				"features_enabled": 1
	}
		)
		subscription.insert(ignore_permissions=True)
		LicenseManager.ensure_subscription_license(subscription.name)
		return subscription
