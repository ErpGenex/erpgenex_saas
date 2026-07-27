from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.services.catalog import CatalogService
from erpgenex_saas.services.activity_bundles import (
	CORE_PLATFORM_APPS,
	filter_apps_for_activity,
	get_apps_for_activity,
	get_free_auto_install_apps,
)


class TestActivityBundles(FrappeTestCase):
	def test_general_bundle_matches_requested_base_apps(self):
		apps = get_apps_for_activity("عام")
		self.assertIn("omnexa_core", apps)
		self.assertIn("omnexa_accounting", apps)
		self.assertIn("omnexa_services", apps)
		self.assertIn("omnexa_edms", apps)
		self.assertIn("omnexa_setup_intelligence", apps)
		self.assertIn("omnexa_eng_document_control", apps)
		self.assertIn("omnexa_backup", apps)
		self.assertIn("erpgenex_demo_studio", apps)
		self.assertNotIn("omnexa_trading", apps)
		self.assertNotIn("omnexa_construction", apps)
		self.assertNotIn("omnexa_education", apps)
		self.assertTrue(set(apps).issubset(set(CORE_PLATFORM_APPS)))

	def test_construction_bundle_adds_vertical_only(self):
		apps = get_apps_for_activity("مقاولات")
		self.assertIn("omnexa_core", apps)
		self.assertIn("omnexa_services", apps)
		self.assertIn("omnexa_construction", apps)
		self.assertNotIn("omnexa_education", apps)
		self.assertNotIn("omnexa_trading", apps)

	def test_free_auto_install_bundle_excludes_paid_dependency_apps(self):
		apps = get_free_auto_install_apps("عام")
		self.assertIn("omnexa_services", apps)
		self.assertIn("omnexa_backup", apps)
		self.assertIn("erpgenex_demo_studio", apps)
		self.assertNotIn("omnexa_fixed_assets", apps)

	def test_activity_filter_preserves_original_order(self):
		rows = [
			{"app_slug": "omnexa_core", "display_name": "Core"},
			{"app_slug": "omnexa_construction", "display_name": "Construction"},
			{"app_slug": "omnexa_education", "display_name": "Education"},
		]
		filtered = filter_apps_for_activity(rows, "مقاولات")
		self.assertEqual([row["app_slug"] for row in filtered], ["omnexa_core", "omnexa_construction"])

	def test_requested_base_apps_are_core_free(self):
		for app_slug in [
			"omnexa_services",
			"omnexa_edms",
			"omnexa_reporting_compliance",
			"omnexa_setup_intelligence",
			"omnexa_eng_document_control",
			"omnexa_eng_workflow_engine",
			"omnexa_eng_platform_integrations",
			"omnexa_backup",
			"erpgenex_demo_studio",
		]:
			payload = CatalogService._application_payload(app_slug)
			self.assertEqual(payload["distribution_type"], "Core Free", app_slug)
			self.assertEqual(payload["repository_is_private"], 0, app_slug)
			self.assertEqual(payload["is_core"], 1, app_slug)
