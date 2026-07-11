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

# Apps bundled in base plans — hidden from public pricing/marketplace lists
HIDDEN_CATALOG_APPS = frozenset(
	{
		"frappe",
		"omnexa_core",
		"erpgenex_saas",
		"erpgenex_theme_0426",
		"omnexa_experience",
		"omnexa_theme_manager",
	}
)

# Apps included in base plans (no extra marketplace charge)
INCLUDED_APPS = frozenset(
	HIDDEN_CATALOG_APPS
	| {
		"omnexa_accounting",
		"omnexa_einvoice",
		"omnexa_fixed_assets",
		"omnexa_hr",
		"omnexa_projects_pm",
		"omnexa_ai_employee",
		"omnexa_customer_core",
		"omnexa_intelligence_core",
		"omnexa_n8n_bridge",
		"omnexa_user_academy",
		"omnexa_statutory_audit",
	}
)

# Licensed apps with paid subscription and source code pricing
PAID_LICENSED_APPS = frozenset(
	{
		"erpgenex_maintenance_core",
		"erpgenex_property_mgmt",
		"erpgenex_realestate_dev",
		"erpgenex_realestate_sales",
		"omnexa_agriculture",
		"omnexa_alm",
		"omnexa_car_rental",
		"omnexa_construction",
		"omnexa_consumer_finance",
		"omnexa_credit_engine",
		"omnexa_credit_risk",
		"omnexa_education",
		"omnexa_engineering_consulting",
		"omnexa_factoring",
		"omnexa_finance_engine",
		"omnexa_healthcare",
		"omnexa_leasing_finance",
		"omnexa_manufacturing",
		"omnexa_mortgage_finance",
		"omnexa_nursery",
		"omnexa_operational_risk",
		"omnexa_restaurant",
		"omnexa_sme_microfinance",
		"omnexa_sme_retail_finance",
		"omnexa_tourism",
		"omnexa_trading",
		"omnexa_vehicle_finance",
	}
)

# Default monthly add-on price by category (edit here or per-app in Desk)
# Competitive market pricing with free apps and affordable source code options
DEFAULT_APP_PRICES_BY_CATEGORY = {
	"Core": 0,
	"CRM": 0,
	"Trading": 0,
	"Accounting": 0,
	"Healthcare": 0,
	"Education": 0,
	"Manufacturing": 0,
	"POS": 0,
	"HR": 0,
	"Projects": 0,
	"Analytics": 0,
	"AI": 0,
	"Website": 0,
	"Helpdesk": 0,
	"Other": 0,
}

DEFAULT_APP_PRICE = 0

# Pricing for paid licensed apps (monthly subscription)
PAID_APP_MONTHLY_PRICES = {
	"erpgenex_maintenance_core": 29,
	"erpgenex_property_mgmt": 49,
	"erpgenex_realestate_dev": 59,
	"erpgenex_realestate_sales": 49,
	"omnexa_agriculture": 39,
	"omnexa_alm": 34,
	"omnexa_car_rental": 29,
	"omnexa_construction": 49,
	"omnexa_consumer_finance": 39,
	"omnexa_credit_engine": 44,
	"omnexa_credit_risk": 39,
	"omnexa_education": 34,
	"omnexa_engineering_consulting": 44,
	"omnexa_factoring": 39,
	"omnexa_finance_engine": 49,
	"omnexa_healthcare": 59,
	"omnexa_leasing_finance": 44,
	"omnexa_manufacturing": 54,
	"omnexa_mortgage_finance": 44,
	"omnexa_nursery": 29,
	"omnexa_operational_risk": 34,
	"omnexa_restaurant": 29,
	"omnexa_sme_microfinance": 39,
	"omnexa_sme_retail_finance": 34,
	"omnexa_tourism": 29,
	"omnexa_trading": 44,
	"omnexa_vehicle_finance": 39,
}

# Source code pricing for paid licensed apps (one-time purchase)
PAID_APP_SOURCE_CODE_PRICES = {
	"erpgenex_maintenance_core": 899,
	"erpgenex_property_mgmt": 1499,
	"erpgenex_realestate_dev": 1799,
	"erpgenex_realestate_sales": 1499,
	"omnexa_agriculture": 1199,
	"omnexa_alm": 999,
	"omnexa_car_rental": 899,
	"omnexa_construction": 1499,
	"omnexa_consumer_finance": 1199,
	"omnexa_credit_engine": 1299,
	"omnexa_credit_risk": 1199,
	"omnexa_education": 999,
	"omnexa_engineering_consulting": 1299,
	"omnexa_factoring": 1199,
	"omnexa_finance_engine": 1499,
	"omnexa_healthcare": 1799,
	"omnexa_leasing_finance": 1299,
	"omnexa_manufacturing": 1599,
	"omnexa_mortgage_finance": 1299,
	"omnexa_nursery": 899,
	"omnexa_operational_risk": 999,
	"omnexa_restaurant": 899,
	"omnexa_sme_microfinance": 1199,
	"omnexa_sme_retail_finance": 999,
	"omnexa_tourism": 899,
	"omnexa_trading": 1299,
	"omnexa_vehicle_finance": 1199,
}

# Source code pricing (one-time purchase for full source code access)
SOURCE_CODE_PRICES_BY_CATEGORY = {
	"Core": 0,
	"CRM": 299,
	"Trading": 399,
	"Accounting": 499,
	"Healthcare": 599,
	"Education": 399,
	"Manufacturing": 599,
	"POS": 299,
	"HR": 299,
	"Projects": 399,
	"Analytics": 449,
	"AI": 799,
	"Website": 199,
	"Helpdesk": 249,
	"Other": 199,
}

DEFAULT_SOURCE_CODE_PRICE = 299
