import frappe


def before_request():
	if not hasattr(frappe.local, "erpgenex_saas_context"):
		frappe.local.erpgenex_saas_context = {}
	from erpgenex_saas.portal_context import apply_portal_language

	apply_portal_language()


def after_request():
	if hasattr(frappe.local, "erpgenex_saas_context"):
		frappe.local.erpgenex_saas_context = {}
