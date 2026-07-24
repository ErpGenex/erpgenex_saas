from __future__ import annotations

import os
import re
from urllib.parse import urlparse

import frappe


def get_main_site_name() -> str:
	value = frappe.conf.get("erpgenex_saas_main_site") or os.environ.get("ERPGENEX_SAAS_MAIN_SITE") or ""
	return str(value).strip()


def get_root_domain() -> str:
	value = (
		frappe.conf.get("erpgenex_saas_root_domain")
		or os.environ.get("ERPGENEX_SAAS_ROOT_DOMAIN")
		or frappe.conf.get("host_name")
		or "localhost"
	)
	root = str(value).strip()
	if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", root):
		return "localhost"
	return root or "localhost"


def get_server_host() -> str:
	value = (
		frappe.conf.get("erpgenex_saas_server_host")
		or frappe.conf.get("erpgenex_saas_server_ip")
		or os.environ.get("ERPGENEX_SAAS_SERVER_HOST")
		or os.environ.get("ERPGENEX_SAAS_SERVER_IP")
		or frappe.conf.get("host_name")
		or "localhost"
	)
	host = str(value).strip()
	if not host:
		return "localhost"

	parsed = urlparse(host if "://" in host else f"//{host}")
	normalized = parsed.hostname or host
	if parsed.port:
		return f"{normalized}:{parsed.port}"
	return normalized


def get_email_domain() -> str:
	value = frappe.conf.get("erpgenex_saas_email_domain") or os.environ.get("ERPGENEX_SAAS_EMAIL_DOMAIN")
	if value:
		return str(value).strip() or "example.invalid"
	return "example.invalid"


def is_main_site(site_name: str | None = None) -> bool:
	site = str(site_name or getattr(frappe.local, "site", "") or "").strip()
	if not site:
		return False

	configured = get_main_site_name()
	if configured:
		return site == configured

	try:
		if not frappe.db.table_exists("SaaS Tenant"):
			return False
		return not bool(frappe.db.exists("SaaS Tenant", {"site_name": site}))
	except Exception:
		return False


def get_site_url(port: int | str | None = None, scheme: str = "http") -> str:
	host = get_server_host()
	if port in (None, "", 0):
		return f"{scheme}://{host}"
	return f"{scheme}://{host.split(':', 1)[0]}:{port}"
