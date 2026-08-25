from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.services.github_distribution import parse_github_repository


class TestGithubDistribution(FrappeTestCase):
	def test_parse_github_repository(self):
		owner, repo = parse_github_repository("https://github.com/ErpGenex/omnexa_healthcare.git")
		self.assertEqual(owner, "ErpGenex")
		self.assertEqual(repo, "omnexa_healthcare")
