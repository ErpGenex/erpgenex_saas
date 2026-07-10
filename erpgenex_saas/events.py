import frappe

from erpgenex_saas.services import PricingService, ProvisioningService, SubscriptionService


def validate_plan(doc, _method=None):
	if doc.minimum_users and doc.maximum_users and doc.minimum_users > doc.maximum_users:
		frappe.throw("Minimum users cannot exceed maximum users")


def validate_tenant(doc, _method=None):
	if doc.subdomain and " " in doc.subdomain:
		frappe.throw("Subdomain must not contain spaces")


def sync_tenant_status(doc, _method=None):
	if doc.status == "Suspended" and doc.active_subscription:
		frappe.logger("erpgenex_saas").info("Tenant %s suspended with active subscription", doc.name)


def validate_subscription(doc, _method=None):
	if doc.starts_on and doc.billing_cycle:
		doc.ends_on = SubscriptionService.compute_end_date(doc.starts_on, doc.billing_cycle)
	breakdown = PricingService.calculate(
		base_amount=doc.base_amount or 0,
		apps_amount=doc.apps_amount or 0,
		extra_users_amount=doc.extra_users_amount or 0,
		extra_storage_amount=doc.extra_storage_amount or 0,
		extra_services_amount=doc.extra_services_amount or 0,
	)
	doc.total_amount = breakdown.total_amount


def on_subscription_update(doc, _method=None):
	if doc.status == "Active" and doc.tenant:
		if frappe.db.get_value("SaaS Tenant", doc.tenant, "active_subscription") != doc.name:
			frappe.db.set_value(
				"SaaS Tenant",
				doc.tenant,
				"active_subscription",
				doc.name,
				update_modified=False,
			)
	if doc.status == "Active" and doc.provisioning_request and not doc.provisioned:
		ProvisioningService.enqueue_request(doc.provisioning_request)


def validate_request(doc, _method=None):
	if not doc.request_type:
		doc.request_type = "Initial Provisioning"
	if not doc.requested_by:
		doc.requested_by = frappe.session.user


def on_tenant_trash(doc, _method=None):
	from erpgenex_saas.services.deployment import DeploymentService

	DeploymentService.release_tenant_resources(doc.name)
