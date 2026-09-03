# Copyright (c) 2026, ErpGenEx
# Auto-generated Global Excellence report pack

import frappe
from frappe import _


def execute(filters=None):
	data = frappe.db.sql(
		"""
		SELECT `name`, `tenant`, `provisioning_request`, `stage`, `status`
		FROM `tabProvisioning Stage Log`
		ORDER BY modified DESC
		LIMIT 500
		""",
		as_dict=True,
	)
	columns = [
		{"label": _("Name"), "fieldname": "name", "fieldtype": "Link", "width": 140},
		{"label": _("Tenant"), "fieldname": "tenant", "fieldtype": "Link", "width": 120},
		{"label": _("Provisioning Request"), "fieldname": "provisioning_request", "fieldtype": "Link", "width": 120},
		{"label": _("Stage"), "fieldname": "stage", "fieldtype": "Select", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Select", "width": 120}
	]
	return columns, data
