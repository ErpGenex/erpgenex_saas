from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

import frappe
from frappe.utils import get_datetime, now_datetime, nowdate


ACTIVE_LICENSE_STATUSES = ("Trial", "Active")
SOURCE_LICENSE_TYPE = "Lifetime Source Code License"
SAAS_LICENSE_TYPE = "SaaS Subscription License"
TRIAL_LICENSE_TYPE = "Trial License"
ENTERPRISE_LICENSE_TYPE = "Enterprise License"


class LicenseManager:
	@staticmethod
	def _hash_token(token: str) -> str:
		return hashlib.sha256(token.encode("utf-8")).hexdigest()

	@staticmethod
	def _new_license_key() -> str:
		return f"EGX-{secrets.token_urlsafe(24).replace('-', '').replace('_', '')[:28].upper()}"

	@staticmethod
	def _license_status_for_subscription(status: str) -> str:
		if status in ("Trial", "Active", "Grace Period"):
			return "Active" if status == "Grace Period" else status
		if status == "Expired":
			return "Expired"
		if status == "Cancelled":
			return "Revoked"
		if status in ("Paused", "Draft"):
			return "Suspended"
		return "Suspended"

	@staticmethod
	def create_license(
		application: str,
		license_type: str,
		status: str = "Active",
		tenant: str | None = None,
		customer: str | None = None,
		subscription: str | None = None,
		source_purchase: str | None = None,
		starts_on: str | None = None,
		ends_on: str | None = None,
	):
		doc = frappe.get_doc(
			{
				"doctype": "SaaS License",
				"application": application,
				"license_type": license_type,
				"status": status,
				"tenant": tenant,
				"customer": customer,
				"subscription": subscription,
				"source_purchase": source_purchase,
				"starts_on": starts_on or nowdate(),
				"ends_on": ends_on,
				"features_enabled": 1 if status in ACTIVE_LICENSE_STATUSES else 0,
				"license_key": LicenseManager._new_license_key(),
			}
		)
		doc.insert(ignore_permissions=True)
		return doc

	@staticmethod
	def ensure_subscription_license(subscription_name: str):
		sub = frappe.get_doc("SaaS Subscription", subscription_name)
		if not sub.application:
			return None
		existing = frappe.db.get_value(
			"SaaS License",
			{"subscription": sub.name, "application": sub.application, "license_type": ("in", [SAAS_LICENSE_TYPE, TRIAL_LICENSE_TYPE])},
			"name",
		)
		license_type = TRIAL_LICENSE_TYPE if sub.status == "Trial" or sub.billing_cycle == "Trial" else SAAS_LICENSE_TYPE
		if existing:
			lic = frappe.get_doc("SaaS License", existing)
			lic.status = "Trial" if license_type == TRIAL_LICENSE_TYPE else LicenseManager._license_status_for_subscription(sub.status)
			lic.license_type = license_type
			lic.starts_on = sub.starts_on
			lic.ends_on = sub.ends_on
			lic.features_enabled = 1 if lic.status in ACTIVE_LICENSE_STATUSES or lic.status == "Grace Period" else 0
			lic.save(ignore_permissions=True)
			return lic
		return LicenseManager.create_license(
			application=sub.application,
			license_type=license_type,
			status="Trial" if license_type == TRIAL_LICENSE_TYPE else LicenseManager._license_status_for_subscription(sub.status),
			tenant=sub.tenant,
			subscription=sub.name,
			starts_on=sub.starts_on,
			ends_on=sub.ends_on,
		)

	@staticmethod
	def sync_subscription_feature_state(subscription_name: str):
		sub = frappe.get_doc("SaaS Subscription", subscription_name)
		enabled = sub.status in ("Trial", "Active", "Grace Period")
		reason = "" if enabled else f"Subscription {sub.status}"
		if getattr(sub, "features_enabled", None) != int(enabled):
			sub.features_enabled = int(enabled)
			sub.disabled_reason = reason
			sub.save(ignore_permissions=True)

		for name in frappe.get_all("SaaS License", filters={"subscription": subscription_name}, pluck="name"):
			lic = frappe.get_doc("SaaS License", name)
			lic.status = LicenseManager._license_status_for_subscription(sub.status)
			lic.features_enabled = int(enabled)
			lic.ends_on = sub.ends_on
			lic.save(ignore_permissions=True)
		return {"subscription": subscription_name, "features_enabled": enabled, "reason": reason}

	@staticmethod
	def is_application_enabled(tenant: str, application: str) -> bool:
		app = frappe.get_doc("SaaS Application", application)
		if app.is_core or app.distribution_type == "Core Free":
			return True
		return bool(
			frappe.db.exists(
				"SaaS License",
				{
					"tenant": tenant,
					"application": application,
					"status": ("in", ACTIVE_LICENSE_STATUSES),
					"features_enabled": 1,
				},
			)
		)

	@staticmethod
	def create_source_purchase(tenant: str | None, customer_email: str, application: str):
		app = frappe.get_doc("SaaS Application", application)
		if not app.source_code_available:
			frappe.throw("Source code purchase is not available for this application")
		purchase = frappe.get_doc(
			{
				"doctype": "SaaS Source Purchase",
				"tenant": tenant,
				"customer_email": customer_email,
				"application": application,
				"status": "Pending Payment",
				"purchase_date": now_datetime(),
				"amount": app.source_code_price or 0,
				"currency": "USD",
			}
		)
		purchase.insert(ignore_permissions=True)
		return purchase

	@staticmethod
	def fulfill_source_purchase(source_purchase: str, grant_github_access: bool = False, github_username: str | None = None):
		purchase = frappe.get_doc("SaaS Source Purchase", source_purchase)
		if purchase.status not in ("Paid", "Fulfilled"):
			frappe.throw("Source purchase must be paid before fulfillment")
		license_name = purchase.license
		if not license_name:
			lic = LicenseManager.create_license(
				application=purchase.application,
				license_type=SOURCE_LICENSE_TYPE,
				status="Active",
				tenant=purchase.tenant,
				customer=purchase.customer_email,
				source_purchase=purchase.name,
			)
			purchase.license = lic.name
		purchase.status = "Fulfilled"
		purchase.github_access_granted = int(bool(grant_github_access))
		if github_username:
			purchase.github_username = github_username
		purchase.save(ignore_permissions=True)
		return purchase

	@staticmethod
	def create_download_link(source_purchase: str, expires_in_hours: int | None = None):
		purchase = frappe.get_doc("SaaS Source Purchase", source_purchase)
		if purchase.status != "Fulfilled":
			frappe.throw("Source purchase must be fulfilled before creating a download link")
		settings = frappe.get_single("SaaS Settings")
		hours = int(expires_in_hours or settings.default_download_expiry_hours or 24)
		token = secrets.token_urlsafe(32)
		expires_on = now_datetime() + timedelta(hours=hours)
		doc = frappe.get_doc(
			{
				"doctype": "SaaS Source Download Link",
				"source_purchase": purchase.name,
				"application": purchase.application,
				"status": "Active",
				"token_hash": LicenseManager._hash_token(token),
				"expires_on": expires_on,
			}
		)
		doc.insert(ignore_permissions=True)
		doc.download_url = f"/api/method/erpgenex_saas.api.portal.download_source_code?token={token}"
		doc.save(ignore_permissions=True)
		return {"download_link": doc.name, "download_url": doc.download_url, "expires_on": doc.expires_on}

	@staticmethod
	def verify_download_token(token: str):
		token_hash = LicenseManager._hash_token(token)
		name = frappe.db.get_value("SaaS Source Download Link", {"token_hash": token_hash}, "name")
		if not name:
			frappe.throw("Invalid download link")
		doc = frappe.get_doc("SaaS Source Download Link", name)
		if doc.status != "Active":
			frappe.throw("Download link is not active")
		if get_datetime(doc.expires_on) < now_datetime():
			doc.status = "Expired"
			doc.save(ignore_permissions=True)
			frappe.throw("Download link has expired")
		purchase = frappe.get_doc("SaaS Source Purchase", doc.source_purchase)
		if purchase.status != "Fulfilled":
			frappe.throw("Source purchase is not fulfilled")
		doc.download_count = int(doc.download_count or 0) + 1
		doc.last_downloaded_on = now_datetime()
		doc.last_downloaded_by = frappe.session.user
		doc.save(ignore_permissions=True)
		return {"application": doc.application, "source_purchase": purchase.name, "download_link": doc.name}

	@staticmethod
	def revoke_download_link(download_link: str):
		doc = frappe.get_doc("SaaS Source Download Link", download_link)
		doc.status = "Revoked"
		doc.revoked_on = now_datetime()
		doc.save(ignore_permissions=True)
		return doc

	@staticmethod
	def expire_due_licenses():
		today = nowdate()
		for name in frappe.get_all("SaaS License", filters={"ends_on": ("<", today), "status": ("in", ["Trial", "Active"])}, pluck="name"):
			doc = frappe.get_doc("SaaS License", name)
			doc.status = "Expired"
			doc.features_enabled = 0
			doc.save(ignore_permissions=True)
