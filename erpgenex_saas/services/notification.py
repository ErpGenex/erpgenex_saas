from __future__ import annotations

import frappe


class NotificationService:
	EVENTS = (
		"registration",
		"payment",
		"renewal",
		"expiration",
		"upgrade",
		"downgrade",
		"backup",
		"error",
	)

	@staticmethod
	def notify(tenant: str, event_type: str, subject: str, message: str, channel: str = "Email"):
		if event_type not in NotificationService.EVENTS:
			frappe.throw(f"Unsupported event type: {event_type}")
		doc = frappe.get_doc(
			{
				"doctype": "SaaS Notification Log",
				"tenant": tenant,
				"event_type": event_type,
				"channel": channel,
				"subject": subject,
				"message": message,
				"status": "Queued"
	}
		)
		doc.insert(ignore_permissions=True)
		tenant_email = frappe.db.get_value("SaaS Tenant", tenant, "company_email")
		if channel == "Email" and tenant_email:
			try:
				frappe.sendmail(recipients=[tenant_email], subject=subject, message=message)
				doc.status = "Sent"
				doc.save(ignore_permissions=True)
			except Exception:
				doc.status = "Failed"
				doc.save(ignore_permissions=True)
		return doc
