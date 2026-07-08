from erpgenex_saas.bootstrap import bootstrap_platform
from erpgenex_saas.services import CatalogService


def before_install():
	import frappe

	frappe.logger("erpgenex_saas").info("Running erpgenex_saas before_install")


def after_install():
	import frappe

	frappe.logger("erpgenex_saas").info("Running erpgenex_saas after_install")
	CatalogService.sync_installed_apps_to_catalog()
	bootstrap_platform()


def after_migrate():
	from erpgenex_saas.sync_doctypes import sync_all_doctypes

	sync_all_doctypes()
	bootstrap_platform()
