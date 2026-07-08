def get_context(context):
	context.no_cache = 1
	context.title = "Features - ERPGenex SaaS"
	context.features = [
		{"title": "Multi-tenant isolation", "body": "Each customer gets an isolated tenant with dedicated subscription lifecycle."},
		{"title": "Modular app catalog", "body": "Package ERPGenex apps into Starter, Business, and Enterprise bundles."},
		{"title": "Automated provisioning", "body": "Queue-based provisioning requests with audit trail and notifications."},
		{"title": "Billing & payments", "body": "Invoices, payment registration, and webhook-ready payment providers."},
		{"title": "Domain management", "body": "Subdomain and custom domain tracking with SSL status placeholders."},
		{"title": "Monitoring", "body": "Platform health snapshots and daily usage metrics."},
	]
