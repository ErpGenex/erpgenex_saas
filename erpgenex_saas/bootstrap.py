import frappe


DEFAULT_PLANS = [
	{
		"plan_name": "Free Monthly",
		"plan_tier": "Free",
		"billing_cycle": "Monthly",
		"base_price": 0,
		"maximum_users": 1,
		"max_sites": 1,
		"storage_gb": 1,
		"support_level": "Community",
	},
	{
		"plan_name": "Starter Monthly",
		"plan_tier": "Starter",
		"billing_cycle": "Monthly",
		"base_price": 49,
		"maximum_users": 5,
		"max_sites": 2,
		"storage_gb": 10,
		"support_level": "Community",
	},
	{
		"plan_name": "Professional Monthly",
		"plan_tier": "Professional",
		"billing_cycle": "Monthly",
		"base_price": 149,
		"maximum_users": 25,
		"max_sites": 5,
		"storage_gb": 50,
		"support_level": "Business",
	},
	{
		"plan_name": "Business Monthly",
		"plan_tier": "Business",
		"billing_cycle": "Monthly",
		"base_price": 299,
		"maximum_users": 100,
		"max_sites": 20,
		"storage_gb": 250,
		"support_level": "Priority",
	},
	{
		"plan_name": "Enterprise Monthly",
		"plan_tier": "Enterprise",
		"billing_cycle": "Monthly",
		"base_price": 999,
		"maximum_users": 0,
		"max_sites": 0,
		"storage_gb": 1000,
		"support_level": "Enterprise",
	},
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
				"plan_tier": row["plan_tier"],
				"billing_cycle": row["billing_cycle"],
				"base_price": row["base_price"],
				"maximum_users": row.get("maximum_users"),
				"max_sites": row.get("max_sites"),
				"storage_gb": row.get("storage_gb"),
				"support_level": row.get("support_level"),
				"included_applications": "Core applications",
				"is_active": 1,
			}
		).insert(ignore_permissions=True)


def ensure_default_packages():
	defaults = [
		("Free", "Free Monthly", "Community"),
		("Starter", "Starter Monthly", "Community"),
		("Professional", "Professional Monthly", "Business"),
		("Business", "Business Monthly", "Priority"),
		("Enterprise", "Enterprise Monthly", "Enterprise"),
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
	if not doc.deployment_mode:
		doc.deployment_mode = doc.site_distribution_method or "Port"
		changed = True
	if not doc.start_port:
		doc.start_port = doc.base_port or 8000
		changed = True
	if not doc.end_port:
		doc.end_port = doc.max_port or 8999
		changed = True
	if not doc.server_host:
		doc.server_host = doc.server_ip or "localhost"
		changed = True
	if not doc.root_domain:
		doc.root_domain = doc.platform_domain or "erpgenex.com"
		changed = True
	if not doc.subdomain_pattern:
		doc.subdomain_pattern = "{site}.{root_domain}"
		changed = True
	if not doc.platform_domain:
		doc.platform_domain = doc.root_domain or "erpgenex.com"
		changed = True
	if not doc.extra_user_price:
		doc.extra_user_price = 5
		changed = True
	if not doc.extra_storage_price_per_gb:
		doc.extra_storage_price_per_gb = 2
		changed = True
	if changed:
		doc.save(ignore_permissions=True)


def ensure_allocated_ports():
	from erpgenex_saas.services.port_manager import PortManager

	PortManager().ensure_reserved_port_80()


def bootstrap_platform():
	ensure_roles()
	ensure_saas_settings()
	ensure_default_plans()
	ensure_default_packages()
	ensure_allocated_ports()
