from __future__ import annotations

import urllib.parse

import frappe
from frappe import _

PORTAL_LANGUAGES = ("en", "ar")


def apply_portal_language() -> None:
	"""Apply EN/AR language for /saas website routes."""
	request = getattr(frappe.local, "request", None)
	path = getattr(request, "path", "") or ""
	if not str(path).startswith("/saas"):
		return

	lang = (frappe.form_dict.get("lang") or "").strip().lower()
	if lang not in PORTAL_LANGUAGES:
		lang = (frappe.request.cookies.get("preferred_language") or "en").strip().lower()
	if lang not in PORTAL_LANGUAGES:
		lang = "en"

	frappe.local.lang = lang
	if lang != (frappe.request.cookies.get("preferred_language") or ""):
		frappe.local.cookie_manager.set_cookie("preferred_language", lang)


def lang_switch_url(lang_code: str) -> str:
	request = getattr(frappe.local, "request", None)
	path = getattr(request, "path", None) or "/saas"
	qs = dict(frappe.form_dict or {})
	qs["lang"] = lang_code
	query = urllib.parse.urlencode({k: v for k, v in qs.items() if v is not None and k != "cmd"})
	return f"{path}?{query}" if query else path


def apply_portal_context(context) -> None:
	apply_portal_language()
	context.lang = frappe.local.lang
	context.is_rtl = frappe.local.lang == "ar"
	context.lang_en_url = lang_switch_url("en")
	context.lang_ar_url = lang_switch_url("ar")
	context.portal_strings = {
		"month": _("/ month"),
		"year": _("/ year"),
		"mo": _(" / mo"),
		"processing": _("Processing…"),
		"install": _("Install"),
		"selected_total": _("Selected Apps Total"),
		"continue_checkout": _("Continue to Checkout →"),
	}
