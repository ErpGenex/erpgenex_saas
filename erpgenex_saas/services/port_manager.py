from __future__ import annotations

import socket

import frappe

from erpgenex_saas.services.deployment_settings import get_deployment_config


class PortManager:
	"""Port allocation backed by Allocated Port records and OS availability checks."""

	RESERVED_PORTS = {80, 443}

	def __init__(self):
		config = get_deployment_config()
		self.start_port = config.start_port
		self.end_port = config.end_port

	def get_available_port(self, start: int | None = None) -> int:
		start = max(int(start or self.start_port), self.start_port)
		for port in range(start, self.end_port + 1):
			if self.is_port_available(port):
				return port
		frappe.throw(
			f"No available ports in range {self.start_port}-{self.end_port}. "
			"Increase End Port or release unused ports."
		)

	def is_port_available(self, port: int) -> bool:
		if port in self.RESERVED_PORTS:
			return False
		if port < self.start_port or port > self.end_port:
			return False
		if self._is_port_allocated(port):
			return False
		if self._is_port_in_use_os(port):
			return False
		return True

	def _is_port_allocated(self, port: int) -> bool:
		status = frappe.db.get_value("Allocated Port", {"port_number": port}, "status")
		return status in ("Reserved", "Running")

	def _is_port_in_use_os(self, port: int) -> bool:
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.settimeout(0.5)
			return sock.connect_ex(("127.0.0.1", port)) == 0

	def reserve_port(self, port: int, tenant_name: str, site_folder: str) -> frappe._dict:
		if not self.is_port_available(port):
			frappe.throw(f"Port {port} is not available")

		name = f"PORT-{port}"
		if frappe.db.exists("Allocated Port", name):
			doc = frappe.get_doc("Allocated Port", name)
			doc.update(
				{
					"site": site_folder,
					"tenant": tenant_name,
					"status": "Reserved",
					"reserved_at": frappe.utils.now_datetime(),
					"released_at": None,
				}
			)
			doc.save(ignore_permissions=True)
		else:
			doc = frappe.get_doc(
				{
					"doctype": "Allocated Port",
					"port_number": port,
					"site": site_folder,
					"tenant": tenant_name,
					"status": "Reserved",
					"reserved_at": frappe.utils.now_datetime(),
				}
			)
			doc.insert(ignore_permissions=True)

		frappe.db.set_value("SaaS Tenant", tenant_name, "port_number", port, update_modified=False)
		return doc

	def mark_running(self, port: int, pid: int | None = None):
		doc_name = frappe.db.get_value("Allocated Port", {"port_number": port}, "name")
		if not doc_name:
			return
		doc = frappe.get_doc("Allocated Port", doc_name)
		doc.status = "Running"
		if pid:
			doc.service_pid = pid
		doc.last_health_check = frappe.utils.now_datetime()
		doc.save(ignore_permissions=True)

	def mark_failed(self, port: int, message: str = ""):
		doc_name = frappe.db.get_value("Allocated Port", {"port_number": port}, "name")
		if not doc_name:
			return
		doc = frappe.get_doc("Allocated Port", doc_name)
		doc.status = "Failed"
		if message:
			doc.notes = message
		doc.save(ignore_permissions=True)

	def release_port(self, port: int):
		doc_name = frappe.db.get_value("Allocated Port", {"port_number": port}, "name")
		if not doc_name:
			return
		doc = frappe.get_doc("Allocated Port", doc_name)
		doc.status = "Free"
		doc.site = None
		doc.tenant = None
		doc.service_pid = None
		doc.released_at = frappe.utils.now_datetime()
		doc.save(ignore_permissions=True)

	def release_tenant_port(self, tenant_name: str):
		port = frappe.db.get_value("SaaS Tenant", tenant_name, "port_number")
		if port:
			self.release_port(int(port))
			frappe.db.set_value("SaaS Tenant", tenant_name, "port_number", None, update_modified=False)

	def ensure_reserved_port_80(self):
		if frappe.db.exists("Allocated Port", "PORT-80"):
			return
		frappe.get_doc(
			{
				"doctype": "Allocated Port",
				"port_number": 80,
				"site": "main",
				"status": "Running",
				"notes": "Reserved for main SaaS control plane site",
				"reserved_at": frappe.utils.now_datetime(),
			}
		).insert(ignore_permissions=True)
