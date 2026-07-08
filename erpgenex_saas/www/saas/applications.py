import frappe

from erpgenex_saas.portal_context import apply_portal_context
from erpgenex_saas.services.catalog import CatalogService


def get_context(context):
	apply_portal_context(context)
	context.no_cache = 1
	context.title = frappe._("Applications — ERPGenex SaaS")
	try:
		context.applications = CatalogService.list_active_applications()
	except Exception:
		context.applications = []
