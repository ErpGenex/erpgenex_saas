from __future__ import annotations

from datetime import timedelta

import frappe
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
					else:
						doc.status = "Expired"
					doc.save(ignore_permissions=True)

	@staticmethod
	def pause(subscription_name: str, reason: str = ""):
		doc = frappe.get_doc("SaaS Subscription", subscription_name)
		if doc.status not in ("Active", "Trial", "Grace Period"):
			frappe.throw(f"Cannot pause subscription in status: {doc.status}")
		doc.status = "Paused"
		if reason:
			doc.add_comment("Comment", f"Paused: {reason}")
		doc.save(ignore_permissions=True)
		return doc

	@staticmethod
	def resume(subscription_name: str):
		doc = frappe.get_doc("SaaS Subscription", subscription_name)
		if doc.status != "Paused":
			frappe.throw(f"Cannot resume subscription in status: {doc.status}")
		doc.status = "Active"
		doc.save(ignore_permissions=True)
		return doc

	@staticmethod
	def cancel(subscription_name: str, reason: str = ""):
		doc = frappe.get_doc("SaaS Subscription", subscription_name)
		if doc.status == "Cancelled":
			return doc
		doc.status = "Cancelled"
		if reason:
			doc.add_comment("Comment", f"Cancelled: {reason}")
		doc.save(ignore_permissions=True)
		tenant = frappe.get_doc("SaaS Tenant", doc.tenant)
		if tenant.status == "Active":
			tenant.status = "Suspended"
			tenant.save(ignore_permissions=True)
		return doc
