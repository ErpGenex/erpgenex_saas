from types import SimpleNamespace
from unittest.mock import patch

from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.services.license_manager import LicenseManager


class TestApplicationProtection(FrappeTestCase):
	def test_paid_application_requires_private_repository(self):
		app = SimpleNamespace(
			name="paid_app",
			is_core=False,
			distribution_type="SaaS Subscription",
			repository_is_private=0,
			repository_url="",
		)

		with patch("frappe.get_doc", return_value=app), patch("frappe.throw", side_effect=Exception) as mock_throw:
			with self.assertRaises(Exception):
				LicenseManager.ensure_private_distribution("paid_app")

		mock_throw.assert_called_once()

	def test_source_download_requires_login(self):
		import frappe

		with patch.object(frappe.session, "user", "Guest"), patch("frappe.throw", side_effect=Exception) as mock_throw:
			with self.assertRaises(Exception):
				LicenseManager.verify_download_token("token")

		mock_throw.assert_called_once()

	def test_paid_app_cannot_receive_github_access(self):
		purchase = SimpleNamespace(
			name="purchase-1",
			application="paid_app",
			status="Paid",
			license=None,
			tenant=None,
			customer_email="customer@example.com",
			github_access_granted=0,
			github_username="",
			save=lambda **kwargs: None,
		)
		paid_app = SimpleNamespace(is_core=False, distribution_type="SaaS Subscription")

		with (
			patch("frappe.get_doc", side_effect=lambda doctype, name=None: purchase if doctype == "SaaS Source Purchase" else paid_app),
			patch("frappe.throw", side_effect=Exception) as mock_throw,
		):
			with self.assertRaises(Exception):
				LicenseManager.fulfill_source_purchase("purchase-1", grant_github_access=True, github_username="user")

		mock_throw.assert_called_once()
