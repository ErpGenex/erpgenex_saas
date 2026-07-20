from __future__ import annotations

import frappe
import time
import json


class ProgressTracker:
	"""Tracks progress of provisioning operations without doc.save conflicts."""

	def __init__(self):
		self.logger = frappe.logger("erpgenex_saas")

	def _has_progress_field(self) -> bool:
		return frappe.get_meta("SaaS Tenant").has_field("provisioning_progress")

	def _read_progress(self, tenant_name: str) -> dict:
		current = frappe.db.get_value("SaaS Tenant", tenant_name, "provisioning_progress")
		if not current:
			return {}
		try:
			return json.loads(current)
		except json.JSONDecodeError:
			return {}

	def _write_progress(self, tenant_name: str, progress_data: dict):
		if not self._has_progress_field() or not frappe.db.exists("SaaS Tenant", tenant_name):
			return
		frappe.db.set_value(
			"SaaS Tenant",
			tenant_name,
			"provisioning_progress",
			json.dumps(progress_data),
			update_modified=False,
		)

	def start(self, request_name: str):
		try:
			progress_data = {
				"request_name": request_name,
				"status": "started",
				"progress": 0,
				"start_time": time.time(),
				"step": "initializing"
	}
			self._write_progress(request_name, progress_data)
			self.logger.info("Progress tracking started for %s", request_name)
		except Exception as e:
			self.logger.error("Failed to start progress tracking: %s", str(e))

	def update(self, request_name: str, step: str, progress: int):
		try:
			progress_data = self._read_progress(request_name)
			progress_data.update(
				{
					"step": step,
					"progress": progress,
					"last_updated": time.time()
	}
			)
			self._write_progress(request_name, progress_data)
			self.logger.info("Progress updated for %s: %s - %s%%", request_name, step, progress)
		except Exception as e:
			self.logger.error("Failed to update progress: %s", str(e))

	def complete(self, request_name: str):
		try:
			progress_data = self._read_progress(request_name)
			progress_data.update(
				{
					"status": "completed",
					"progress": 100,
					"end_time": time.time(),
					"step": "completed"
	}
			)
			self._write_progress(request_name, progress_data)
			self.logger.info("Progress completed for %s", request_name)
		except Exception as e:
			self.logger.error("Failed to complete progress: %s", str(e))

	def fail(self, request_name: str, error: str):
		try:
			progress_data = self._read_progress(request_name)
			progress_data.update(
				{
					"status": "failed",
					"error": error,
					"end_time": time.time(),
					"step": "failed"
	}
			)
			self._write_progress(request_name, progress_data)
			self.logger.error("Progress failed for %s: %s", request_name, error)
		except Exception as e:
			self.logger.error("Failed to mark progress as failed: %s", str(e))

	def get_progress(self, request_name: str) -> dict:
		try:
			progress_data = self._read_progress(request_name)
			if progress_data:
				return progress_data
			return {"status": "not_started", "progress": 0
	}
		except Exception as e:
			self.logger.error("Failed to get progress: %s", str(e))
			return {"status": "error", "error": str(e)
	}

	def get_all_progress(self) -> list:
		try:
			tenants = frappe.db.get_all(
				"SaaS Tenant",
				{"status": ["in", ["Provisioning", "Active"]]},
			)
			progress_list = []
			for tenant in tenants:
				progress = self.get_progress(tenant["name"])
				progress["tenant_name"] = tenant["name"]
				progress_list.append(progress)
			return progress_list
		except Exception as e:
			self.logger.error("Failed to get all progress: %s", str(e))
			return []
