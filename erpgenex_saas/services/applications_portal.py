from __future__ import annotations

import frappe

from erpgenex_saas.services.catalog import CatalogService
from erpgenex_saas.services.license_manager import SOURCE_LICENSE_TYPE, LicenseManager


def mask_license_key(key: str | None) -> str:
	key = (key or "").strip()
	if len(key) <= 10:
		return key
	return f"{key[:6]}…{key[-4:]}"


def _require_logged_in_user() -> str:
	if frappe.session.user in (None, "Guest"):
		frappe.throw("Login required", frappe.PermissionError)
	return frappe.session.user


def _user_tenant_names(user: str) -> list[str]:
	from erpgenex_saas.api.customer import _user_tenant_names

	return _user_tenant_names(user)


def _tenant_installed_slugs(tenant_name: str) -> list[str]:
	from erpgenex_saas.api.customer import _latest_selected_apps
	from erpgenex_saas.services.provisioning import ProvisioningService

	slugs = set(_latest_selected_apps(tenant_name))
	tenant = frappe.db.get_value(
		"SaaS Tenant",
		tenant_name,
		["site_folder", "site_name", "status"],
		as_dict=True,
	)
	if tenant and tenant.status == "Active":
		site = (tenant.site_folder or tenant.site_name or "").strip()
		if site:
			try:
				slugs.update(ProvisioningService._list_installed_apps(site))
			except Exception:
				pass
	return sorted(slug for slug in slugs if slug)


def _subscription_rows(tenant_name: str) -> list[dict]:
	return frappe.get_all(
		"SaaS Subscription",
		filters={"tenant": tenant_name, "application": ("is", "set"), "docstatus": ("!=", 2)},
		fields=[
			"name",
			"application",
			"billing_cycle",
			"status",
			"starts_on",
			"ends_on",
			"apps_amount",
			"features_enabled",
		],
		order_by="modified desc",
		limit=200,
		ignore_permissions=True,
	)


def _license_rows(tenant_name: str) -> list[dict]:
	return frappe.get_all(
		"SaaS License",
		filters={"tenant": tenant_name, "docstatus": ("!=", 2)},
		fields=[
			"name",
			"application",
			"license_type",
			"status",
			"license_key",
			"subscription",
			"source_purchase",
			"starts_on",
			"ends_on",
			"features_enabled",
		],
		order_by="modified desc",
		limit=200,
		ignore_permissions=True,
	)


def _source_purchase_rows(tenant_name: str) -> list[dict]:
	return frappe.get_all(
		"SaaS Source Purchase",
		filters={"tenant": tenant_name},
		fields=["name", "application", "status", "amount", "purchase_date", "license", "customer_email"],
		order_by="modified desc",
		limit=100,
		ignore_permissions=True,
	)


def _entitlement_for_app(
	app_slug: str,
	*,
	installed: bool,
	subscription: dict | None,
	license_doc: dict | None,
	source_purchase: dict | None,
) -> dict:
	payload = CatalogService._application_payload(app_slug)
	scenario = "free"
	if source_purchase and source_purchase.get("status") in ("Paid", "Fulfilled"):
		scenario = "source"
	elif subscription:
		scenario = "subscription"
	elif payload.get("is_core"):
		scenario = "included"

	return {
		"app_slug": app_slug,
		"display_name": payload.get("display_name") or app_slug,
		"category": payload.get("category") or "General",
		"is_core": bool(payload.get("is_core")),
		"installed": installed,
		"scenario": scenario,
		"subscription": subscription,
		"license": {
			"name": license_doc.get("name") if license_doc else None,
			"license_type": license_doc.get("license_type") if license_doc else None,
			"status": license_doc.get("status") if license_doc else None,
			"license_key_masked": mask_license_key(license_doc.get("license_key") if license_doc else None),
			"starts_on": license_doc.get("starts_on") if license_doc else None,
			"ends_on": license_doc.get("ends_on") if license_doc else None,
		}
		if license_doc
		else None,
		"source_purchase": source_purchase,
	}


