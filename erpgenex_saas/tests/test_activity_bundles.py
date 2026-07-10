from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.services.activity_bundles import get_apps_for_activity


class TestActivityBundles(FrappeTestCase):
	def test_construction_bundle_includes_core_and_construction(self):
		apps = get_apps_for_activity("مقاولات")
		self.assertIn("omnexa_core", apps)
		self.assertIn("omnexa_trading", apps)
		self.assertIn("omnexa_accounting", apps)
		self.assertIn("omnexa_construction", apps)
		self.assertNotIn("omnexa_education", apps)

	def test_general_bundle_excludes_verticals(self):
		apps = get_apps_for_activity("عام")
		self.assertNotIn("omnexa_construction", apps)
		self.assertNotIn("omnexa_education", apps)
