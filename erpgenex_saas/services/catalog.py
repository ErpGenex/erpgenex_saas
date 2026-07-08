from __future__ import annotations

import re
from pathlib import Path

import frappe
from frappe.utils import get_bench_path

from erpgenex_saas.constants import (
	DEFAULT_APP_PRICE,
	DEFAULT_APP_PRICES_BY_CATEGORY,
	INCLUDED_APPS,
	BRAND_REPLACEMENTS,
)


class CatalogService:
	@staticmethod
	def normalize_brand(text: str) -> str:
		result = (text or "").strip()
		for old, new in BRAND_REPLACEMENTS:
			result = result.replace(old, new)
		result = re.sub(r"\s*[—–-]\s*", " — ", result)
		result = re.sub(r"\s+", " ", result).strip(" —")
		return result

	@staticmethod
	def _get_hooks_metadata(app_name: str) -> dict:
		try:
			hooks = frappe.get_module(f"{app_name}.hooks")
			return {
				"title": getattr(hooks, "app_title", None),
				"description": getattr(hooks, "app_description", None),
				"publisher": getattr(hooks, "app_publisher", None),
			}
		except Exception:
			return {}

	@staticmethod
	def _build_display_name(app_name: str) -> str:
		meta = CatalogService._get_hooks_metadata(app_name)
		if meta.get("title"):
			return CatalogService.normalize_brand(meta["title"])

		label = app_name
		if label.startswith("omnexa_"):
			label = "erpgenex_" + label[len("omnexa_") :]
		label = label.replace("_", " ")
		label = re.sub(r"\b(omnexa|erpgenex)\b", "ErpGenex", label, flags=re.I)
		return CatalogService.normalize_brand(label.title())

	@staticmethod
	def _build_description(app_name: str) -> str:
		meta = CatalogService._get_hooks_metadata(app_name)
		if meta.get("description"):
			return CatalogService.normalize_brand(meta["description"])
		display = CatalogService._build_display_name(app_name)
		return f"{display} — modular ErpGenex business application for your tenant workspace."

	@staticmethod
	def _infer_category(app_name: str) -> str:
		slug = app_name.lower()
		rules = (
			("healthcare", "Healthcare"),
			("education", "Education"),
			("hr", "HR"),
			("accounting", "Accounting"),
			("trading", "Trading"),
			("manufacturing", "Manufacturing"),
			("restaurant", "POS"),
			("finance", "Accounting"),
			("credit", "Analytics"),
			("risk", "Analytics"),
			("ai_", "AI"),
			("construction", "Manufacturing"),
			("realestate", "CRM"),
			("property", "CRM"),
			("maintenance", "Projects"),
			("tourism", "Other"),
			("agriculture", "Other"),
			("nursery", "Other"),
			("edms", "Other"),
			("audit", "Analytics"),
			("einvoice", "Accounting"),
			("core", "Core"),
			("theme", "Website"),
			("experience", "Website"),
		)
		for needle, category in rules:
			if needle in slug:
				return category
		return "Other"

	@staticmethod
	def _default_monthly_price(app_name: str, category: str) -> float:
		if app_name in INCLUDED_APPS:
			return 0.0
		return float(DEFAULT_APP_PRICES_BY_CATEGORY.get(category, DEFAULT_APP_PRICE))

	@staticmethod
	def _application_payload(app_name: str) -> dict:
		category = CatalogService._infer_category(app_name)
		return {
			"application_name": app_name,
			"display_name": CatalogService._build_display_name(app_name),
			"app_slug": app_name,
			"category": category,
			"description": CatalogService._build_description(app_name),
			"monthly_price": CatalogService._default_monthly_price(app_name, category),
			"is_active": 1,
		}

	@staticmethod
	def sync_installed_apps_to_catalog(update_existing: bool = True):
		apps_file = Path(get_bench_path()) / "sites" / "apps.txt"
		if not apps_file.exists():
			return []

		changed = []
		for line in apps_file.read_text(encoding="utf-8").splitlines():
			app_name = line.strip()
			if not app_name:
				continue

			payload = CatalogService._application_payload(app_name)
			if frappe.db.exists("SaaS Application", app_name):
				if not update_existing:
					continue
				doc = frappe.get_doc("SaaS Application", app_name)
				doc.display_name = payload["display_name"]
				doc.category = payload["category"]
				doc.description = payload["description"]
				if not doc.monthly_price:
					doc.monthly_price = payload["monthly_price"]
				doc.is_active = 1
				doc.save(ignore_permissions=True)
				changed.append(doc.name)
				continue

			try:
				doc = frappe.get_doc({"doctype": "SaaS Application", **payload})
				doc.insert(ignore_permissions=True)
				changed.append(doc.name)
			except frappe.DuplicateEntryError:
				continue
		return changed

	@staticmethod
	def rebrand_all_applications(reset_prices: bool = False):
		"""Force ErpGenex branding on every marketplace app record."""
		updated = []
		for row in frappe.get_all("SaaS Application", pluck="name"):
			app_name = row
			payload = CatalogService._application_payload(app_name)
			doc = frappe.get_doc("SaaS Application", app_name)
			doc.display_name = payload["display_name"]
			doc.description = payload["description"]
			doc.category = payload["category"]
			if reset_prices or not doc.monthly_price:
				doc.monthly_price = payload["monthly_price"]
			doc.save(ignore_permissions=True)
			updated.append(app_name)
		return updated

	@staticmethod
	def list_active_applications():
		return frappe.get_all(
			"SaaS Application",
			filters={"is_active": 1},
			fields=["name", "display_name", "app_slug", "monthly_price", "category", "description"],
			order_by="display_name asc",
		)


def rebrand_marketplace_apps(reset_prices: bool = False):
	return CatalogService.rebrand_all_applications(reset_prices=reset_prices)
