# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `event_name`, `reference`
		FROM `tabSaaS Audit Log`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Event Name"), "fieldname": "event_name", "fieldtype": "Data", "width": 120},
		{"label": _("Reference"), "fieldname": "reference", "fieldtype": "Data", "width": 120}
	]
	return columns, data
