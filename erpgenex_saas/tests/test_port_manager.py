from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.services.port_manager import PortManager


class TestPortManager(FrappeTestCase):
	def test_reserve_and_release_port(self):
		tenant = frappe.get_doc(
			{
				"doctype": "SaaS Tenant",
				"tenant_name": f"Port Test {frappe.generate_hash(length=6)}",
				"company_email": f"port-{frappe.generate_hash(length=6)}@example.com",
				"subdomain": f"port-{frappe.generate_hash(length=6).lower()}",
			}
		).insert(ignore_permissions=True)

		manager = PortManager()
		with patch.object(PortManager, "_is_port_in_use_os", return_value=False):
			port = manager.get_available_port(start=8700)
			manager.reserve_port(port, tenant.name, tenant.subdomain)

		self.assertTrue(frappe.db.exists("Allocated Port", f"PORT-{port}"))
		self.assertEqual(frappe.db.get_value("SaaS Tenant", tenant.name, "port_number"), port)

		manager.release_port(port)
		self.assertEqual(
			frappe.db.get_value("Allocated Port", f"PORT-{port}", "status"),
			"Free",
		)
