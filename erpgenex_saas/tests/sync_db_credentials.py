"""Sync MariaDB credentials into SaaS Settings from bench environment."""
from __future__ import annotations

import json
from pathlib import Path

import frappe


def _detect_mariadb_root_password() -> str | None:
	candidates = ["Microhard2610"]
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
	main_config_path = Path("/home/frappeuser/frappe-bench/sites/erpgenex.local.site/site_config.json")
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
				"mariadb_root_password_set": bool(root_password),
			}
		)
	)
