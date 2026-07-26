from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.services.activity_bundles import filter_apps_for_activity, get_apps_for_activity


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

	def test_activity_filter_preserves_original_order(self):
		rows = [
			{"app_slug": "omnexa_core", "display_name": "Core"},
			{"app_slug": "omnexa_construction", "display_name": "Construction"},
			{"app_slug": "omnexa_education", "display_name": "Education"},
		]
		filtered = filter_apps_for_activity(rows, "مقاولات")
		self.assertEqual([row["app_slug"] for row in filtered], ["omnexa_core", "omnexa_construction"])
