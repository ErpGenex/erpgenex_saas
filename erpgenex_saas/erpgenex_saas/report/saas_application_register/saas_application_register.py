# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `application_name`, `display_name`
		FROM `tabSaaS Application`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Application Name"), "fieldname": "application_name", "fieldtype": "Data", "width": 120},
		{"label": _("Display Name"), "fieldname": "display_name", "fieldtype": "Data", "width": 120}
	]
	return columns, data
