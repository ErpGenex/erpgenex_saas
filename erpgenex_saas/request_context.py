import frappe


def before_request():
	try:
		if not hasattr(frappe.local, "erpgenex_saas_context"):
			frappe.local.erpgenex_saas_context = {}
		from erpgenex_saas.portal_context import apply_portal_language
		from erpgenex_saas.permissions import restrict_to_saas_portal

		apply_portal_language()
		restrict_to_saas_portal()
	except Exception as e:
		frappe.logger("erpgenex_saas").warning(f"Before request failed: {str(e)}")


def after_request():
	try:
		if hasattr(frappe.local, "erpgenex_saas_context"):
			frappe.local.erpgenex_saas_context = {}
	except Exception as e:
		frappe.logger("erpgenex_saas").warning(f"After request failed: {str(e)}")
