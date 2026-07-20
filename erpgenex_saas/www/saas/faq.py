def get_context(context):
	context.no_cache = 1
	context.title = "FAQ - ERPGenex SaaS"
	context.faqs = [
		{"q": "Does SaaS modify existing ERPGenex apps?", "a": "No. erpgenex_saas is a standalone platform layer that reads app metadata without changing business apps."
	},
		{"q": "How is a tenant provisioned?", "a": "Registration creates tenant, subscription, invoice, and a queued provisioning request processed by background workers."},
		{"q": "Which payment providers are supported?", "a": "The billing layer supports PayPal, Stripe, and manual payment registration with webhook verification hooks."},
		{"q": "Can I pause or cancel a subscription?", "a": "Yes. Subscription lifecycle supports pause, resume, and cancel through the API and desk."},
	]
