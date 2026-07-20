def build_openapi_spec():
	return {
		"openapi": "3.0.3",
		"info": {
			"title": "ERPGenex SaaS API",
			"version": "1.0.0",
			"description": "Versioned REST API for ERPGenex SaaS platform"
	},
		"paths": {
			"/api/method/erpgenex_saas.api.v1.guest_quote": {
				"post": {"summary": "Get subscription quote", "tags": ["Pricing"]
	}
			},
			"/api/method/erpgenex_saas.api.v1.guest_register": {
				"post": {"summary": "Register customer and create tenant", "tags": ["Portal"]
	}
			},
			"/api/method/erpgenex_saas.api.v1.platform_health": {
				"get": {"summary": "Platform monitoring snapshot", "tags": ["Monitoring"]
	}
			},
			"/api/method/erpgenex_saas.api.v1.package_quote": {
				"post": {"summary": "Calculate package price", "tags": ["Pricing"]
	}
			},
			"/api/method/erpgenex_saas.api.portal.list_marketplace_applications": {
				"get": {"summary": "List marketplace applications", "tags": ["Marketplace"]
	}
			},
			"/api/method/erpgenex_saas.api.portal.register_invoice_payment": {
				"post": {"summary": "Register invoice payment", "tags": ["Billing"]
	}
			},
			"/api/method/erpgenex_saas.api.v1.cancel_subscription": {
				"post": {"summary": "Cancel subscription", "tags": ["Subscription"]
	}
			},
			"/api/method/erpgenex_saas.api.v1.pause_subscription": {
				"post": {"summary": "Pause subscription", "tags": ["Subscription"]
	}
			},
			"/api/method/erpgenex_saas.api.v1.resume_subscription": {
				"post": {"summary": "Resume subscription", "tags": ["Subscription"]
	}
			},
		},
	}
