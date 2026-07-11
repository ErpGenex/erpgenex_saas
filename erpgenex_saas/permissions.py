import frappe


def get_tenant_permission_query(user):
	"""Get tenant permission query with site isolation."""
	try:
		if not user:
			user = frappe.session.user

		# Ensure we're on the correct site before checking permissions
		site_name = getattr(frappe.local, "site", "")
		if not site_name:
			return "1=0"

		if "System Manager" in frappe.get_roles(user) or "SaaS Admin" in frappe.get_roles(user):
			return ""

		# SaaS Customers can only see their own tenants
		if "SaaS Customer" in frappe.get_roles(user):
			tenants = frappe.get_all("SaaS Customer Account", filters={"user": user}, pluck="tenant")
			if not tenants:
				return "1=0"
			return "`tabSaaS Tenant`.name in ({})".format(", ".join(repr(t) for t in tenants))

		# Other users have no access
		return "1=0"
	except Exception as e:
		# Log error but return restrictive query to maintain site isolation
		frappe.logger("erpgenex_saas").warning(f"Tenant permission query failed for site {getattr(frappe.local, 'site', 'unknown')}: {str(e)}")
		return "1=0"


def get_subscription_permission_query(user):
	"""Get subscription permission query with site isolation."""
	try:
		if not user:
			user = frappe.session.user

		# Ensure we're on the correct site before checking permissions
		site_name = getattr(frappe.local, "site", "")
		if not site_name:
			return "1=0"

		if "System Manager" in frappe.get_roles(user) or "SaaS Admin" in frappe.get_roles(user):
			return ""

		# SaaS Customers can only see their own subscriptions
		if "SaaS Customer" in frappe.get_roles(user):
			tenants = frappe.get_all("SaaS Customer Account", filters={"user": user}, pluck="tenant")
			if not tenants:
				return "1=0"
			return "`tabSaaS Subscription`.tenant in ({})".format(", ".join(repr(t) for t in tenants))

		# Other users have no access
		return "1=0"
	except Exception as e:
		# Log error but return restrictive query to maintain site isolation
		frappe.logger("erpgenex_saas").warning(f"Subscription permission query failed for site {getattr(frappe.local, 'site', 'unknown')}: {str(e)}")
		return "1=0"


def get_activity_wizard_permission_query(user):
	"""Get activity wizard permission query with site isolation."""
	try:
		if not user:
			user = frappe.session.user

		# Ensure we're on the correct site before checking permissions
		site_name = getattr(frappe.local, "site", "")
		if not site_name:
			return "1=0"

		if "System Manager" in frappe.get_roles(user) or "SaaS Admin" in frappe.get_roles(user):
			return ""

		# SaaS Customers can only see their own wizards
		if "SaaS Customer" in frappe.get_roles(user):
			return "`tabActivity Selection Wizard`.owner = {}".format(repr(user))

		# Other users have no access
		return "1=0"
	except Exception as e:
		# Log error but return restrictive query to maintain site isolation
		frappe.logger("erpgenex_saas").warning(f"Activity wizard permission query failed for site {getattr(frappe.local, 'site', 'unknown')}: {str(e)}")
		return "1=0"


def restrict_to_saas_portal():
	"""Restrict SaaS Customer access to only SaaS portal pages with site isolation."""
	try:
		# Ensure we're on a valid site
		site_name = getattr(frappe.local, "site", "")
		if not site_name:
			return

		if frappe.session.user == "Guest":
			return

		request = getattr(frappe.local, "request", None)
		current_path = request.path if request else ""
		if not current_path:
			return

		if current_path.startswith(("/assets/", "/files/", "/private/files/", "/socket.io/", "/.well-known")):
			return

		if "SaaS Customer" in frappe.get_roles(frappe.session.user):
			if current_path.startswith(("/app", "/desk")):
				frappe.local.flags.redirect_location = "/saas/dashboard"
				raise frappe.Redirect

			# Allow access to SaaS portal pages
			allowed_routes = [
				"/saas",
				"/saas/dashboard",
				"/saas/applications",
				"/saas/pricing",
				"/saas/features",
				"/saas/contact",
				"/saas/faq",
				"/saas/about",
				"/saas/docs",
				"/activity-wizard",
				"/api/method/erpgenex_saas",
				"/login",
				"/logout",
				"/api/method/login",
				"/api/method/logout",
			]

			# Check if current path is allowed
			is_allowed = any(current_path.startswith(route) for route in allowed_routes)

			if not is_allowed:
				# Redirect to SaaS dashboard if trying to access other pages
				frappe.local.flags.redirect_location = "/saas/dashboard"
				raise frappe.Redirect
	except frappe.Redirect:
		raise
	except Exception as e:
		# Log error but don't break the request to maintain site isolation
		frappe.logger("erpgenex_saas").warning(f"Portal restriction failed for site {getattr(frappe.local, 'site', 'unknown')}: {str(e)}")
