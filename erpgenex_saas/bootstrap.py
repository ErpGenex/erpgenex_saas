import frappe


DEFAULT_PLANS = [
	{"plan_name": "Starter Monthly", "billing_cycle": "Monthly", "base_price": 49},
	{"plan_name": "Business Monthly", "billing_cycle": "Monthly", "base_price": 149},
	{"plan_name": "Professional Monthly", "billing_cycle": "Monthly", "base_price": 249},
	{"plan_name": "Enterprise Monthly", "billing_cycle": "Monthly", "base_price": 499},
	{"plan_name": "Unlimited Monthly", "billing_cycle": "Monthly", "base_price": 999},
]

SAAS_ROLES = ("SaaS Admin", "SaaS Customer")


def ensure_default_plans():
	for row in DEFAULT_PLANS:
		if frappe.db.exists("SaaS Plan", row["plan_name"]):
			continue
		frappe.get_doc(
			{
				"doctype": "SaaS Plan",
				"plan_name": row["plan_name"],
				"billing_cycle": row["billing_cycle"],
				"base_price": row["base_price"],
				"is_active": 1,
			}
		).insert(ignore_permissions=True)


def ensure_default_packages():
	defaults = [
		("Starter", "Starter Monthly", "Business"),
		("Business", "Business Monthly", "Priority"),
		("Professional", "Professional Monthly", "Priority"),
		("Enterprise", "Enterprise Monthly", "Enterprise"),
		("Unlimited", "Unlimited Monthly", "Enterprise"),
	]
	for package_name, base_plan, support_level in defaults:
		if frappe.db.exists("SaaS Package", package_name):
			continue
		frappe.get_doc(
			{
				"doctype": "SaaS Package",
				"package_name": package_name,
				"base_plan": base_plan,
				"support_level": support_level,
				"is_active": 1,
			}
		).insert(ignore_permissions=True)


def ensure_roles():
	for role_name in SAAS_ROLES:
		if frappe.db.exists("Role", role_name):
			continue
		frappe.get_doc({"doctype": "Role", "role_name": role_name, "desk_access": 1}).insert(
			ignore_permissions=True
		)


def ensure_saas_settings():
	if not frappe.db.exists("DocType", "SaaS Settings"):
		return
	doc = frappe.get_single("SaaS Settings")
	changed = False
	if not doc.platform_domain:
		doc.platform_domain = "erpgenex.com"
		changed = True
	if not doc.extra_user_price:
		doc.extra_user_price = 5
		changed = True
	if not doc.extra_storage_price_per_gb:
		doc.extra_storage_price_per_gb = 2
		changed = True
	if changed:
		doc.save(ignore_permissions=True)


def bootstrap_platform():
	ensure_roles()
	ensure_saas_settings()
	ensure_default_plans()
	ensure_default_packages()
