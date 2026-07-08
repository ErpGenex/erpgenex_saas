import frappe


def before_request():
	if not hasattr(frappe.local, "erpgenex_saas_context"):
		frappe.local.erpgenex_saas_context = {}


def after_request():
	if hasattr(frappe.local, "erpgenex_saas_context"):
		frappe.local.erpgenex_saas_context = {}
