import frappe
import os


def is_saas_site():
	"""Check if current site is a SaaS tenant site (not the main SaaS platform site)."""
	try:
		# The main SaaS platform site is erpgenex.local.site
		# SaaS tenant sites are the ones created for customers
		site_name = getattr(frappe.local, "site", "")
		if not site_name:
			return False

		# Explicit check for main site - always return False
		if site_name == "erpgenex.local.site":
			return False  # This is the main site, not a tenant

		# Check if this is a tenant site by checking site directory structure
		bench_path = frappe.utils.get_bench_path()
		site_path = os.path.join(bench_path, "sites", site_name)

		# If site directory doesn't exist, it's not a valid site
		if not os.path.exists(site_path):
			return False

		# Check if this is a tenant site by looking for site_config.json
		site_config_path = os.path.join(site_path, "site_config.json")
		if not os.path.exists(site_config_path):
			return False

		# Only check database if we're sure this is a tenant site
		# This prevents cross-database queries from main site
		try:
			# Check if this site has SaaS Tenant doctype in its own database
			if frappe.db.table_exists("SaaS Tenant"):
				# Check if current site is registered as a tenant
				tenant_exists = frappe.db.exists("SaaS Tenant", {"site_name": site_name
	})
				return tenant_exists
		except Exception:
			# If database check fails, assume it's not a tenant site
			# to prevent any cross-site interference
			return False

	except Exception:
		# If any error occurs, assume it's not a tenant site
		# to prevent any cross-site interference
		return False

	return False


def before_request():
	try:
		# Only run SaaS hooks on SaaS tenant sites, not on main site
		if not is_saas_site():
			return

		# Ensure site-specific context isolation
		if not hasattr(frappe.local, "erpgenex_saas_context"):
			frappe.local.erpgenex_saas_context = {}

		# Import and run site-specific functions only for tenant sites
		from erpgenex_saas.portal_context import apply_portal_language
		from erpgenex_saas.permissions import restrict_to_saas_portal

		apply_portal_language()
		restrict_to_saas_portal()
	except Exception as e:
		# Log error but don't raise to prevent breaking the request
		frappe.logger("erpgenex_saas").warning(f"Before request failed for site {frappe.local.site}: {str(e)}")


def after_request():
	try:
		# Only run SaaS hooks on SaaS tenant sites, not on main site
		if not is_saas_site():
			return

		# Clear site-specific context to prevent cross-site contamination
		if hasattr(frappe.local, "erpgenex_saas_context"):
			frappe.local.erpgenex_saas_context = {}
	except Exception as e:
		# Log error but don't raise to prevent breaking the request
		frappe.logger("erpgenex_saas").warning(f"After request failed for site {frappe.local.site}: {str(e)}")
		# Clear context even if there's an error to prevent cross-site contamination
		if hasattr(frappe.local, "erpgenex_saas_context"):
			frappe.local.erpgenex_saas_context = {}
