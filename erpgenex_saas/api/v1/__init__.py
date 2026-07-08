from __future__ import annotations

import frappe

from erpgenex_saas.api import portal
from erpgenex_saas.services import MonitoringService, PackageBuilderService, SiteManagerService, SubscriptionService
from erpgenex_saas.services.domain import DomainService


@frappe.whitelist()
def get_openapi_spec():
	from erpgenex_saas.api.openapi import build_openapi_spec

	return build_openapi_spec()


@frappe.whitelist()
def platform_health():
	return MonitoringService.platform_snapshot()


@frappe.whitelist()
def package_quote(package: str, extra_users: int = 0, extra_storage_gb: float = 0):
	breakdown = PackageBuilderService.calculate_package_price(package, extra_users, extra_storage_gb)
	return breakdown.__dict__


@frappe.whitelist()
def suspend_tenant(tenant: str, reason: str = ""):
	frappe.only_for(("System Manager", "SaaS Admin"))
	return SiteManagerService.suspend_tenant(tenant, reason).as_dict()


@frappe.whitelist()
def resume_tenant(tenant: str):
	frappe.only_for(("System Manager", "SaaS Admin"))
	return SiteManagerService.resume_tenant(tenant).as_dict()


@frappe.whitelist()
def create_domain(tenant: str, domain_name: str, domain_type: str = "Custom Domain"):
	frappe.only_for(("System Manager", "SaaS Admin", "SaaS Customer"))
	return DomainService.create_domain(tenant, domain_name, domain_type).as_dict()


@frappe.whitelist(allow_guest=True)
def guest_quote(**kwargs):
	return portal.get_subscription_quote(**kwargs)


@frappe.whitelist(allow_guest=True)
def guest_register(**kwargs):
	return portal.register_customer(**kwargs)


@frappe.whitelist(allow_guest=True)
def get_provisioning_status(request_name: str):
	if not frappe.db.exists("Provisioning Request", request_name):
		frappe.throw("Provisioning request not found")
	doc = frappe.get_doc("Provisioning Request", request_name)
	return {
		"status": doc.status,
		"message": doc.last_message,
		"tenant": doc.tenant,
	}


@frappe.whitelist(allow_guest=True)
def start_provisioning(request_name: str):
	from erpgenex_saas.services.provisioning import ProvisioningService

	if not frappe.db.exists("Provisioning Request", request_name):
		frappe.throw("Provisioning request not found")
	doc = frappe.get_doc("Provisioning Request", request_name)
	if doc.status in ("Queued", "Failed"):
		ProvisioningService.run(request_name)
	return get_provisioning_status(request_name)


@frappe.whitelist()
def pause_subscription(subscription: str, reason: str = ""):
	frappe.only_for(("System Manager", "SaaS Admin", "SaaS Customer"))
	return SubscriptionService.pause(subscription, reason).as_dict()


@frappe.whitelist()
def resume_subscription(subscription: str):
	frappe.only_for(("System Manager", "SaaS Admin", "SaaS Customer"))
	return SubscriptionService.resume(subscription).as_dict()


@frappe.whitelist()
def cancel_subscription(subscription: str, reason: str = ""):
	frappe.only_for(("System Manager", "SaaS Admin", "SaaS Customer"))
	return SubscriptionService.cancel(subscription, reason).as_dict()
