import frappe


def get_context(context):
	context.no_cache = 1
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/saas/register"
		raise frappe.Redirect
	frappe.local.flags.redirect_location = "/saas/dashboard"
	raise frappe.Redirect
