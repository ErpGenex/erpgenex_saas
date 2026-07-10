from __future__ import annotations

import frappe
import time
import psutil
import subprocess


class MonitoringService:
	"""Monitoring service for system health and metrics"""
	
	def __init__(self):
		self.logger = frappe.logger("erpgenex_saas")
	
	def collect_metrics(self) -> dict:
		"""Collect system metrics"""
		try:
			metrics = {
				"cpu": self.get_cpu_usage(),
				"memory": self.get_memory_usage(),
				"disk": self.get_disk_usage(),
				"timestamp": time.time()
			}
			return metrics
		except Exception as e:
			self.logger.error(f"Failed to collect metrics: {str(e)}")
			return {}
	
	def get_cpu_usage(self) -> float:
		"""Get CPU usage percentage"""
		try:
			return psutil.cpu_percent(interval=1)
		except Exception as e:
			self.logger.error(f"Failed to get CPU usage: {str(e)}")
			return 0.0
	
	def get_memory_usage(self) -> dict:
		"""Get memory usage"""
		try:
			mem = psutil.virtual_memory()
			return {
				"total": mem.total,
				"available": mem.available,
				"used": mem.used,
				"percent": mem.percent
			}
		except Exception as e:
			self.logger.error(f"Failed to get memory usage: {str(e)}")
			return {}
	
	def get_disk_usage(self) -> dict:
		"""Get disk usage"""
		try:
			disk = psutil.disk_usage('/')
			return {
				"total": disk.total,
				"used": disk.used,
				"free": disk.free,
				"percent": disk.percent
			}
		except Exception as e:
			self.logger.error(f"Failed to get disk usage: {str(e)}")
			return {}
	
	def check_health(self) -> dict:
		"""Check system health"""
		try:
			health = {
				"database": self.check_database(),
				"redis": self.check_redis(),
				"nginx": self.check_nginx(),
				"frappe": self.check_frappe(),
				"timestamp": time.time()
			}
			return health
		except Exception as e:
			self.logger.error(f"Failed to check health: {str(e)}")
			return {}
	
	def check_database(self) -> dict:
		"""Check database health"""
		try:
			# Try to execute a simple query
			frappe.db.sql("SELECT 1")
			return {
				"status": "healthy",
				"message": "Database is responding"
			}
		except Exception as e:
			return {
				"status": "unhealthy",
				"message": str(e)
			}
	
	def check_redis(self) -> dict:
		"""Check Redis health"""
		try:
			import redis
			redis_client = redis.Redis(host='127.0.0.1', port=6379, db=0)
			redis_client.ping()
			return {
				"status": "healthy",
				"message": "Redis is responding"
			}
		except Exception as e:
			return {
				"status": "unhealthy",
				"message": str(e)
			}
	
	def check_nginx(self) -> dict:
		"""Check Nginx health"""
		try:
			result = subprocess.run(
				["nginx", "-t"],
				capture_output=True,
				text=True,
				timeout=10
			)
			if result.returncode == 0:
				return {
					"status": "healthy",
					"message": "Nginx configuration is valid"
				}
			else:
				return {
					"status": "unhealthy",
					"message": result.stderr
				}
		except Exception as e:
			return {
				"status": "unhealthy",
				"message": str(e)
			}
	
	def check_frappe(self) -> dict:
		"""Check Frappe health"""
		try:
			# Check if Frappe is responding
			frappe.db.sql("SELECT 1")
			return {
				"status": "healthy",
				"message": "Frappe is responding"
			}
		except Exception as e:
			return {
				"status": "unhealthy",
				"message": str(e)
			}
	
	def log_metrics(self, tenant_name: str = None):
		"""Log metrics for monitoring"""
		metrics = self.collect_metrics()
		health = self.check_health()
		
		self.logger.info(f"System Metrics: {metrics}")
		self.logger.info(f"System Health: {health}")
		
		if tenant_name:
			self.logger.info(f"Monitoring for tenant: {tenant_name}")
	
	def get_tenant_stats(self, tenant_name: str) -> dict:
		"""Get statistics for a specific tenant"""
		try:
			tenant = frappe.get_doc("SaaS Tenant", tenant_name)
			
			stats = {
				"tenant_name": tenant.tenant_name,
				"site_name": tenant.site_name,
				"status": tenant.status,
				"port_number": tenant.port_number,
				"provisioned_on": tenant.provisioned_on,
				"has_credentials": bool(tenant.admin_password),
				"site_url": tenant.site_url
			}
			
			return stats
		except Exception as e:
			self.logger.error(f"Failed to get tenant stats: {str(e)}")
			return {}
