from __future__ import annotations

import json

import frappe


class AuditService:
	@staticmethod
	def log(event_name: str, reference: str, payload: dict | None = None):
		frappe.get_doc(
			{
				"doctype": "SaaS Audit Log",
				"event_name": event_name,
				"reference": reference,
				"user": frappe.session.user if frappe.session else "Administrator",
				"payload": json.dumps(payload or {}, default=str),
			}
		).insert(ignore_permissions=True)
