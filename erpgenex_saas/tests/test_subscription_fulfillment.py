from frappe.tests.utils import FrappeTestCase
from frappe.utils import getdate

from erpgenex_saas.services.billing import BillingService
from erpgenex_saas.services.subscription import SubscriptionService
from erpgenex_saas.services.subscription_fulfillment import SubscriptionFulfillmentService


class TestSubscriptionFulfillment(FrappeTestCase):
	def test_subscribe_creates_draft_subscription(self):
		if not self._has_prerequisites():
			return

		tenant = self._ensure_tenant()
		application = self._paid_application()
		sub = SubscriptionService.subscribe_to_application(tenant, application, "Monthly")
		self.assertEqual(sub.status, "Draft")
		self.assertEqual(int(sub.features_enabled or 0), 0)

	def test_payment_activates_subscription_and_license(self):
		if not self._has_prerequisites():
			return

		tenant = self._ensure_tenant()
		application = self._paid_application()
		sub = SubscriptionService.subscribe_to_application(tenant, application, "Annual")
		invoice = BillingService.create_invoice_for_subscription(sub.name)
		BillingService.register_payment(invoice.name, float(invoice.amount_due or 0), "PayPal", "TEST-PAY-1")
		result = SubscriptionFulfillmentService.activate_paid_invoice(invoice.name)

		self.assertTrue(result.get("activated"))
		self.assertTrue(result.get("license_key"))
		self.assertEqual(
			getdate(result.get("ends_on")).isoformat(),
			SubscriptionService.compute_end_date(result.get("starts_on"), "Annual").isoformat(),
		)

	def _has_prerequisites(self) -> bool:
		import frappe

		return bool(
			frappe.db.exists("DocType", "SaaS Tenant")
			and frappe.db.get_all("SaaS Application", filters={"is_core": 0}, pluck="name", limit=1)
			and frappe.db.get_all("SaaS Plan", filters={"billing_cycle": "Monthly", "is_active": 1}, pluck="name", limit=1)
		)

	def _ensure_tenant(self) -> str:
		import frappe

		name = frappe.db.get_value("SaaS Tenant", {}, "name")
		if name:
			return name
		doc = frappe.get_doc(
			{
				"doctype": "SaaS Tenant",
				"tenant_name": "test-fulfillment-tenant",
				"company_email": "test-fulfillment@example.com",
				"status": "Draft",
				"site_name": "test-fulfillment.local",
			}
		)
		doc.insert(ignore_permissions=True)
		return doc.name

	def _paid_application(self) -> str:
		import frappe

		return frappe.get_all("SaaS Application", filters={"is_core": 0}, pluck="name", limit=1)[0]
