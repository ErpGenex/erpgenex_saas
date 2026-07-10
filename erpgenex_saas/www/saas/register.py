import frappe


def get_context(context):
	context.no_cache = 1
	context.title = "تسجيل حساب - ERPGenex SaaS"
	if frappe.session.user != "Guest":
		frappe.local.flags.redirect_location = "/saas/dashboard"
		raise frappe.Redirect
	return context
