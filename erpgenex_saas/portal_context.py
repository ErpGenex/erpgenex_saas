from __future__ import annotations

import urllib.parse

import frappe
from frappe import _

PORTAL_LANGUAGES = ("en", "ar")


def apply_portal_language() -> None:
	"""Apply EN/AR language for /saas website routes with site isolation."""
	try:
		# Ensure we're on a valid site before applying language
		site_name = getattr(frappe.local, "site", "")
		if not site_name:
			return
		request = getattr(frappe.local, "request", None)
		if not request:
			return
		path = getattr(request, "path", "") or ""
		if not str(path).startswith("/saas"):
			return

		lang = (frappe.form_dict.get("lang") or "").strip().lower()
		if lang not in PORTAL_LANGUAGES:
			lang = (frappe.request.cookies.get("preferred_language") or "en").strip().lower()
		if lang not in PORTAL_LANGUAGES:
			lang = "en"

		# Set language in site-specific context
		frappe.local.lang = lang
		if lang != (frappe.request.cookies.get("preferred_language") or ""):
			frappe.local.cookie_manager.set_cookie("preferred_language", lang)

	except Exception as e:
		# Log error but don't break the request to maintain site isolation
		frappe.logger("erpgenex_saas").warning(f"Portal language application failed for site {getattr(frappe.local, 'site', 'unknown')}: {str(e)}")


def lang_switch_url(lang_code: str) -> str:
	try:
		request = getattr(frappe.local, "request", None)
		if not request:
			return "/saas"

		path = getattr(request, "path", None) or "/saas"
		qs = dict(frappe.form_dict or {})
		qs["lang"] = lang_code
		query = urllib.parse.urlencode({k: v for k, v in qs.items() if v is not None and k != "cmd"})
		return f"{path}?{query}" if query else path
	except Exception:
		return "/saas"


def apply_portal_context(context) -> None:
	try:
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
			"continue_checkout": _("Continue to Checkout →")
	}
	except Exception as e:
		# Log error but don't break the request to maintain site isolation
		frappe.logger("erpgenex_saas").warning(f"Portal context application failed for site {getattr(frappe.local, 'site', 'unknown')}: {str(e)}")
