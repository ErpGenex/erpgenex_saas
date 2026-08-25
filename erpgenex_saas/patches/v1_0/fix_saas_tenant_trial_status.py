"""Normalize legacy SaaS Tenant status Trial → Draft."""

from __future__ import annotations

import frappe


def execute():
	if not frappe.db.exists("DocType", "SaaS Tenant"):
		return
	frappe.db.sql(
		"""
		UPDATE `tabSaaS Tenant`
		SET status = 'Draft'
		WHERE status = 'Trial'
		"""
	)
	frappe.db.commit()
