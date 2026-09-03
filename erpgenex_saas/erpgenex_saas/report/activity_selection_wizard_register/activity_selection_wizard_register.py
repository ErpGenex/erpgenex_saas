# i18n:managed-catalog — bilingual/regional catalog; UI via ar.csv
# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `status`
		FROM `tabActivity Selection Wizard`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("الحالة"), "fieldname": "status", "fieldtype": "Select", "width": 120}
	]
	return columns, data
