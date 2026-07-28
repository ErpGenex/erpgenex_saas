from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.services.catalog import CatalogService


class TestCatalogService(FrappeTestCase):
	def test_list_active_applications_returns_rows(self):
		CatalogService.sync_installed_apps_to_catalog()
		rows = CatalogService.list_active_applications()
		self.assertTrue(isinstance(rows, list))
		self.assertFalse(any(row["app_slug"] == "frappe" for row in rows))

	def test_hidden_catalog_apps_excluded(self):
		CatalogService.sync_installed_apps_to_catalog()
		rows = CatalogService.list_active_applications()
		slugs = {row["app_slug"] for row in rows}
		self.assertNotIn("frappe", slugs)
		self.assertNotIn("omnexa_core", slugs)

	def test_paid_apps_are_marked_private(self):
		payload = CatalogService._application_payload("omnexa_trading")
		self.assertEqual(payload["repository_is_private"], 1)

	def test_free_apps_are_marked_public(self):
		payload = CatalogService._application_payload("omnexa_accounting")
		self.assertEqual(payload["repository_is_private"], 0)

	def test_marketplace_applications_keeps_paid_apps_visible(self):
		from unittest.mock import patch

		with patch.object(CatalogService, "sync_marketplace_catalog", return_value=[]), patch(
			"frappe.get_all",
			return_value=[
				{
					"name": "omnexa_trading",
					"display_name": "ERPGenex Trading",
					"app_slug": "omnexa_trading",
					"monthly_price": 44,
					"annual_price": 440,
					"trial_days": 0,
					"category": "Trading",
					"description": "Trading application",
					"is_core": 0,
					"distribution_type": "SaaS Subscription",
					"source_code_available": 1,
					"source_code_price": 1299,
					"rating": 0,
					"current_version": None,
					"latest_version": None,
					"update_available": 0,
					"screenshots": "",
					"release_history": "",
					"changelog": "",
				},
			],
		):
			rows = CatalogService.list_marketplace_applications()

		self.assertTrue(any(row["app_slug"] == "omnexa_trading" for row in rows))

