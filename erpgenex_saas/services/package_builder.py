from __future__ import annotations

import frappe

from erpgenex_saas.services.pricing import PricingService


class PackageBuilderService:
	@staticmethod
	def calculate_package_price(package_name: str, extra_users: int = 0, extra_storage_gb: float = 0):
		package = frappe.get_doc("SaaS Package", package_name)
		plan = frappe.get_doc("SaaS Plan", package.base_plan)
		apps_amount = 0.0
		for row in package.applications:
			price = row.monthly_price_override
			if not price and row.application:
				price = frappe.db.get_value("SaaS Application", row.application, "monthly_price") or 0
			apps_amount += float(price or 0)
		settings = frappe.get_single("SaaS Settings")
		extra_users_amount = extra_users * float(settings.extra_user_price or 0)
		extra_storage_amount = extra_storage_gb * float(settings.extra_storage_price_per_gb or 0)
		return PricingService.calculate(
			base_amount=plan.base_price,
			apps_amount=apps_amount,
			extra_users_amount=extra_users_amount,
			extra_storage_amount=extra_storage_amount,
		)
