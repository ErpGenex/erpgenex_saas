import frappe
from frappe.tests.utils import FrappeTestCase

from erpgenex_saas.services.audit import AuditService
from erpgenex_saas.services.domain import DomainService
from erpgenex_saas.services.monitoring import MonitoringService
from erpgenex_saas.services.subscription import SubscriptionService


class TestMonitoringService(FrappeTestCase):
	def test_platform_snapshot(self):
		snapshot = MonitoringService.platform_snapshot()
		self.assertIn("tenants", snapshot)
		self.assertIn("active_tenants", snapshot)

	def test_record_usage_snapshot(self):
		before = frappe.db.count("SaaS Usage Snapshot")
		MonitoringService.record_usage_snapshot()
		after = frappe.db.count("SaaS Usage Snapshot")
		self.assertEqual(after, before + 1)


class TestDomainService(FrappeTestCase):
	def test_create_domain(self):
		tenant = frappe.get_doc(
			{
				"doctype": "SaaS Tenant",
				"tenant_name": "Domain Test Tenant",
				"company_email": f"domain-{frappe.generate_hash(length=6)}@example.com",
				"subdomain": f"domain-{frappe.generate_hash(length=6).lower()}",
			}
		).insert(ignore_permissions=True)
		domain_name = f"{tenant.subdomain}.test.local"
		domain = DomainService.create_domain(tenant.name, domain_name)
		self.assertEqual(domain.domain_name, domain_name)
		verified = DomainService.verify_domain(domain_name)
		self.assertEqual(verified.status, "Verified")


class TestSubscriptionLifecycle(FrappeTestCase):
	def test_pause_resume_cancel(self):
		plan_name = "Lifecycle Plan"
		if not frappe.db.exists("SaaS Plan", plan_name):
			frappe.get_doc(
				{
					"doctype": "SaaS Plan",
					"plan_name": plan_name,
					"billing_cycle": "Monthly",
					"base_price": 50,
				}
			).insert(ignore_permissions=True)

		tenant = frappe.get_doc(
			{
				"doctype": "SaaS Tenant",
				"tenant_name": "Lifecycle Tenant",
				"company_email": f"lifecycle-{frappe.generate_hash(length=6)}@example.com",
				"subdomain": f"lifecycle-{frappe.generate_hash(length=6).lower()}",
				"status": "Active",
			}
		).insert(ignore_permissions=True)

		subscription = frappe.get_doc(
			{
				"doctype": "SaaS Subscription",
				"tenant": tenant.name,
				"plan": plan_name,
				"billing_cycle": "Monthly",
				"starts_on": "2026-07-08",
				"status": "Active",
				"base_amount": 50,
			}
		).insert(ignore_permissions=True)

		paused = SubscriptionService.pause(subscription.name, "maintenance")
		self.assertEqual(paused.status, "Paused")
		resumed = SubscriptionService.resume(subscription.name)
		self.assertEqual(resumed.status, "Active")
		cancelled = SubscriptionService.cancel(subscription.name, "customer request")
		self.assertEqual(cancelled.status, "Cancelled")
		self.assertEqual(frappe.db.get_value("SaaS Tenant", tenant.name, "status"), "Suspended")


class TestAuditService(FrappeTestCase):
	def test_audit_log(self):
		before = frappe.db.count("SaaS Audit Log")
		AuditService.log("test.event", "REF-001", {"ok": True})
		after = frappe.db.count("SaaS Audit Log")
		self.assertEqual(after, before + 1)
