from __future__ import annotations

import frappe


class DomainService:
	@staticmethod
	def create_domain(tenant: str, domain_name: str, domain_type: str = "Subdomain"):
		existing = frappe.db.get_value(
			"SaaS Domain", {"domain_name": domain_name
	}, ["name", "tenant"], as_dict=True
		)
		if existing:
			if existing.tenant == tenant:
				return frappe.get_doc("SaaS Domain", existing.name)
			frappe.throw(f"Domain already exists: {domain_name}")
		doc = frappe.get_doc(
			{
				"doctype": "SaaS Domain",
				"tenant": tenant,
				"domain_name": domain_name,
				"domain_type": domain_type,
				"status": "Pending Verification",
				"ssl_status": "Pending"
	}
		)
		doc.insert(ignore_permissions=True)
		return doc

	@staticmethod
	def verify_domain(domain_name: str):
		name = frappe.db.get_value("SaaS Domain", {"domain_name": domain_name
	}, "name")
		if not name:
			frappe.throw(f"Domain not found: {domain_name}")
		doc = frappe.get_doc("SaaS Domain", name)
		doc.status = "Verified"
		doc.dns_verified = 1
		doc.save(ignore_permissions=True)
		return doc
