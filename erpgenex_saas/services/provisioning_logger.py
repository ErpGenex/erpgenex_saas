from __future__ import annotations

import time
from contextlib import contextmanager

import frappe


class ProvisioningLogger:
	"""Structured stage logging for provisioning and deployment."""

	def __init__(self, tenant: str, request_name: str | None = None):
		self.tenant = tenant
		self.request_name = request_name
		self.logger = frappe.logger("erpgenex_saas")

	@contextmanager
	def stage(self, stage_name: str):
		start = time.time()
		log_doc = frappe.get_doc(
			{
				"doctype": "Provisioning Stage Log",
				"tenant": self.tenant,
				"provisioning_request": self.request_name,
				"stage": stage_name,
				"status": "Running",
				"start_time": frappe.utils.now_datetime()
	}
		)
		log_doc.insert(ignore_permissions=True)
		frappe.db.commit()

		try:
			self.logger.info("Stage %s started for tenant %s", stage_name, self.tenant)
			yield log_doc
			log_doc.status = "Success"
		except Exception as exc:
			log_doc.status = "Failed"
			log_doc.traceback = frappe.get_traceback(with_context=True)
			log_doc.stderr = str(exc)
			raise
		finally:
			end = time.time()
			log_doc.end_time = frappe.utils.now_datetime()
			log_doc.duration_seconds = round(end - start, 3)
			log_doc.save(ignore_permissions=True)
			frappe.db.commit()

	def record_command(
		self,
		log_doc,
		command: list[str],
		result,
		*,
		redact_args: list[int] | None = None,
	):
		safe_cmd = list(command)
		for idx in redact_args or []:
			if 0 <= idx < len(safe_cmd):
				safe_cmd[idx] = "********"
		log_doc.stdout = (result.stdout or "")[:65000]
		log_doc.stderr = (result.stderr or "")[:65000]
		log_doc.exit_code = result.returncode
		log_doc.save(ignore_permissions=True)
