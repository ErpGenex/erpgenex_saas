from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PricingBreakdown:
	base_amount: float
	apps_amount: float
	extra_users_amount: float
	extra_storage_amount: float
	extra_services_amount: float
	total_amount: float


class PricingService:
	@staticmethod
	def calculate(
		base_amount: float,
		apps_amount: float = 0,
		extra_users_amount: float = 0,
		extra_storage_amount: float = 0,
		extra_services_amount: float = 0,
	) -> PricingBreakdown:
		total_amount = (
			float(base_amount)
			+ float(apps_amount)
			+ float(extra_users_amount)
			+ float(extra_storage_amount)
			+ float(extra_services_amount)
		)
		return PricingBreakdown(
			base_amount=float(base_amount),
			apps_amount=float(apps_amount),
			extra_users_amount=float(extra_users_amount),
			extra_storage_amount=float(extra_storage_amount),
			extra_services_amount=float(extra_services_amount),
			total_amount=round(total_amount, 2),
		)
