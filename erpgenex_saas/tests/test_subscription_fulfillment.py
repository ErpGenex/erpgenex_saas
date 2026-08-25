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
		self._site_plan("Annual")
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

	def test_payment_activates_tenant_subscription(self):
		if not self._has_prerequisites():
			return

		import frappe

		tenant = self._ensure_tenant()
		plan = self._site_plan("Monthly")
		subscription = frappe.get_doc(
			{
				"doctype": "SaaS Subscription",
				"tenant": tenant,
				"plan": plan,
				"billing_cycle": "Monthly",
				"starts_on": "2026-07-08",
				"base_amount": 100,
			}
		).insert(ignore_permissions=True)
		invoice = BillingService.create_invoice_for_subscription(subscription.name)
		BillingService.register_payment(invoice.name, float(invoice.amount_due or 0), "PayPal", "TEST-PAY-2")
		result = SubscriptionFulfillmentService.activate_paid_invoice(invoice.name)

		self.assertTrue(result.get("activated"))
		self.assertEqual(result.get("tenant"), tenant)
		self.assertEqual(frappe.db.get_value("SaaS Tenant", tenant, "status"), "Active")
		self.assertEqual(frappe.db.get_value("SaaS Tenant", tenant, "active_subscription"), subscription.name)
		self.assertEqual(frappe.db.get_value("SaaS Subscription", subscription.name, "status"), "Active")
		self.assertEqual(
			getdate(result.get("ends_on")).isoformat(),
			SubscriptionService.compute_end_date(result.get("starts_on"), "Monthly").isoformat(),
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
			tenant = frappe.get_doc("SaaS Tenant", name)
			if not tenant.site_name:
				tenant.site_name = "test-fulfillment.local"
			if not tenant.site_folder:
				tenant.site_folder = "test-fulfillment.local"
			if tenant.status not in ("Draft", "Provisioning", "Active", "Suspended", "Archived"):
				tenant.status = "Draft"
			tenant.save(ignore_permissions=True)
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

	def _site_plan(self, billing_cycle: str) -> str:
		import frappe

		plan = frappe.db.get_value(
			"SaaS Plan",
			{"billing_cycle": billing_cycle, "is_active": 1},
			"name",
		)
		if plan:
			return plan
		plan_doc = frappe.get_doc(
			{
				"doctype": "SaaS Plan",
				"plan_name": f"Test {billing_cycle} Plan",
				"billing_cycle": billing_cycle,
				"base_price": 100,
				"is_active": 1,
			}
		)
		plan_doc.insert(ignore_permissions=True)
		return plan_doc.name
