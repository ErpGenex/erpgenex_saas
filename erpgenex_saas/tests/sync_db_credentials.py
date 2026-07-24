"""Sync MariaDB credentials into SaaS Settings from bench environment."""
from __future__ import annotations

import os
import json
from pathlib import Path

import frappe
from frappe.utils import get_bench_path


def _detect_mariadb_root_password() -> str | None:
	candidates = [
		os.environ.get("ERPGENEX_SAAS_MARIADB_ROOT_PASSWORD"),
		os.environ.get("MARIADB_ROOT_PASSWORD"),
		os.environ.get("MYSQL_ROOT_PASSWORD"),
	]
	candidates = [candidate for candidate in candidates if candidate]
	for password in candidates:
		try:
			import pymysql

			conn = pymysql.connect(
				host="localhost",
				user="root",
				password=password,
				charset="utf8mb4",
			)
			conn.close()
			return password
		except Exception:
			continue
	return None


def run():
	site_name = getattr(frappe.local, "site", None)
	if not site_name:
		from erpgenex_saas.runtime_config import get_main_site_name
		site_name = get_main_site_name()
	if not site_name:
		raise frappe.ValidationError("Unable to resolve the current site name")
	main_config_path = Path(get_bench_path()) / "sites" / site_name / "site_config.json"
	main_config = json.loads(main_config_path.read_text(encoding="utf-8"))
	db_password = main_config.get("db_password")
	root_password = _detect_mariadb_root_password()

	settings = frappe.get_single("SaaS Settings")
	if db_password:
		settings.database_password = db_password
	if root_password:
		settings.mariadb_root_password = root_password
	settings.save(ignore_permissions=True)
	frappe.db.commit()

	print(
		json.dumps(
			{
				"database_password_set": bool(db_password),
				"mariadb_root_password_set": bool(root_password)
	}
		)
	)
