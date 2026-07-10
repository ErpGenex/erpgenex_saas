import frappe


def get_context(context):
	context.no_cache = 1
	context.title = "إنشاء موقع جديد"
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/saas/register?next=/activity-wizard"
		raise frappe.Redirect

	from erpgenex_saas.api.customer import get_site_limit

	context.user_email = frappe.session.user
	context.site_limit = get_site_limit()
	existing_wizard = frappe.db.get_value(
		"Activity Selection Wizard",
		{"owner": frappe.session.user, "status": ["!=", "مكتمل"]},
		"name",
	)
	context.existing_wizard = frappe.get_doc("Activity Selection Wizard", existing_wizard) if existing_wizard else None
	return context
