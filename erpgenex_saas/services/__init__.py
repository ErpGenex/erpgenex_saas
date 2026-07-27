from __future__ import annotations

from importlib import import_module

_EXPORTS = {
	"AuditService": "audit",
	"BillingService": "billing",
	"CatalogService": "catalog",
	"DomainService": "domain",
	"MonitoringService": "monitoring",
	"NotificationService": "notification",
	"PackageBuilderService": "package_builder",
	"PaymentService": "payment",
	"PricingService": "pricing",
	"ProvisioningService": "provisioning",
	"SiteManagerService": "site_manager",
	"SubscriptionService": "subscription",
	"LicenseManager": "license_manager",
	"ApplicationDistributionService": "application_distribution",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str):
	module_name = _EXPORTS.get(name)
	if not module_name:
		raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
	module = import_module(f".{module_name}", __name__)
	value = getattr(module, name)
	globals()[name] = value
	return value
