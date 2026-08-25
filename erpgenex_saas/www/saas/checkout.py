import frappe

from erpgenex_saas.portal_context import apply_portal_context


def get_context(context):
	apply_portal_context(context)
	context.no_cache = 1
	settings = frappe.get_single("SaaS Settings")
	context.extra_user_price = float(settings.extra_user_price or 0)
	context.extra_storage_price_per_gb = float(settings.extra_storage_price_per_gb or 0)
	context.title = frappe._("Checkout — ERPGenex SaaS")
	return context
