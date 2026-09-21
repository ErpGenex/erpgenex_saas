# Copyright (c) 2026, ErpGenEx
"""Deactivate approval workflows that hijacked operational Select `status` fields.

Global Excellence mistakenly bound Draft/Pending Approval workflows to business
status enums (Arabic wizard states, Queued/Running, etc.), blocking insert/save.
"""

from __future__ import annotations

import frappe


SAAS_DOCTYPES = (
	"Activity Selection Wizard",
	"Provisioning Request",
	"Provisioning Stage Log",
	"SaaS Tenant",
	"SaaS Customer Account",
	"SaaS Invoice",
	"SaaS Payment",
	"SaaS License",
	"SaaS Domain",
	"SaaS Notification Log",
	"SaaS Source Download Link",
	"Allocated Port",
	"Client Registration Request",
	"Payment Intent",
)


def _status_options(doctype: str) -> set[str]:
	meta = frappe.get_meta(doctype)
	field = meta.get_field("status")
	if not field:
		return set()
	return {o.strip() for o in (field.options or "").split("\n") if o.strip()}


def execute():
	deactivated = []
	for doctype in SAAS_DOCTYPES:
		if not frappe.db.exists("DocType", doctype):
			continue
		options = _status_options(doctype)
		# Keep only if status already speaks the approval vocabulary.
		if "Draft" in options and ("Pending Approval" in options or "Approved" in options):
			continue
		for name in frappe.get_all(
			"Workflow",
			filters={"document_type": doctype, "is_active": 1},
			pluck="name",
		):
			field = frappe.db.get_value("Workflow", name, "workflow_state_field")
			if field == "status":
				frappe.db.set_value("Workflow", name, "is_active", 0)
				deactivated.append(name)

	# Broader sweep: any active workflow on status whose DocType status lacks Draft.
	for row in frappe.get_all(
		"Workflow",
		filters={"is_active": 1, "workflow_state_field": "status"},
		fields=["name", "document_type"],
	):
		if not frappe.db.exists("DocType", row.document_type):
			continue
		options = _status_options(row.document_type)
		if "Draft" in options and ("Pending Approval" in options or "Approved" in options):
			continue
		if "Draft" in options and len(options) <= 6:
			# Heuristic: pure Draft/… approval selects are fine; mixed business enums are not.
			# If options include operational values, deactivate.
			operational = options - {
				"Draft",
				"Pending Approval",
				"Approved",
				"Rejected",
				"Cancelled",
				"Canceled",
			}
			if not operational:
				continue
		frappe.db.set_value("Workflow", row.name, "is_active", 0)
		deactivated.append(row.name)

	frappe.clear_cache(doctype="Workflow")
	frappe.db.commit()
