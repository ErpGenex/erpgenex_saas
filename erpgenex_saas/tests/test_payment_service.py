from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.services.payment import PaymentService


class TestPaymentService(FrappeTestCase):
	def test_verify_webhook_accepts_supported_provider(self):
		result = PaymentService.verify_webhook(
			provider="PayPal",
			payload={"event_type": "PAYMENT.SALE.COMPLETED"},
			signature="demo-signature",
		)
		self.assertTrue(result["verified"])
		self.assertEqual(result["provider"], "PayPal")
