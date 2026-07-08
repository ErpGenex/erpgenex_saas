import frappe

from erpgenex_saas.portal_context import apply_portal_context


def get_context(context):
	apply_portal_context(context)
	context.no_cache = 1
	context.title = frappe._("ERPGenex SaaS — Enterprise Cloud Platform")
	context.hero_title = frappe._("Launch your ERP workspace in minutes")
	context.hero_subtitle = frappe._(
		"Premium multi-tenant SaaS platform with subscription billing, "
		"modular app marketplace, automated provisioning, and enterprise-grade security."
	)
	context.stats = [
		{"value": 1200, "suffix": "+", "label": frappe._("Active Tenants")},
		{"value": 52, "suffix": "", "label": frappe._("ERP Applications")},
		{"value": 99, "suffix": ".9%", "label": frappe._("Uptime SLA")},
	]
