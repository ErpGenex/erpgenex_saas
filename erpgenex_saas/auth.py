import frappe
import time
from functools import wraps


def validate():
	"""Enhanced auth hook for API token and tenant-bound auth with rate limiting."""
	frappe.local.flags.erpgenex_saas_auth_checked = True
	
	# Redirect SaaS Customer users to their dashboard
	_redirect_saas_customer()
	
	# Implement rate limiting for API calls
	_rate_limit_check()


def _redirect_saas_customer():
	"""Redirect SaaS Customer users to their dashboard and prevent access to /app/dashboard."""
	try:
		if frappe.session.user == "Guest":
			return
		
		# Check if user has SaaS Customer role
		user_roles = frappe.get_roles(frappe.session.user)
		if "SaaS Customer" not in user_roles:
			return
		
		# Get current path
		import urllib.parse
		path = frappe.local.request.path if hasattr(frappe.local, 'request') else ""
		
		# Redirect to SaaS dashboard if trying to access /app or /desk
		if path.startswith("/app") or path.startswith("/desk"):
			frappe.local.flags.redirect_location = "/saas/dashboard"
			frappe.local.response['type'] = 'redirect'
			frappe.local.response['location'] = '/saas/dashboard'
			
	except Exception as e:
		# Log error but don't block requests on redirect failure
		frappe.logger("erpgenex_saas").warning(f"SaaS Customer redirect check failed: {str(e)}")


def _rate_limit_check():
	"""Basic rate limiting to prevent abuse."""
	try:
		# Get client IP
		client_ip = frappe.local.request_ip if hasattr(frappe.local, 'request_ip') else 'unknown'
		
		# Simple in-memory rate limiting (consider Redis for production)
		if not hasattr(frappe.local, 'rate_limit_cache'):
			frappe.local.rate_limit_cache = {}
		
		now = time.time()
		window = 60  # 1 minute window
		max_requests = 100  # Max 100 requests per minute
		
		if client_ip not in frappe.local.rate_limit_cache:
			frappe.local.rate_limit_cache[client_ip] = []
		
		# Clean old requests
		frappe.local.rate_limit_cache[client_ip] = [
			t for t in frappe.local.rate_limit_cache[client_ip] if t > now - window
		]
		
		# Check if limit exceeded
		if len(frappe.local.rate_limit_cache[client_ip]) >= max_requests:
			frappe.throw("Rate limit exceeded. Please try again later.", frappe.TooManyRequestsError)
		
		# Add current request
		frappe.local.rate_limit_cache[client_ip].append(now)
		
	except Exception as e:
		# Log error but don't block requests on rate limit failure
		frappe.logger("erpgenex_saas").warning(f"Rate limiting check failed: {str(e)}")


def require_authenticated_user():
	"""Decorator to ensure user is authenticated."""
	def decorator(f):
		@wraps(f)
		def wrapper(*args, **kwargs):
			if frappe.session.user == "Guest":
				frappe.throw("Authentication required", frappe.PermissionError)
			return f(*args, **kwargs)
		return wrapper
	return decorator


def validate_tenant_access(tenant_name):
	"""Validate that the current user has access to the specified tenant."""
	try:
		if frappe.session.user == "Guest":
			frappe.throw("Authentication required", frappe.PermissionError)
		
		# Check if user is System Manager (full access)
		if "System Manager" in frappe.get_roles(frappe.session.user):
			return True
		
		# Check if user is linked to the tenant
		customer_account = frappe.db.get_value(
			"SaaS Customer Account",
			{"user": frappe.session.user, "tenant": tenant_name}
		)
		
		if not customer_account:
			frappe.throw("You don't have access to this tenant", frappe.PermissionError)
		
		return True
		
	except Exception as e:
		frappe.logger("erpgenex_saas").error(f"Tenant access validation failed: {str(e)}")
		raise
