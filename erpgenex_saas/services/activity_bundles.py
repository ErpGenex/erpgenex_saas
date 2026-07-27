from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe.utils import get_bench_path

from erpgenex_saas.constants import PAID_LICENSED_APPS

# Core + basic platform stack (installed with omnexa_core bootstrap).
CORE_PLATFORM_APPS = (
	"frappe",
	"omnexa_core",
	"omnexa_accounting",
	"omnexa_theme_manager",
	"omnexa_services",
	"omnexa_projects_pm",
	"omnexa_hr",
	"omnexa_fixed_assets",
	"omnexa_einvoice",
	"omnexa_edms",
	"omnexa_customer_core",
	"omnexa_ai_employee",
	"public-scripts",
	"omnexa_reporting_compliance",
	"omnexa_user_academy",
	"omnexa_statutory_audit",
	"omnexa_setup_intelligence",
	"omnexa_n8n_bridge",
	"omnexa_intelligence_core",
	"omnexa_experience",
	"omnexa_eng_workflow_engine",
	"omnexa_eng_platform_integrations",
	"omnexa_eng_document_control",
	"omnexa_backup",
	"erpgenex_demo_studio",
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


def _exclude_paid_apps(apps: list[str]) -> list[str]:
	"""Exclude paid apps from automatic site provisioning bundles."""
	return [app for app in apps if app not in PAID_LICENSED_APPS]


def get_apps_for_activity(activity: str) -> list[str]:
	"""Return ordered install list: core/basic platform + activity vertical only."""
	vertical = ACTIVITY_VERTICAL_APPS.get(activity, ())
	return _exclude_paid_apps(_dedupe_existing_apps(list(CORE_PLATFORM_APPS) + list(vertical)))


def _walk_required_app_dependency_slugs(seed_apps: list[str]) -> list[str]:
	"""Return unique app slugs reachable via ``required_apps`` hooks."""
	order: list[str] = []
	seen: set[str] = set()
	queue = [app.strip() for app in seed_apps if app and str(app).strip()]

	while queue:
		app = queue.pop(0)
		if app in seen:
			continue
		seen.add(app)
		order.append(app)
		if app in {"frappe", "erpnext", "payments"}:
			continue
		try:
			hooks = frappe.get_hooks(app_name=app)
		except Exception:
			continue
		for raw in hooks.get("required_apps") or ():
			if not isinstance(raw, str):
				continue
			dep = raw.strip()
			if dep and dep not in seen:
				queue.append(dep)

	return order


def _is_core_free_app(app_slug: str) -> bool:
	if not app_slug or app_slug in PAID_LICENSED_APPS:
		return False
	if app_slug not in get_bench_app_slugs():
		return False
	try:
		from erpgenex_saas.services.catalog import CatalogService

		payload = CatalogService._application_payload(app_slug)
	except Exception:
		return False
	return payload.get("distribution_type") == "Core Free"


def _is_auto_install_safe(app_slug: str) -> bool:
	if not _is_core_free_app(app_slug):
		return False
	for dep in _walk_required_app_dependency_slugs([app_slug]):
		if not _is_core_free_app(dep):
			return False
	return True


def get_free_auto_install_apps(activity: str) -> list[str]:
	"""Return the dependency-safe free bundle used during site creation."""
	return [app for app in get_apps_for_activity(activity) if _is_auto_install_safe(app)]


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

	raw = selected_apps or get_free_auto_install_apps(activity or "عام")
	candidates = [slug for slug in (normalize_app_entry(item) for item in raw) if slug]
	apps = _exclude_paid_apps(_dedupe_existing_apps(list(LOCKED_PLATFORM_APPS) + candidates))
	if "omnexa_core" not in apps and "omnexa_core" in get_bench_app_slugs():
		apps.insert(0, "omnexa_core")
	return [app for app in apps if _is_auto_install_safe(app)]


def list_selectable_applications(activity: str | None = None) -> list[dict]:
	"""Return every bench app that can be selected by the public wizard."""
	from erpgenex_saas.services.catalog import CatalogService

	activity = activity or get_user_business_activity()
	apps = []
	for app in get_bench_app_order():
		if app in {"frappe", "erpgenex_saas"} or app in PAID_LICENSED_APPS:
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
		"omnexa_theme_manager": "إدارة الثيم",
		"omnexa_services": "الخدمات",
		"omnexa_projects_pm": "إدارة المشاريع",
		"omnexa_hr": "الموظفين",
		"omnexa_fixed_assets": "الأصول الثابتة",
		"omnexa_einvoice": "الفوترة الإلكترونية",
		"omnexa_edms": "إدارة المستندات",
		"omnexa_customer_core": "العملاء",
		"omnexa_ai_employee": "الموظف الذكي",
		"public-scripts": "Public Scripts",
		"omnexa_reporting_compliance": "الالتزام والتقارير",
		"omnexa_user_academy": "أكاديمية المستخدم",
		"omnexa_statutory_audit": "التدقيق النظامي",
		"omnexa_setup_intelligence": "إعداد الذكاء",
		"omnexa_n8n_bridge": "أتمتة n8n",
		"omnexa_intelligence_core": "الذكاء التشغيلي",
		"omnexa_experience": "تجربة المستخدم",
		"omnexa_eng_workflow_engine": "محرك سير العمل",
		"omnexa_eng_platform_integrations": "تكاملات المنصة",
		"omnexa_eng_document_control": "التحكم في المستندات",
		"omnexa_backup": "النسخ الاحتياطي",
		"erpgenex_demo_studio": "ERPGenex Demo Studio",
		"omnexa_construction": "المقاولات",
		"omnexa_education": "التعليم"
	}
	return [{"name": labels.get(app, app), "app": app
	} for app in get_visible_app_slugs(activity)]