def get_tenant_application_state(tenant_name: str, user: str | None = None) -> dict:
	user = user or _require_logged_in_user()
	if tenant_name not in _user_tenant_names(user):
		frappe.throw("Not permitted for this tenant", frappe.PermissionError)

	installed_slugs = _tenant_installed_slugs(tenant_name)
	subscriptions = {row.application: row for row in _subscription_rows(tenant_name)}
	licenses_by_app: dict[str, dict] = {}
	for row in _license_rows(tenant_name):
		if row.application and row.application not in licenses_by_app:
			licenses_by_app[row.application] = row

	source_by_app: dict[str, dict] = {}
	for row in _source_purchase_rows(tenant_name):
		if row.application and row.application not in source_by_app:
			source_by_app[row.application] = row

	all_slugs = sorted(set(installed_slugs) | set(subscriptions) | set(licenses_by_app) | set(source_by_app))
	items = [
		_entitlement_for_app(
			slug,
			installed=slug in installed_slugs,
			subscription=subscriptions.get(slug),
			license_doc=licenses_by_app.get(slug),
			source_purchase=source_by_app.get(slug),
		)
		for slug in all_slugs
	]

	return {
		"tenant": tenant_name,
		"installed_count": len(installed_slugs),
		"items": items,
	}


def get_applications_portal_state(user: str | None = None) -> dict:
	user = user or frappe.session.user
	logged_in = user not in (None, "Guest")
	tenants: list[dict] = []
	installed_summary: list[dict] = []

	if logged_in:
		for tenant_name in _user_tenant_names(user):
			if frappe.db.get_value("SaaS Tenant", tenant_name, "status") == "Archived":
				continue
			tenant_doc = frappe.db.get_value(
				"SaaS Tenant",
				tenant_name,
				["name", "tenant_name", "status", "site_name", "subdomain"],
				as_dict=True,
			)
			state = get_tenant_application_state(tenant_name, user=user)
			tenants.append({**tenant_doc, "application_state": state})
			for item in state.get("items") or []:
				installed_summary.append({**item, "tenant": tenant_name})

	marketplace = CatalogService.list_marketplace_applications()
	status_by_slug: dict[str, dict] = {}
	for row in installed_summary:
		slug = row.get("app_slug")
		if not slug:
			continue
		status_by_slug.setdefault(slug, {"installed_on": [], "scenario": row.get("scenario")})
		status_by_slug[slug]["installed_on"].append(row.get("tenant"))

	for app in marketplace:
		slug = app.get("app_slug") or app.get("name")
		app["portal_status"] = status_by_slug.get(slug, {"installed_on": [], "scenario": None})

	settings = frappe.get_single("SaaS Settings")
	return {
		"logged_in": logged_in,
		"user": user if logged_in else None,
		"tenants": tenants,
		"installed_summary": installed_summary,
		"marketplace": marketplace,
		"payment": {
			"paypal_enabled": bool(settings.paypal_enabled),
			"paypal_business_email": (settings.paypal_business_email or "").strip(),
		},
		"scenarios": [
			{
				"id": "subscription",
				"title": "Subscription",
				"description": "Choose Monthly or Annual billing, pay via PayPal, receive an activation key, then install on your tenant site.",
				"billing_cycles": ["Monthly", "Annual"],
			},
			{
				"id": "payment",
				"title": "Payment & Activation",
				"description": "After payment the platform generates an EGX license key. Enter it in ErpGenEx Marketplace on your tenant site to unlock the app.",
			},
			{
				"id": "source",
				"title": "Source Code",
				"description": "One-time purchase grants a lifetime source license and secure download link without a recurring subscription.",
			},
		],
	}


def reveal_license_key(tenant: str, application: str, user: str | None = None) -> dict:
	user = user or _require_logged_in_user()
	if tenant not in _user_tenant_names(user):
		frappe.throw("Not permitted for this tenant", frappe.PermissionError)

	licenses = frappe.get_all(
		"SaaS License",
		filters={"tenant": tenant, "application": application, "docstatus": ("!=", 2)},
		fields=["name", "license_key", "license_type", "status", "ends_on"],
		order_by="modified desc",
		limit=1,
		ignore_permissions=True,
	)
	license_doc = licenses[0] if licenses else None
	if not license_doc:
		frappe.throw("No license found for this application")

	if license_doc.license_type == SOURCE_LICENSE_TYPE:
		purchase = frappe.db.get_value(
			"SaaS Source Purchase",
			{"tenant": tenant, "application": application, "license": license_doc.name},
			["status", "name"],
			as_dict=True,
		)
		if purchase and purchase.status not in ("Paid", "Fulfilled"):
			frappe.throw("Source purchase is not paid yet")

	return {
		"license": license_doc.name,
		"license_key": license_doc.license_key,
		"license_type": license_doc.license_type,
		"status": license_doc.status,
		"ends_on": license_doc.ends_on,
		"activation_hint": "Open your tenant site → ErpGenEx Marketplace → Activate License → paste this key.",
	}
