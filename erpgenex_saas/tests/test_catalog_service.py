from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.services.catalog import CatalogService


class TestCatalogService(FrappeTestCase):
	def test_list_active_applications_returns_rows(self):
		CatalogService.sync_installed_apps_to_catalog()
		rows = CatalogService.list_active_applications()
		self.assertTrue(isinstance(rows, list))
		self.assertTrue(any(row["app_slug"] == "frappe" for row in rows))
