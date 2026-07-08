import frappe

from erpgenex_saas.constants import PRICING_TIERS


def get_context(context):
	context.no_cache = 1
	context.title = "Secure Checkout — ERPGenex SaaS"
	context.plans = frappe.get_all(
		"SaaS Plan",
		filters={"is_active": 1},
		fields=["name", "plan_name", "base_price", "billing_cycle"],
		order_by="base_price asc",
	)
	if not context.plans:
		context.plans = [
			{"name": t["plan"], "plan_name": t["name"], "base_price": t["monthly"]} for t in PRICING_TIERS
		]
	context.billing_cycles = ["Monthly", "Quarterly", "Annual", "Trial"]
