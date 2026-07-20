from __future__ import annotations

import os
import signal
import shutil
import subprocess
import time
from pathlib import Path

import frappe
from frappe.utils import get_bench_path


class ServiceManager:
	"""Manage per-tenant bench serve processes without shell=True."""

	SERVICE_DIR_NAME = "tenant_services"

	def __init__(self):
		self.bench_path = get_bench_path()
		self.service_dir = Path(self.bench_path) / "config" / self.SERVICE_DIR_NAME
		self.service_dir.mkdir(parents=True, exist_ok=True)
		self.logger = frappe.logger("erpgenex_saas")

	def bench_command(self) -> str:
		return shutil.which("bench") or os.path.join(self.bench_path, "env", "bin", "bench")

	def pid_file(self, site_folder: str) -> Path:
		return self.service_dir / f"{site_folder}.pid"

	def log_file(self, site_folder: str) -> Path:
		return self.service_dir / f"{site_folder}.log"

	def supervisor_conf_path(self, site_folder: str) -> Path:
		return self.service_dir / f"supervisor-{site_folder}.conf"

	def create_service(self, site_folder: str, port: int) -> dict:
		"""Create and start an isolated bench serve process for the site."""
		if self.is_running(site_folder):
			pid = self.read_pid(site_folder)
			return {"status": "running", "pid": pid, "method": "existing"
	}

		if self._port_open(port):
			return {"status": "running", "pid": None, "method": "existing-port"
	}

		if self._try_supervisor(site_folder, port):
			pid = self.read_pid(site_folder)
			return {"status": "running", "pid": pid, "method": "supervisor"
	}

		return self._start_bench_serve(site_folder, port)

	def _try_supervisor(self, site_folder: str, port: int) -> bool:
		conf = self.supervisor_conf_path(site_folder)
		log_path = self.log_file(site_folder)
		pid_path = self.pid_file(site_folder)
		conf.write_text(
			f"""[program:frappe-{site_folder}]
command={self.bench_command()} --site {site_folder} serve --port {port}
directory={self.bench_path}
autostart=true
autorestart=true
stdout_logfile={log_path}
stderr_logfile={log_path}
pidfile={pid_path}
""",
			encoding="utf-8",
		)

		steps = [
			["supervisorctl", "reread"],
			["supervisorctl", "update"],
			["supervisorctl", "start", f"frappe-{site_folder}"],
		]
		for cmd in steps:
			try:
				result = subprocess.run(
					cmd,
					cwd=self.bench_path,
					capture_output=True,
					text=True,
					timeout=30,
					check=False,
				)
				if result.returncode != 0:
					self.logger.warning("Supervisor step failed for %s: %s", site_folder, result.stderr)
					return False
			except (FileNotFoundError, subprocess.SubprocessError):
				return False

		time.sleep(2)
		return self.is_running(site_folder)

	def _start_bench_serve(self, site_folder: str, port: int) -> dict:
		log_path = self.log_file(site_folder)
		pid_path = self.pid_file(site_folder)
		log_handle = open(log_path, "a", encoding="utf-8")

		process = subprocess.Popen(
			[
				self.bench_command(),
				"--site",
				site_folder,
				"serve",
				"--port",
				str(port),
			],
			cwd=self.bench_path,
			stdout=log_handle,
			stderr=log_handle,
			start_new_session=True,
		)
		pid_path.write_text(str(process.pid), encoding="utf-8")

		for _ in range(30):
			time.sleep(1)
			if process.poll() is not None:
				raise RuntimeError(f"Service failed to start for {site_folder} on port {port}")
			if self._port_open(port):
				break
		else:
			raise RuntimeError(f"Port {port} did not open for {site_folder}")

		return {"status": "running", "pid": process.pid, "method": "bench-serve"
	}

	def _port_open(self, port: int) -> bool:
		import socket

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.settimeout(0.5)
			return sock.connect_ex(("127.0.0.1", port)) == 0

	def stop_service(self, site_folder: str) -> bool:
		stopped = False
		if self.supervisor_conf_path(site_folder).exists():
			try:
				subprocess.run(
					["supervisorctl", "stop", f"frappe-{site_folder}"],
					cwd=self.bench_path,
					capture_output=True,
					text=True,
					timeout=20,
					check=False,
				)
				stopped = True
			except (FileNotFoundError, subprocess.SubprocessError):
				pass

		pid = self.read_pid(site_folder)
		if pid and self._pid_alive(pid):
			try:
				os.kill(pid, signal.SIGTERM)
				stopped = True
			except ProcessLookupError:
				pass

		if self.pid_file(site_folder).exists():
			self.pid_file(site_folder).unlink(missing_ok=True)
		return stopped

	def restart_service(self, site_folder: str, port: int) -> dict:
		self.stop_service(site_folder)
		time.sleep(1)
		return self.create_service(site_folder, port)

	def is_running(self, site_folder: str) -> bool:
		pid = self.read_pid(site_folder)
		return bool(pid and self._pid_alive(pid))

	def read_pid(self, site_folder: str) -> int | None:
		pid_path = self.pid_file(site_folder)
		if not pid_path.exists():
			return None
		try:
			return int(pid_path.read_text(encoding="utf-8").strip())
		except ValueError:
			return None

	def read_logs(self, site_folder: str, tail: int = 200) -> str:
		log_path = self.log_file(site_folder)
		if not log_path.exists():
			return ""
		lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
		return "\n".join(lines[-tail:])

	def _pid_alive(self, pid: int) -> bool:
		try:
			os.kill(pid, 0)
			return True
		except ProcessLookupError:
			return False
