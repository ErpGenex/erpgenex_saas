from __future__ import annotations

import frappe
from frappe.utils import today

from erpgenex_saas.services.license_manager import LicenseManager
from erpgenex_saas.services.subscription import SubscriptionService


class SubscriptionFulfillmentService:
	"""Activate subscriptions, licenses, and tenant sites after successful payment."""

	@staticmethod
	def activate_paid_invoice(invoice_name: str) -> dict:
		invoice = frappe.get_doc("SaaS Invoice", invoice_name)
		if invoice.status not in ("Paid", "Partially Paid"):
			return {"activated": False, "reason": "invoice_not_paid"}

		result: dict = {"activated": True, "invoice": invoice.name, "tenant": invoice.tenant}

		if invoice.subscription:
			result.update(SubscriptionFulfillmentService._activate_application_subscription(invoice.subscription))

		source_purchases = frappe.get_all(
			"SaaS Source Purchase",
			filters={"invoice": invoice.name, "status": ("in", ["Paid", "Pending Payment"])},
			pluck="name",
		)
		if source_purchases:
			result["source_purchases"] = [
				SubscriptionFulfillmentService._activate_source_purchase(name) for name in source_purchases
			]

		return result

	@staticmethod
	def _activate_application_subscription(subscription_name: str) -> dict:
		sub = frappe.get_doc("SaaS Subscription", subscription_name)
		if not sub.application:
			return {"subscription": subscription_name, "skipped": "tenant_plan_subscription"}

		if sub.status in ("Active", "Trial", "Grace Period"):
			lic_name = frappe.db.get_value(
				"SaaS License",
				{"subscription": sub.name, "application": sub.application},
				"name",
			)
			license_key = frappe.db.get_value("SaaS License", lic_name, "license_key") if lic_name else None
			return {
				"subscription": sub.name,
				"application": sub.application,
				"license_key": license_key,
				"already_active": True,
			}

		start = today()
		sub.starts_on = start
		sub.ends_on = SubscriptionService.compute_end_date(start, sub.billing_cycle)
		sub.status = "Active"
		sub.features_enabled = 1
		sub.disabled_reason = ""
		sub.save(ignore_permissions=True)

		license_doc = LicenseManager.ensure_subscription_license(sub.name)
		LicenseManager.sync_subscription_feature_state(sub.name)
		SubscriptionFulfillmentService._activate_tenant(sub.tenant, sub.name)

		return {
			"subscription": sub.name,
			"application": sub.application,
			"billing_cycle": sub.billing_cycle,
			"starts_on": sub.starts_on,
			"ends_on": sub.ends_on,
			"license_key": license_doc.license_key if license_doc else None,
			"tenant_status": frappe.db.get_value("SaaS Tenant", sub.tenant, "status"),
		}

	@staticmethod
	def _activate_tenant(tenant_name: str | None, subscription_name: str | None = None) -> None:
		if not tenant_name or not frappe.db.exists("SaaS Tenant", tenant_name):
			return

		tenant = frappe.get_doc("SaaS Tenant", tenant_name)
		has_site = bool((tenant.site_folder or tenant.site_name or "").strip())
		if has_site and tenant.status in ("Draft", "Provisioning", "Suspended"):
			tenant.status = "Active"
		if subscription_name:
			tenant.active_subscription = subscription_name
		tenant.save(ignore_permissions=True)

	@staticmethod
	def _activate_source_purchase(source_purchase_name: str) -> dict:
		purchase = frappe.get_doc("SaaS Source Purchase", source_purchase_name)
		if purchase.status == "Pending Payment":
			purchase.status = "Paid"
			purchase.save(ignore_permissions=True)

		if purchase.status == "Paid":
			purchase = LicenseManager.fulfill_source_purchase(purchase.name)
			link = LicenseManager.create_download_link(purchase.name)
		elif purchase.status == "Fulfilled":
			existing = frappe.get_all(
				"SaaS Source Download Link",
				filters={"source_purchase": purchase.name, "status": ("in", ["Active", "Used"])},
				fields=["name", "download_url"],
				order_by="creation desc",
				limit=1,
			)
			link = existing[0] if existing else LicenseManager.create_download_link(purchase.name)
		else:
			link = {}

		app = frappe.get_doc("SaaS Application", purchase.application)
		license_key = frappe.db.get_value("SaaS License", purchase.license, "license_key") if purchase.license else None
		github = SubscriptionFulfillmentService._github_access_payload(app, purchase, license_key)

		return {
			"source_purchase": purchase.name,
			"application": purchase.application,
			"license_key": license_key,
			"download_url": link.get("download_url") if isinstance(link, dict) else link.get("download_url"),
			"github": github,
		}

	@staticmethod
	def _github_access_payload(app, purchase, license_key: str | None) -> dict:
		repository_url = (getattr(app, "repository_url", None) or "").strip()
		return {
			"repository_url": repository_url,
			"repository_provider": getattr(app, "repository_provider", None) or "GitHub",
			"repository_is_private": int(bool(getattr(app, "repository_is_private", 0))),
			"customer_email": purchase.customer_email,
			"access_scope": purchase.application,
			"license_key": license_key,
			"instructions": (
				"Use this private repository URL with your ErpGenex account. "
				"Access is limited to the purchased application only."
				if repository_url
				else "Configure repository_url on the SaaS Application record to expose GitHub download access."
			),
		}
