import frappe

def get_context(context):
	"""Context for tenant cleanup page"""
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login"
		frappe.local.response['type'] = 'redirect'
		frappe.local.response['location'] = '/login'
		return
	
	# Check if user is System Manager
	if "System Manager" not in frappe.get_roles(frappe.session.user):
		frappe.throw("Only System Managers can access this page", frappe.PermissionError)
	
	context.no_cache = 1
	return context
