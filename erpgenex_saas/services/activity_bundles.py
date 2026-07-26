from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe.utils import get_bench_path

# Core + basic platform stack (installed with omnexa_core bootstrap).
CORE_PLATFORM_APPS = (
	"frappe",
	"omnexa_core",
	"omnexa_accounting",
	"omnexa_fixed_assets",
	"omnexa_hr",
	"omnexa_projects_pm",
	"omnexa_ai_employee",
	"omnexa_customer_core",
	"omnexa_einvoice",
	"omnexa_experience",
	"omnexa_intelligence_core",
	"omnexa_n8n_bridge",
	"omnexa_user_academy",
	"omnexa_statutory_audit",
	"omnexa_theme_manager",
	"omnexa_trading",
)

ACTIVITY_VERTICAL_APPS = {
	"عام": (),
	"مقاولات": ("omnexa_construction",),
	"تعليمي": ("omnexa_education",),
}

ACTIVITY_LABELS = {
	"عام": "General",
	"مقاولات": "Construction",
	"تعليمي": "Education"
	}

# Backward-compatible alias used in older imports/tests.
CORE_APP_SLUGS = CORE_PLATFORM_APPS
LOCKED_PLATFORM_APPS = ("omnexa_core",)


def get_bench_app_slugs() -> set[str]:
	apps_file = Path(get_bench_path()) / "sites" / "apps.txt"
	if not apps_file.exists():
		return set()
	return {line.strip() for line in apps_file.read_text(encoding="utf-8").splitlines() if line.strip()}


def get_bench_app_order() -> list[str]:
	apps_file = Path(get_bench_path()) / "sites" / "apps.txt"
	if not apps_file.exists():
		return []
	return [line.strip() for line in apps_file.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalize_app_entry(entry) -> str | None:
	if isinstance(entry, dict):
		return entry.get("app") or entry.get("app_slug") or entry.get("name")
	if isinstance(entry, str):
		return entry.strip() or None
	return None


def _dedupe_existing_apps(candidates: list[str] | tuple[str, ...]) -> list[str]:
	installed = get_bench_app_slugs()
	seen: set[str] = set()
	apps: list[str] = []
	for app in candidates:
		if not app or app in seen or app not in installed:
			continue
		seen.add(app)
		apps.append(app)
	return apps


def get_apps_for_activity(activity: str) -> list[str]:
	"""Return ordered install list: core/basic platform + activity vertical only."""
	vertical = ACTIVITY_VERTICAL_APPS.get(activity, ())
	return _dedupe_existing_apps(list(CORE_PLATFORM_APPS) + list(vertical))


def get_visible_app_slugs(activity: str | None) -> list[str]:
	"""Return ordered app slugs visible for a company activity.

	ERP/core apps are visible for every activity. Vertical apps are only visible
	for the matching activity, and the returned order preserves the core order
	first followed by the activity-specific order.
	"""
	activity = (activity or "عام").strip() or "عام"
	vertical = ACTIVITY_VERTICAL_APPS.get(activity, ())
	return _dedupe_existing_apps(list(CORE_PLATFORM_APPS) + list(vertical))


def filter_apps_for_activity(apps: list[dict], activity: str | None) -> list[dict]:
	visible = set(get_visible_app_slugs(activity))
	return [app for app in apps if (app.get("app_slug") or app.get("name")) in visible]


def get_tenant_business_activity(tenant_name: str | None) -> str | None:
	if not tenant_name:
		return None
	request = frappe.db.get_value(
		"Provisioning Request",
		{"tenant": tenant_name},
		["name", "execution_log"],
		order_by="creation desc",
		as_dict=True,
	)
	if not request or not request.get("execution_log"):
		return None
	log = request.execution_log or ""
	try:
		payload = json.loads(log)
		activity = (payload.get("business_activity") or "").strip()
		if activity:
			return activity
	except Exception:
		pass
	for line in log.splitlines():
		if line.startswith("Business Activity:"):
			return line.split(":", 1)[1].strip() or None
	return None


def get_user_business_activity(user: str | None = None) -> str | None:
	user = user or frappe.session.user
	if not user or user == "Guest":
		return None
	tenant = frappe.db.get_value(
		"SaaS Customer Account",
		{"user": user},
		"tenant",
		order_by="creation desc",
	)
	if not tenant:
		tenant = frappe.db.get_value(
			"SaaS Tenant",
			{"company_email": user},
			"name",
			order_by="creation desc",
		)
	return get_tenant_business_activity(tenant)


def normalize_selected_apps(selected_apps, activity: str | None = None) -> list[str]:
	"""Validate user-selected app slugs against installed bench apps."""
	if isinstance(selected_apps, str):
		import json

		try:
			selected_apps = json.loads(selected_apps)
		except Exception:
			selected_apps = [part.strip() for part in selected_apps.split(",")]

	raw = selected_apps or get_apps_for_activity(activity or "عام")
	candidates = [slug for slug in (normalize_app_entry(item) for item in raw) if slug]
	apps = _dedupe_existing_apps(list(LOCKED_PLATFORM_APPS) + candidates)
	if "omnexa_core" not in apps and "omnexa_core" in get_bench_app_slugs():
		apps.insert(0, "omnexa_core")
	return apps


def list_selectable_applications(activity: str | None = None) -> list[dict]:
	"""Return every bench app that can be selected by the public wizard."""
	from erpgenex_saas.services.catalog import CatalogService

	activity = activity or get_user_business_activity()
	apps = []
	for app in get_bench_app_order():
		if app in {"frappe", "erpgenex_saas"}:
			continue
		payload = CatalogService._application_payload(app)
		apps.append(
			{
				"name": payload["application_name"],
				"app": payload["app_slug"],
				"app_slug": payload["app_slug"],
				"display_name": payload["display_name"],
				"description": payload["description"],
				"category": payload["category"],
				"monthly_price": payload["monthly_price"],
				"locked": app in LOCKED_PLATFORM_APPS,
				"recommended": app in CORE_PLATFORM_APPS
	}
		)
	return filter_apps_for_activity(apps, activity)


def get_apps_preview(activity: str) -> list[dict]:
	labels = {
		"frappe": "Frappe Framework",
		"omnexa_core": "ERPGenex Core",
		"omnexa_accounting": "الحسابات",
		"omnexa_fixed_assets": "الأصول الثابتة",
		"omnexa_hr": "الموظفين",
		"omnexa_projects_pm": "إدارة المشاريع",
		"omnexa_ai_employee": "الموظف الذكي",
		"omnexa_customer_core": "العملاء",
		"omnexa_einvoice": "الفوترة الإلكترونية",
		"omnexa_experience": "تجربة المستخدم",
		"omnexa_intelligence_core": "الذكاء التشغيلي",
		"omnexa_n8n_bridge": "أتمتة n8n",
		"omnexa_user_academy": "أكاديمية المستخدم",
		"omnexa_statutory_audit": "التدقيق النظامي",
		"omnexa_theme_manager": "إدارة الثيم",
		"omnexa_construction": "المقاولات",
		"omnexa_education": "التعليم"
	}
	return [{"name": labels.get(app, app), "app": app
	} for app in get_visible_app_slugs(activity)]
