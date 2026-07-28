from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.services.applications_portal import get_applications_portal_state, mask_license_key


class TestApplicationsPortal(FrappeTestCase):
	def test_mask_license_key(self):
		key = "EGX-ABCDEFGHIJKLMNOPQRSTUVWXYZ"
		masked = mask_license_key(key)
		self.assertIn("…", masked)
		self.assertNotEqual(masked, key)

	def test_portal_state_guest(self):
		previous = self.session.user
		try:
			self.set_user("Guest")
			state = get_applications_portal_state()
			self.assertFalse(state["logged_in"])
			self.assertEqual(state["installed_summary"], [])
		finally:
			self.set_user(previous)
