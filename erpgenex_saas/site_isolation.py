"""
Site Isolation Module for ERPGenex SaaS

This module provides comprehensive site isolation to ensure that:
1. No SaaS tenant site can affect another tenant site
2. No SaaS tenant site can affect the main platform site
3. The main platform site cannot be affected by tenant operations
"""

import frappe
import os
from functools import wraps


def ensure_site_isolation(func):
	"""
	Decorator to ensure site isolation for API functions.
	This validates that operations are performed within the correct site context.
	"""
	@wraps(func)
	def wrapper(*args, **kwargs):
		try:
			# Ensure we have a valid site context
			site_name = getattr(frappe.local, "site", "")
			if not site_name:
				frappe.throw("Site context not found", frappe.PermissionError)

			# Validate site exists
			bench_path = frappe.utils.get_bench_path()
			site_path = os.path.join(bench_path, "sites", site_name)
			if not os.path.exists(site_path):
				frappe.throw(f"Site {site_name} does not exist", frappe.PermissionError)

			# Execute the function
			return func(*args, **kwargs)

		except frappe.PermissionError:
			raise
		except Exception as e:
			frappe.logger("erpgenex_saas").error(f"Site isolation check failed: {str(e)}")
			frappe.throw("Site isolation validation failed", frappe.PermissionError)

	return wrapper


def validate_tenant_access(tenant_name):
	"""
	Validate that the current user has access to the specified tenant.
	This prevents cross-tenant data access.
	"""
	try:
		site_name = getattr(frappe.local, "site", "")
		if not site_name:
			return False

		# System managers and SaaS admins can access all tenants
		if "System Manager" in frappe.get_roles() or "SaaS Admin" in frappe.get_roles():
			return True

		# SaaS customers can only access their own tenants
		if "SaaS Customer" in frappe.get_roles():
			user_tenants = frappe.get_all("SaaS Customer Account", 
				filters={"user": frappe.session.user}, 
				pluck="tenant")
			return tenant_name in user_tenants

		# Other roles have no access
		return False

	except Exception as e:
		frappe.logger("erpgenex_saas").error(f"Tenant access validation failed: {str(e)}")
		return False


def get_site_context():
	"""
	Get the current site context with isolation validation.
	Returns site-specific configuration and metadata.
	"""
	try:
		site_name = getattr(frappe.local, "site", "")
		if not site_name:
			return None

		# Return site-specific context
		return {
			"site_name": site_name,
			"is_main_site": site_name == "erpgenex.local.site",
			"is_tenant_site": frappe.db.table_exists("SaaS Tenant") and 
				frappe.db.exists("SaaS Tenant", {"site_name": site_name})
		}

	except Exception as e:
		frappe.logger("erpgenex_saas").error(f"Site context retrieval failed: {str(e)}")
		return None


def isolate_database_query(query, params=None):
	"""
	Ensure database queries are isolated to the current site.
	This prevents cross-site database access.
	"""
	try:
		site_name = getattr(frappe.local, "site", "")
		if not site_name:
			raise frappe.PermissionError("No site context for database query")

		# Execute query in current site context
		if params:
			return frappe.db.sql(query, params)
		else:
			return frappe.db.sql(query)

	except Exception as e:
		frappe.logger("erpgenex_saas").error(f"Database query isolation failed: {str(e)}")
		raise frappe.PermissionError("Database query isolation failed")


def clear_site_cache():
	"""
	Clear cache only for the current site to prevent cross-site cache contamination.
	"""
	try:
		site_name = getattr(frappe.local, "site", "")
		if not site_name:
			return

		# Clear site-specific cache
		frappe.clear_cache()
		frappe.cache_manager.clear()

	except Exception as e:
		frappe.logger("erpgenex_saas").error(f"Site cache clearing failed: {str(e)}")


def validate_site_operation(operation):
	"""
	Validate that an operation is allowed for the current site.
	"""
	try:
		site_context = get_site_context()
		if not site_context:
			return False

		# Main site can perform all operations
		if site_context["is_main_site"]:
			return True

		# Tenant sites have restricted operations
		if site_context["is_tenant_site"]:
			allowed_operations = [
				"read_tenant_data",
				"update_tenant_settings",
				"view_subscription"
			]
			return operation in allowed_operations

		return False

	except Exception as e:
		frappe.logger("erpgenex_saas").error(f"Site operation validation failed: {str(e)}")
		return False
