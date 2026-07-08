import frappe


def validate():
	"""Placeholder auth hook for future API token and tenant-bound auth."""
	frappe.local.flags.erpgenex_saas_auth_checked = True
