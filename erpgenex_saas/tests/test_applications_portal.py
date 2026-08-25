import frappe
from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.api.portal import get_applications_portal_state as api_get_applications_portal_state
from erpgenex_saas.services.applications_portal import get_applications_portal_state, mask_license_key


class TestApplicationsPortal(FrappeTestCase):
	def test_mask_license_key(self):
		key = "EGX-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
		masked = mask_license_key(key)
		self.assertIn("…", masked)
		self.assertNotEqual(masked, key)

	def test_portal_state_guest(self):
		state = get_applications_portal_state(user="Guest")
		self.assertFalse(state["logged_in"])
		self.assertEqual(state["installed_summary"], [])

	def test_api_portal_state_guest_access(self):
		previous = frappe.session.user
		try:
			frappe.set_user("Guest")
			state = api_get_applications_portal_state()
			self.assertFalse(state["logged_in"])
			self.assertIn("marketplace", state)
		finally:
			frappe.set_user(previous)
