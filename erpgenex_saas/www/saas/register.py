import frappe


def get_context(context):
	frappe.local.flags.redirect_location = "/saas/checkout"
	if frappe.local.request.query_string:
		frappe.local.flags.redirect_location += "?" + frappe.local.request.query_string.decode()
	raise frappe.Redirect
