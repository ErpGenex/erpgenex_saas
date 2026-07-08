def get_context(context):
	context.no_cache = 1
	context.title = "Documentation - ERPGenex SaaS"
	context.endpoints = [
		{"method": "GET", "path": "erpgenex_saas.api.v1.platform_health", "desc": "Platform monitoring snapshot"},
		{"method": "POST", "path": "erpgenex_saas.api.v1.guest_register", "desc": "Register customer and create tenant"},
		{"method": "POST", "path": "erpgenex_saas.api.v1.guest_quote", "desc": "Get subscription quote"},
		{"method": "GET", "path": "erpgenex_saas.api.customer.get_dashboard", "desc": "Customer dashboard data"},
		{"method": "GET", "path": "erpgenex_saas.api.v1.get_openapi_spec", "desc": "OpenAPI 3.0 specification"},
	]
