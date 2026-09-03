# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `tenant`, `subscription`, `invoice_date`, `status`, `paid_amount`
		FROM `tabSaaS Invoice`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Tenant"), "fieldname": "tenant", "fieldtype": "Link", "width": 120},
		{"label": _("Subscription"), "fieldname": "subscription", "fieldtype": "Link", "width": 120},
		{"label": _("Invoice Date"), "fieldname": "invoice_date", "fieldtype": "Date", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Select", "width": 120},
		{"label": _("Paid Amount"), "fieldname": "paid_amount", "fieldtype": "Currency", "width": 120}
	]
	return columns, data
