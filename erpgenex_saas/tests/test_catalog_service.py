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
