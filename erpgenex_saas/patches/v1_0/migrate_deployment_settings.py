import frappe

from erpgenex_saas.bootstrap import ensure_saas_settings, ensure_allocated_ports
from erpgenex_saas.runtime_config import get_root_domain


def execute():
	ensure_saas_settings()
	ensure_allocated_ports()
	settings = frappe.get_single("SaaS Settings")
	if not settings.deployment_mode:
		settings.deployment_mode = "Port"
	if not settings.start_port:
		settings.start_port = 8000
	if not settings.end_port:
		settings.end_port = 8999
	if not settings.server_host:
		settings.server_host = settings.server_ip or "localhost"
	if not settings.root_domain:
		settings.root_domain = settings.platform_domain or get_root_domain()
	if not settings.subdomain_pattern:
		settings.subdomain_pattern = "{site}.{root_domain}"
	settings.save(ignore_permissions=True)
	print("Deployment settings migrated to Port mode defaults")
