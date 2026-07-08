import frappe

from erpgenex_saas.bootstrap import ensure_default_packages, ensure_default_plans
from erpgenex_saas.services import CatalogService, MonitoringService, ProvisioningService, SubscriptionService


def process_due_provisioning_requests():
	requests = frappe.get_all(
		"Provisioning Request",
		filters={"status": "Queued", "docstatus": ("!=", 2)},
		fields=["name"],
		limit=20,
		order_by="creation asc",
	)
	for row in requests:
		ProvisioningService.enqueue_request(row.name)


def run_provisioning_request(request_name: str):
	ProvisioningService.run(request_name)


def expire_trials_and_grace_periods():
	SubscriptionService.mark_due_trials_and_grace_periods()


def generate_usage_snapshots():
	MonitoringService.record_usage_snapshot()


def sync_marketplace_catalog():
	CatalogService.sync_installed_apps_to_catalog(update_existing=True)
	ensure_default_plans()
	ensure_default_packages()
