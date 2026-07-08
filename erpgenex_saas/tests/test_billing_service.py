import frappe
from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.services.billing import BillingService


class TestBillingService(FrappeTestCase):
	def setUp(self):
		super().setUp()
		if not frappe.db.exists("Currency", "USD"):
			frappe.get_doc(
				{"doctype": "Currency", "currency_name": "USD", "symbol": "$", "enabled": 1}
			).insert(ignore_permissions=True)

	def test_create_invoice_and_register_payment(self):
		plan_name = "Test Billing Plan"
		if not frappe.db.exists("SaaS Plan", plan_name):
			frappe.get_doc(
				{
					"doctype": "SaaS Plan",
					"plan_name": plan_name,
					"billing_cycle": "Monthly",
					"base_price": 100,
				}
			).insert(ignore_permissions=True)

		tenant = frappe.get_doc(
			{
				"doctype": "SaaS Tenant",
				"tenant_name": "Tenant Billing Test",
				"company_email": "billing@example.com",
				"subdomain": f"tenant-billing-{frappe.generate_hash(length=6).lower()}",
			}
		).insert(ignore_permissions=True)

		subscription = frappe.get_doc(
			{
				"doctype": "SaaS Subscription",
				"tenant": tenant.name,
				"plan": plan_name,
				"billing_cycle": "Monthly",
				"starts_on": "2026-07-08",
				"base_amount": 100,
				"apps_amount": 20,
			}
		).insert(ignore_permissions=True)

		invoice = BillingService.create_invoice_for_subscription(subscription.name)
		self.assertEqual(float(invoice.amount_due), 120.0)

		payment = BillingService.register_payment(invoice.name, 120, "PayPal", frappe.generate_hash(length=10))
		self.assertEqual(payment.provider, "PayPal")
		self.assertEqual(frappe.db.get_value("SaaS Invoice", invoice.name, "status"), "Paid")
