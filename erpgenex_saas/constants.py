PLAN_BILLING_CYCLES = (
	"Monthly",
	"Quarterly",
	"Semi Annual",
	"Annual",
	"Lifetime",
	"Trial",
)

SUBSCRIPTION_STATUSES = (
	"Draft",
	"Trial",
	"Active",
	"Grace Period",
	"Paused",
	"Cancelled",
	"Expired",
)

TENANT_STATUSES = (
	"Draft",
	"Provisioning",
	"Active",
	"Suspended",
	"Archived",
)

PROVISIONING_STATUSES = (
	"Queued",
	"Running",
	"Completed",
	"Failed",
)

PRICING_TIERS = [
	{
		"slug": "starter",
		"name": "Starter",
		"plan": "Starter Monthly",
		"monthly": 49,
		"yearly": 470,
		"featured": False,
		"features": ["1 Tenant", "5 Users", "10 GB Storage", "Email Support"],
	},
	{
		"slug": "business",
		"name": "Business",
		"plan": "Business Monthly",
		"monthly": 149,
		"yearly": 1430,
		"featured": False,
		"features": ["3 Tenants", "25 Users", "50 GB Storage", "Priority Support"],
	},
	{
		"slug": "professional",
		"name": "Professional",
		"plan": "Professional Monthly",
		"monthly": 249,
		"yearly": 2390,
		"featured": True,
		"features": ["10 Tenants", "100 Users", "200 GB Storage", "24/7 Support"],
	},
	{
		"slug": "enterprise",
		"name": "Enterprise",
		"plan": "Enterprise Monthly",
		"monthly": 499,
		"yearly": 4790,
		"featured": False,
		"features": ["Unlimited Tenants", "500 Users", "1 TB Storage", "Dedicated Manager"],
	},
	{
		"slug": "unlimited",
		"name": "Unlimited",
		"plan": "Unlimited Monthly",
		"monthly": 999,
		"yearly": 9590,
		"featured": False,
		"features": ["Everything Unlimited", "Custom SLA", "White Label", "On-prem Option"],
	},
]

# Branding: marketplace display names use ErpGenex instead of Omnexa
BRAND_REPLACEMENTS = (
	("Omnexa ", "ErpGenex "),
	("OMNEXA ", "ERPGenex "),
	("Omnexa", "ErpGenex"),
	("OMNEXA", "ERPGenex"),
	("ErpGenEx", "ErpGenex"),
	("ERPGENEX", "ERPGenex"),
)

# Apps included in base plans (no extra marketplace charge)
INCLUDED_APPS = frozenset(
	{
		"frappe",
		"omnexa_core",
		"erpgenex_saas",
		"erpgenex_theme_0426",
		"omnexa_experience",
		"omnexa_theme_manager",
	}
)

# Default monthly add-on price by category (edit here or per-app in Desk)
DEFAULT_APP_PRICES_BY_CATEGORY = {
	"Core": 0,
	"CRM": 19,
	"Trading": 29,
	"Accounting": 39,
	"Healthcare": 49,
	"Education": 39,
	"Manufacturing": 45,
	"POS": 25,
	"HR": 29,
	"Projects": 29,
	"Analytics": 35,
	"AI": 59,
	"Website": 15,
	"Helpdesk": 19,
	"Other": 19,
}

DEFAULT_APP_PRICE = 19
