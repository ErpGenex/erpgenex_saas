from __future__ import annotations

from dataclasses import dataclass

import frappe


@dataclass
class DeploymentConfig:
	deployment_mode: str
	start_port: int
	end_port: int
	server_host: str
	use_https: bool
	root_domain: str
	subdomain_pattern: str


def get_deployment_config() -> DeploymentConfig:
	settings = frappe.get_single("SaaS Settings")
	mode = settings.deployment_mode or settings.site_distribution_method or "Port"
	return DeploymentConfig(
		deployment_mode=mode,
		start_port=int(settings.start_port or settings.base_port or 8000),
		end_port=int(settings.end_port or settings.max_port or 8999),
		server_host=(settings.server_host or settings.server_ip or "localhost").strip(),
		use_https=bool(settings.use_https),
		root_domain=(settings.root_domain or settings.platform_domain or "erpgenex.local").strip(),
		subdomain_pattern=(settings.subdomain_pattern or "{site}.{root_domain}").strip(),
	)


def build_subdomain(subdomain_slug: str, config: DeploymentConfig | None = None) -> str:
	config = config or get_deployment_config()
	site = subdomain_slug.lower().replace(" ", "-").replace("_", "-")
	pattern = config.subdomain_pattern.replace("{root_domain}", config.root_domain)
	return pattern.replace("{site}", site)


def build_access_url(
	host: str,
	port: int | None = None,
	domain: str | None = None,
	use_https: bool = False,
) -> str:
	scheme = "https" if use_https else "http"
	if domain:
		return f"{scheme}://{domain}"
	if port:
		return f"{scheme}://{host}:{port}"
	return f"{scheme}://{host}"


def normalize_subdomain(value: str) -> str:
	import re

	slug = (value or "").strip().lower()
	slug = slug.replace(" ", "-").replace("_", "-")
	slug = re.sub(r"[^a-z0-9-]", "", slug)
	slug = re.sub(r"-+", "-", slug).strip("-")
	return slug or "tenant"
