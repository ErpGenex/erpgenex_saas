from frappe import _

from erpgenex_saas.portal_context import apply_portal_context


def erpgenex_saas_nav_items():
	return [
		{"label": _("Home"), "route": "/saas"},
		{"label": _("Pricing"), "route": "/saas/pricing"},
		{"label": _("Applications"), "route": "/saas/applications"},
		{"label": _("Checkout"), "route": "/saas/checkout"},
		{"label": _("Dashboard"), "route": "/saas/dashboard"},
	]


def update_website_context(context):
	apply_portal_context(context)
