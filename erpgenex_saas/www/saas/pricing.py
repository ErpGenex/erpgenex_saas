import frappe

from erpgenex_saas.constants import PRICING_TIERS


def get_context(context):
	context.no_cache = 1
	context.title = "Pricing — ERPGenex SaaS"

	db_plans = frappe.get_all(
		"SaaS Plan",
		filters={"is_active": 1},
		fields=["name", "plan_name", "base_price", "billing_cycle"],
		order_by="base_price asc",
	)

	if db_plans:
		context.tiers = []
		for plan in db_plans:
			name = plan.plan_name or plan.name
			monthly = float(plan.base_price or 0)
			context.tiers.append(
				{
					"slug": name.lower().replace(" ", "-"),
					"name": name.replace(" Monthly", "").replace(" Monthly", ""),
					"plan": plan.name,
					"monthly": monthly,
					"yearly": round(monthly * 12 * 0.8),
					"featured": "professional" in name.lower() or "business" in name.lower(),
					"features": _features_for_plan(name),
				}
			)
	else:
		context.tiers = PRICING_TIERS


def _features_for_plan(plan_name: str) -> list[str]:
	plan_key = plan_name.lower()
	for tier in PRICING_TIERS:
		if tier["name"].lower() in plan_key or tier["plan"].lower() in plan_key:
			return tier["features"]
	return ["Flexible ErpGenex tenant", "Modular apps", "Email support"]
