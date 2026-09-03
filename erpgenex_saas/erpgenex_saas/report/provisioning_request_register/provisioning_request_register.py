# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `tenant`, `request_type`, `status`
		FROM `tabProvisioning Request`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Tenant"), "fieldname": "tenant", "fieldtype": "Link", "width": 120},
		{"label": _("Request Type"), "fieldname": "request_type", "fieldtype": "Select", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Select", "width": 120}
	]
	return columns, data
