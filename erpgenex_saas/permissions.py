import frappe


def get_tenant_permission_query(user):
	if not user:
		user = frappe.session.user
	if "System Manager" in frappe.get_roles(user) or "SaaS Admin" in frappe.get_roles(user):
		return ""
	tenants = frappe.get_all("SaaS Customer Account", filters={"user": user}, pluck="tenant")
	if not tenants:
		return "1=0"
	return "`tabSaaS Tenant`.name in ({})".format(", ".join(repr(t) for t in tenants))


def get_subscription_permission_query(user):
	if not user:
		user = frappe.session.user
	if "System Manager" in frappe.get_roles(user) or "SaaS Admin" in frappe.get_roles(user):
		return ""
	tenants = frappe.get_all("SaaS Customer Account", filters={"user": user}, pluck="tenant")
	if not tenants:
		return "1=0"
	return "`tabSaaS Subscription`.tenant in ({})".format(", ".join(repr(t) for t in tenants))
