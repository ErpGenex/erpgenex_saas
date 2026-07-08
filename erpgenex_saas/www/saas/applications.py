import frappe

from erpgenex_saas.services import CatalogService


def get_context(context):
	context.no_cache = 1
	context.title = "Applications Marketplace - ERPGenex SaaS"
	try:
		context.applications = CatalogService.list_active_applications()
	except Exception:
		context.applications = []
