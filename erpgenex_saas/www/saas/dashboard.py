import frappe


def get_context(context):
	context.no_cache = 1
	context.title = "لوحة التحكم - ERPGenex SaaS"
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/saas/register?next=/saas/dashboard"
		raise frappe.Redirect
	user = frappe.get_doc("User", frappe.session.user)
	context.username = user.first_name or user.email
	return context
