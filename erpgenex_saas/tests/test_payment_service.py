from frappe.tests.utils import FrappeTestCase
from types import SimpleNamespace
from unittest.mock import patch

from erpgenex_saas.services.payment import PaymentService


class TestPaymentService(FrappeTestCase):
	def test_verify_webhook_accepts_supported_provider(self):
		result = PaymentService.verify_webhook(
			provider="PayPal",
			payload={"event_type": "PAYMENT.SALE.COMPLETED"
	},
			signature="demo-signature",
		)
		self.assertTrue(result["verified"])
		self.assertEqual(result["provider"], "PayPal")

	def test_verify_webhook_rejects_non_paypal_provider(self):
		with self.assertRaises(Exception):
			PaymentService.verify_webhook(provider="Stripe", payload={}, signature=None)

	def test_get_paypal_account_uses_sandbox_configuration(self):
		settings = SimpleNamespace(
			paypal_enabled=1,
			paypal_environment="Sandbox",
			paypal_business_email="live@example.com",
			paypal_sandbox_business_email="sandbox@example.com",
			paypal_merchant_id="LIVE-MID",
			paypal_sandbox_merchant_id="SANDBOX-MID",
		)
		with patch("frappe.get_single", return_value=settings):
			account = PaymentService.get_paypal_account()
		self.assertEqual(account["environment"], "Sandbox")
		self.assertEqual(account["business_email"], "sandbox@example.com")
		self.assertEqual(account["action_url"], "https://www.sandbox.paypal.com/cgi-bin/webscr")
