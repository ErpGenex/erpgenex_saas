from __future__ import annotations

import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import frappe
from frappe.utils import get_bench_path

from erpgenex_saas.services.deployment_settings import (
	DeploymentConfig,
	build_access_url,
	build_subdomain,
	get_deployment_config,
	normalize_subdomain,
)
from erpgenex_saas.services.domain import DomainService
from erpgenex_saas.services.port_manager import PortManager
from erpgenex_saas.services.provisioning_logger import ProvisioningLogger
from erpgenex_saas.services.service_manager import ServiceManager


class DeploymentService:
	@staticmethod
	def resolve_site_folder(site_name: str) -> str:
		if ":" in site_name:
			base, port = site_name.split(":", 1)
			return f"{base}_port_{port}"
		return site_name

	@staticmethod
	def deploy_tenant(
		tenant_name: str,
		site_folder: str,
		request_name: str | None = None,
		*,
		subdomain_slug: str | None = None,
	) -> dict:
		config = get_deployment_config()
		tenant = frappe.get_doc("SaaS Tenant", tenant_name)
		logger = ProvisioningLogger(tenant_name, request_name)
		tenant.deployment_mode = config.deployment_mode
		tenant.site_folder = site_folder

		try:
			with logger.stage("Deployment") as stage_log:
				if config.deployment_mode == "Port":
					result = DeploymentService._deploy_port_mode(
						tenant, site_folder, config, stage_log
					)
				else:
					result = DeploymentService._deploy_subdomain_mode(
						tenant, site_folder, config, subdomain_slug, stage_log
					)

			with logger.stage("Health Check") as stage_log:
				check_urls = DeploymentService.build_health_check_urls(result["access_url"], result.get("port"))
				healthy = False
				for url in check_urls:
					if DeploymentService.health_check_url(url):
						healthy = True
						stage_log.stdout = f"Health check passed: {url}"
						break
				if not healthy:
					stage_log.stdout = f"Tried URLs: {check_urls}"
					raise RuntimeError(f"Health check failed for {result['access_url']}")

			tenant.health_status = "Healthy"
			tenant.service_status = result.get("service_status", "Running")
			tenant.last_health_check = frappe.utils.now_datetime()
			tenant.save(ignore_permissions=True)
			return result
		except Exception as exc:
			DeploymentService.rollback_tenant(
				tenant_name,
				site_folder,
				reason=str(exc),
				request_name=request_name,
			)
			raise

	@staticmethod
	def _deploy_port_mode(tenant, site_folder: str, config: DeploymentConfig, stage_log) -> dict:
		port_manager = PortManager()
		port = port_manager.get_available_port()
		port_manager.reserve_port(port, tenant.name, site_folder)

		service = ServiceManager()
		service_info = service.create_service(site_folder, port)
		time.sleep(3)
		port_manager.mark_running(port, service_info.get("pid"))
		stage_log.stdout = f"Service started: {service_info}"

		access_url = build_access_url(config.server_host, port=port, use_https=config.use_https)
		domain_label = f"{config.server_host}:{port}"

		tenant.port_number = port
		tenant.domain = domain_label
		tenant.access_url = access_url
		tenant.site_url = access_url
		tenant.site_name = domain_label
		tenant.service_status = "Running"
		tenant.save(ignore_permissions=True)

		if not frappe.db.exists("SaaS Domain", {"domain_name": domain_label, "tenant": tenant.name}):
			DomainService.create_domain(tenant.name, domain_label, "Subdomain")

		stage_log.stdout = f"Port {port} allocated\nService: {service_info}\nURL: {access_url}"
		return {
			"deployment_mode": "Port",
			"port": port,
			"domain": domain_label,
			"access_url": access_url,
			"service_status": "Running",
		}

	@staticmethod
	def _deploy_subdomain_mode(
		tenant,
		site_folder: str,
		config: DeploymentConfig,
		subdomain_slug: str | None,
		stage_log,
	) -> dict:
		slug = normalize_subdomain(subdomain_slug or tenant.subdomain or tenant.name)
		domain = build_subdomain(slug, config)
		access_url = build_access_url("", domain=domain, use_https=config.use_https)

		DeploymentService._configure_subdomain_proxy(site_folder, domain, stage_log)

		tenant.port_number = None
		tenant.domain = domain
		tenant.access_url = access_url
		tenant.site_url = access_url
		tenant.site_name = domain
		tenant.service_status = "Running"
		tenant.save(ignore_permissions=True)

		if not frappe.db.exists("SaaS Domain", {"domain_name": domain, "tenant": tenant.name}):
			DomainService.create_domain(tenant.name, domain, "Subdomain")

		stage_log.stdout = f"Subdomain configured: {domain}\nURL: {access_url}"
		return {
			"deployment_mode": "Subdomain",
			"domain": domain,
			"access_url": access_url,
			"service_status": "Running",
		}

	@staticmethod
	def _configure_subdomain_proxy(site_folder: str, domain: str, stage_log):
		bench_path = get_bench_path()
		commands = [
			["bench", "--site", site_folder, "add-to-hosts"],
			["bench", "setup", "add-domain", site_folder, domain, "--ssl", "0"],
			["bench", "setup", "nginx"],
		]
		for command in commands:
			result = subprocess.run(
				command,
				cwd=bench_path,
				capture_output=True,
				text=True,
				timeout=120,
				check=False,
			)
			stage_log.stdout = (stage_log.stdout or "") + f"\n$ {' '.join(command)}\n{result.stdout}"
			if result.stderr:
				stage_log.stderr = (stage_log.stderr or "") + result.stderr
			if result.returncode != 0 and command[1] != "add-to-hosts":
				raise RuntimeError(result.stderr or result.stdout or f"Command failed: {command}")

		reload = subprocess.run(
			["sudo", "nginx", "-s", "reload"],
			cwd=bench_path,
			capture_output=True,
			text=True,
			timeout=30,
			check=False,
		)
		if reload.returncode != 0:
			stage_log.stderr = (stage_log.stderr or "") + (reload.stderr or "nginx reload skipped")

	@staticmethod
	def build_health_check_urls(access_url: str, port: int | None = None) -> list[str]:
		urls = []
		if port:
			urls.extend([f"http://127.0.0.1:{port}", f"http://localhost:{port}"])
		if access_url and access_url not in urls:
			urls.append(access_url)
		return urls

	@staticmethod
	def health_check_url(url: str, timeout: int = 15, retries: int = 8) -> bool:
		for attempt in range(retries):
			try:
				request = urllib.request.Request(url, method="GET")
				with urllib.request.urlopen(request, timeout=timeout) as response:
					if 200 <= response.status < 500:
						return True
			except (urllib.error.URLError, TimeoutError, ValueError):
				time.sleep(min(2 * (attempt + 1), 8))
		return False

	@staticmethod
	def check_tenant_health(tenant_name: str) -> dict:
		tenant = frappe.get_doc("SaaS Tenant", tenant_name)
		url = tenant.access_url or tenant.site_url
		healthy = DeploymentService.health_check_url(url) if url else False
		service = ServiceManager()
		site_folder = tenant.site_folder or DeploymentService.resolve_site_folder(tenant.site_name or "")
		running = service.is_running(site_folder) if site_folder else False

		tenant.health_status = "Healthy" if healthy else "Unhealthy"
		tenant.service_status = "Running" if running else "Stopped"
		tenant.last_health_check = frappe.utils.now_datetime()
		tenant.save(ignore_permissions=True)

		if tenant.port_number:
			port_manager = PortManager()
			if healthy and running:
				port_manager.mark_running(int(tenant.port_number))
			elif not healthy:
				port_manager.mark_failed(int(tenant.port_number), "Health check failed")

		return {
			"tenant": tenant_name,
			"access_url": url,
			"healthy": healthy,
			"service_running": running,
			"health_status": tenant.health_status,
			"service_status": tenant.service_status,
			"last_health_check": str(tenant.last_health_check),
		}

	@staticmethod
	def restart_tenant_service(tenant_name: str) -> dict:
		tenant = frappe.get_doc("SaaS Tenant", tenant_name)
		if tenant.deployment_mode != "Port" or not tenant.port_number:
			frappe.throw("Restart Service is only available for Port mode tenants")
		site_folder = tenant.site_folder or DeploymentService.resolve_site_folder(tenant.site_name or "")
		service = ServiceManager()
		info = service.restart_service(site_folder, int(tenant.port_number))
		tenant.service_status = "Running"
		tenant.save(ignore_permissions=True)
		PortManager().mark_running(int(tenant.port_number), info.get("pid"))
		return {"tenant": tenant_name, "service": info}

	@staticmethod
	def get_tenant_logs(tenant_name: str, tail: int = 200) -> str:
		tenant = frappe.get_doc("SaaS Tenant", tenant_name)
		site_folder = tenant.site_folder or DeploymentService.resolve_site_folder(tenant.site_name or "")
		return ServiceManager().read_logs(site_folder, tail=tail)

	@staticmethod
	def release_tenant_resources(tenant_name: str):
		tenant = frappe.db.get_value(
			"SaaS Tenant",
			tenant_name,
			["port_number", "site_folder", "site_name", "deployment_mode"],
			as_dict=True,
		)
		if not tenant:
			return

		site_folder = tenant.site_folder or DeploymentService.resolve_site_folder(tenant.site_name or "")
		if site_folder:
			ServiceManager().stop_service(site_folder)

		if tenant.port_number:
			PortManager().release_port(int(tenant.port_number))

	@staticmethod
	def rollback_tenant(
		tenant_name: str,
		site_folder: str,
		reason: str = "",
		request_name: str | None = None,
	):
		from erpgenex_saas.services.provisioning import ProvisioningService

		logger = ProvisioningLogger(tenant_name, request_name)
		with logger.stage("Rollback") as stage_log:
			DeploymentService.release_tenant_resources(tenant_name)
			ProvisioningService.rollback_site_folder(site_folder)
			ProvisioningService.rollback_database(site_folder)
			frappe.db.set_value(
				"SaaS Tenant",
				tenant_name,
				{
					"status": "Draft",
					"provisioned_on": None,
					"service_status": "Failed",
					"health_status": "Unhealthy",
					"access_url": None,
				},
				update_modified=True,
			)
			stage_log.stderr = reason
