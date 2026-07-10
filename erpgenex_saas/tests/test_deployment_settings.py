from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.services.deployment_settings import (
	build_access_url,
	build_subdomain,
	get_deployment_config,
	normalize_subdomain,
)


class TestDeploymentSettings(FrappeTestCase):
	def test_normalize_subdomain_ascii(self):
		self.assertEqual(normalize_subdomain("مدرسة النور"), "tenant")
		self.assertEqual(normalize_subdomain("Al Noor School"), "al-noor-school")

	def test_build_subdomain(self):
		from erpgenex_saas.services.deployment_settings import DeploymentConfig

		config = DeploymentConfig(
			deployment_mode="Subdomain",
			start_port=8000,
			end_port=8999,
			server_host="localhost",
			use_https=False,
			root_domain="erpgenex.com",
			subdomain_pattern="{site}.{root_domain}",
		)
		self.assertEqual(build_subdomain("demo-school", config), "demo-school.erpgenex.com")

	def test_build_access_url_port_mode(self):
		url = build_access_url("192.168.1.100", port=8003, use_https=False)
		self.assertEqual(url, "http://192.168.1.100:8003")

	def test_get_deployment_config_defaults(self):
		config = get_deployment_config()
		self.assertIn(config.deployment_mode, ("Port", "Subdomain"))
		self.assertGreaterEqual(config.end_port, config.start_port)
