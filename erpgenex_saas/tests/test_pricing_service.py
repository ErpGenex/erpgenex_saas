from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.services.pricing import PricingService


class TestPricingService(FrappeTestCase):
	def test_calculate_returns_expected_total(self):
		result = PricingService.calculate(
			base_amount=100,
			apps_amount=25,
			extra_users_amount=10,
			extra_storage_amount=5,
			extra_services_amount=15,
		)
		self.assertEqual(result.total_amount, 155.0)
		self.assertEqual(result.base_amount, 100.0)
