from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.api.portal import _is_valid_company_email


class TestPortalRegistration(FrappeTestCase):
	def test_company_email_validation_accepts_normal_domains(self):
		self.assertTrue(_is_valid_company_email("customer@example.com"))
		self.assertTrue(_is_valid_company_email("customer@example.co.uk"))

	def test_company_email_validation_rejects_invalid_values(self):
		self.assertFalse(_is_valid_company_email("customer@"))
		self.assertFalse(_is_valid_company_email("not-an-email"))
