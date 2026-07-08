from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate

from erpgenex_saas.services.subscription import SubscriptionService


class TestSubscriptionService(FrappeTestCase):
	def test_compute_end_date_for_trial(self):
		result = SubscriptionService.compute_end_date("2026-07-08", "Trial")
		self.assertEqual(getdate(result).isoformat(), "2026-07-22")

	def test_compute_end_date_for_annual(self):
		result = SubscriptionService.compute_end_date("2026-07-08", "Annual")
		self.assertEqual(getdate(result).isoformat(), "2027-07-08")
