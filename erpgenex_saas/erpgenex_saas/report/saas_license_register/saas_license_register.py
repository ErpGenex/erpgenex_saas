# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `license_type`, `status`, `tenant`, `application`
		FROM `tabSaaS License`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("License Type"), "fieldname": "license_type", "fieldtype": "Select", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Select", "width": 120},
		{"label": _("Tenant"), "fieldname": "tenant", "fieldtype": "Link", "width": 120},
		{"label": _("Application"), "fieldname": "application", "fieldtype": "Link", "width": 120}
	]
	return columns, data
