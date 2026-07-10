from __future__ import annotations

import frappe
import json
import subprocess
import os
import shutil

from erpgenex_saas.services.audit import AuditService
from erpgenex_saas.services.deployment import DeploymentService
from erpgenex_saas.services.activity_bundles import CORE_PLATFORM_APPS, get_apps_for_activity, normalize_app_entry
from erpgenex_saas.services.deployment_settings import (
	build_subdomain,
	get_deployment_config,
	normalize_subdomain,
)
from erpgenex_saas.services.domain import DomainService
from erpgenex_saas.services.notification import NotificationService
from erpgenex_saas.services.progress_tracker import ProgressTracker
from erpgenex_saas.services.password_manager import PasswordManager
from erpgenex_saas.services.monitoring_service import MonitoringService
from erpgenex_saas.services.provisioning_logger import ProvisioningLogger


class ProvisioningService:
	@staticmethod
	def enqueue_request(request_name: str):
		frappe.enqueue(
			"erpgenex_saas.tasks.run_provisioning_request",
			queue="long",
			timeout=3600,
			enqueue_after_commit=True,
			request_name=request_name,
		)

	@staticmethod
	def run(request_name: str):
		logger = frappe.logger("erpgenex_saas")
		request = frappe.get_doc("Provisioning Request", request_name)
		existing_log = request.execution_log or ""
		provisioning_config = {}
		if existing_log.strip().startswith("{"):
			try:
				provisioning_config = json.loads(existing_log)
			except json.JSONDecodeError:
				provisioning_config = {}

		request.status = "Running"
		request.last_message = "Provisioning started"
		request.execution_log = "Queued request picked up by worker\n"
		if provisioning_config:
			request.execution_log += json.dumps(provisioning_config, ensure_ascii=False) + "\n"
		request.save(ignore_permissions=True)

		# Initialize services
		progress_tracker = ProgressTracker()
		password_manager = PasswordManager()
		monitoring = MonitoringService()
		
		# Start progress tracking
		progress_tracker.start(request.tenant)
		
		# Log system metrics
		monitoring.log_metrics(request.tenant)

		try:
			# Parse execution log for activity and server configuration
			if not provisioning_config and request.execution_log:
				for line in request.execution_log.splitlines():
					line = line.strip()
					if line.startswith("{"):
						try:
							provisioning_config = json.loads(line)
							break
						except json.JSONDecodeError:
							continue

			deployment_config = get_deployment_config()
			site_distribution_method = deployment_config.deployment_mode
			saas_settings = frappe.get_single("SaaS Settings")

			# This is the safe initial implementation layer: record intent and prepare
			# future site creation/dns/ssl/install hooks without touching existing apps.
			tenant = frappe.get_doc("SaaS Tenant", request.tenant)
			tenant.status = "Provisioning"
			
			# Handle server type configuration
			server_type = provisioning_config.get("server_type", "سيرفر مشترك")
			server_config = provisioning_config.get("server_config", {})
			
			# Update progress
			progress_tracker.update(request.tenant, "configuring_server", 10)
			
			logger.info(f"Server type: {server_type}")
			logger.info(f"Server config: {server_config}")
			logger.info(f"Site distribution method: {site_distribution_method}")
			
			slug = normalize_subdomain(tenant.subdomain or tenant.name)
			tenant.deployment_mode = site_distribution_method

			if server_type == "سيرفر مخصص" and server_config:
				logger.info("Using dedicated server configuration")
				domain_name = server_config.get("domain_name", "")
				server_ip = server_config.get("server_ip", "")
				enable_ssl = server_config.get("enable_ssl", False)

				if domain_name:
					tenant.site_name = domain_name
					tenant.site_folder = domain_name
					tenant.custom_domain = domain_name
					request.execution_log += f"Using dedicated server: {server_ip}\nDomain: {domain_name}\n"
					if enable_ssl:
						request.execution_log += "SSL enabled\n"
				else:
					logger.info("No domain provided, falling back to deployment mode defaults")
					if site_distribution_method == "Port":
						tenant.site_name = slug
						tenant.site_folder = slug
					else:
						tenant.site_name = build_subdomain(slug, deployment_config)
						tenant.site_folder = tenant.site_name
			else:
				logger.info(
					"Using shared server configuration, deployment_mode: %s",
					site_distribution_method,
				)
				if site_distribution_method == "Port":
					tenant.site_name = slug
					tenant.site_folder = slug
				else:
					tenant.site_name = build_subdomain(slug, deployment_config)
					tenant.site_folder = tenant.site_name
			
			logger.info("Final site name: %s, site_folder: %s", tenant.site_name, tenant.site_folder)

			tenant.flags.ignore_version = True
			tenant.save(ignore_permissions=True)
			frappe.db.commit()

			site_folder = tenant.site_folder or tenant.site_name or slug
			if not site_folder:
				frappe.throw(f"Could not resolve site folder for tenant {tenant.name}")

			# Update progress
			progress_tracker.update(request.tenant, "tenant_configured", 20)

			# Log business activity and apps to install.
			# New SaaS flow creates the site with Frappe only; apps are installed later from dashboard.
			business_activity = provisioning_config.get("business_activity", "عام")
			if "apps_to_install" in provisioning_config:
				raw_apps = provisioning_config.get("apps_to_install") or []
				apps_to_install = [
					slug
					for slug in (normalize_app_entry(item) for item in raw_apps)
					if slug and slug != "frappe"
				]
			else:
				apps_to_install = get_apps_for_activity(business_activity) or []
			
			request.execution_log += f"Business Activity: {business_activity}\n"
			request.execution_log += f"Site Distribution Method: {site_distribution_method}\n"
			request.execution_log += f"Apps to install: {', '.join(str(app) for app in apps_to_install)}\n"
			
			request.last_message = "Provisioning blueprint created. Site automation pending next phase."
			request.execution_log += (
				f"Tenant set to Provisioning\nReserved site placeholder: {tenant.site_name}\n"
			)
			
			# Create the actual site in /home/frappeuser/frappe-bench/sites
			request.execution_log += f"Creating actual site: {tenant.site_name}\n"
			
			# Update progress
			progress_tracker.update(request.tenant, "creating_site", 30)

			stage_logger = ProvisioningLogger(tenant.name, request.name)
			with stage_logger.stage("Create Site"):
				progress_tracker.update(request.tenant, "creating_site_files", 35)
				site_created = ProvisioningService.create_site(site_folder, tenant.name)
				if not site_created:
					ProvisioningService.cleanup_failed_tenant(
						tenant.name,
						site_folder=site_folder,
						reason="Site creation returned false",
					)
					raise RuntimeError(f"Site creation failed for folder {site_folder}")

			if site_created:
				request.execution_log += "Site created successfully\n"
				tenant.reload()

				progress_tracker.update(request.tenant, "site_created", 60)

				if apps_to_install:
					with stage_logger.stage("Install Apps"):
						ProvisioningService.install_tenant_apps(site_folder, apps_to_install)

					with stage_logger.stage("Migration"):
						ProvisioningService.migrate_site(site_folder)
				else:
					request.execution_log += "No additional apps requested during site creation; Frappe-only site created.\n"

				deployment_result = DeploymentService.deploy_tenant(
					tenant.name,
					site_folder,
					request.name,
					subdomain_slug=slug,
				)
				request.execution_log += f"Deployment: {deployment_result}\n"
				tenant.reload()
			else:
				request.execution_log += f"Site creation failed, continuing with database record only\n"
				request.last_message = "Site creation failed. Provisioning incomplete."
				
				# Mark progress as failed
				progress_tracker.fail(request.tenant, "Site creation failed")
				
				# Don't mark tenant as active if site creation failed
				tenant.reload()
				tenant.status = "Draft"
				tenant.provisioned_on = None
				tenant.save(ignore_permissions=True)
				
				# Still mark request as completed but with failure status
				request.status = "Failed"
				request.save(ignore_permissions=True)
				
				logger.error(f"Site creation failed for tenant {tenant.name}, provisioning incomplete")
				return
			
			request.status = "Completed"
			request.save(ignore_permissions=True)

			tenant.reload()
			tenant.status = "Active"
			tenant.provisioned_on = frappe.utils.now_datetime()
			tenant.flags.ignore_version = True
			tenant.save(ignore_permissions=True)

			# Update progress
			progress_tracker.update(request.tenant, "tenant_activated", 80)

			if request.subscription:
				subscription = frappe.get_doc("SaaS Subscription", request.subscription)
				subscription.provisioned = 1
				subscription.status = "Active" if subscription.status == "Draft" else subscription.status
				subscription.save(ignore_permissions=True)

			NotificationService.notify(
				tenant.name,
				"registration",
				"Tenant provisioned",
				f"Your tenant site {tenant.site_name} is ready.",
			)
			AuditService.log(
				"provisioning.completed",
				request.name,
				{
					"tenant": tenant.name, 
					"site_name": tenant.site_name,
					"business_activity": business_activity,
					"server_type": server_type,
					"site_distribution_method": site_distribution_method
				},
			)
			
			# Mark progress as completed
			progress_tracker.complete(request.tenant)
			
			# Log final metrics
			monitoring.log_metrics(request.tenant)
			
			logger.info("Provisioning completed for tenant %s with activity %s using %s distribution", 
				tenant.name, business_activity, site_distribution_method)
		except Exception:
			error_message = frappe.get_traceback(with_context=True)
			cleanup_message = ""
			try:
				tenant_name = request.tenant
				tenant_doc = frappe.get_doc("SaaS Tenant", tenant_name)
				cleanup_result = ProvisioningService.cleanup_failed_tenant(
					tenant_name,
					site_folder=tenant_doc.site_folder or tenant_doc.site_name or locals().get("site_folder"),
					reason="Provisioning failed",
				)
				cleanup_message = f"\nCleanup: {cleanup_result.get('message')}"
			except Exception:
				cleanup_message = "\nCleanup failed:\n" + frappe.get_traceback(with_context=True)

			request.status = "Failed"
			request.last_message = error_message + cleanup_message
			request.save(ignore_permissions=True)
			progress_tracker.fail(request.tenant, "فشل إنشاء الموقع وتم تنظيف الملفات تلقائيًا")
			logger.error("Provisioning failed for request %s", request_name)
			raise

	@staticmethod
	def _site_has_app(site_folder: str, app: str) -> bool:
		bench_path = "/home/frappeuser/frappe-bench"
		result = subprocess.run(
			["bench", "--site", site_folder, "list-apps"],
			cwd=bench_path,
			capture_output=True,
			text=True,
			timeout=120,
			check=False,
		)
		if result.returncode != 0:
			return False
		return app in result.stdout

	@staticmethod
	def _minimal_omnexa_install_env() -> dict:
		env = os.environ.copy()
		env["OMNEXA_AUTO_INSTALL_FULL_STACK_ON_CORE"] = "0"
		env["OMNEXA_INSTALL_ALL_GITHUB_APPS"] = "0"
		env["OMNEXA_AUTO_GET_APPS"] = "0"
		return env

	@staticmethod
	def _run_bench_install_app(site_folder: str, app: str, *, minimal_core: bool = False) -> subprocess.CompletedProcess:
		bench_path = "/home/frappeuser/frappe-bench"
		env = ProvisioningService._minimal_omnexa_install_env() if minimal_core else os.environ.copy()
		return subprocess.run(
			["bench", "--site", site_folder, "install-app", app],
			cwd=bench_path,
			capture_output=True,
			text=True,
			timeout=1800,
			check=False,
			env=env,
		)

	@staticmethod
	def install_tenant_apps(site_folder: str, apps_to_install: list | None = None):
		logger = frappe.logger("erpgenex_saas")
		raw = list(apps_to_install or [])
		apps: list[str] = []
		for item in raw:
			slug = normalize_app_entry(item)
			if slug and slug not in apps:
				apps.append(slug)

		platform_apps = set(CORE_PLATFORM_APPS)
		if "omnexa_core" not in apps:
			apps.insert(0, "omnexa_core")

		# Phase 1: omnexa_core bootstraps the basic platform stack only (not full bench).
		if not ProvisioningService._site_has_app(site_folder, "omnexa_core"):
			logger.info("Installing omnexa_core (minimal platform stack) on %s", site_folder)
			try:
				result = ProvisioningService._run_bench_install_app(
					site_folder, "omnexa_core", minimal_core=True
				)
				if result.returncode != 0 and not ProvisioningService._site_has_app(site_folder, "omnexa_core"):
					logger.error("Failed to install omnexa_core on %s: %s", site_folder, result.stderr)
					raise RuntimeError(result.stderr or "Failed to install omnexa_core")
			except subprocess.TimeoutExpired:
				if not ProvisioningService._site_has_app(site_folder, "omnexa_core"):
					raise RuntimeError(f"Timed out installing omnexa_core on {site_folder}")

		# Phase 2: install every requested app after core. This lets dashboard install
		# the core/basic bundle first, then any additional vertical app.
		requested_apps = [app for app in apps if app not in {"frappe", "omnexa_core"}]
		for app in requested_apps:
			if ProvisioningService._site_has_app(site_folder, app):
				logger.info("Skipping %s on %s (already installed)", app, site_folder)
				continue
			logger.info("Installing vertical app %s on %s", app, site_folder)
			try:
				result = ProvisioningService._run_bench_install_app(site_folder, app)
			except subprocess.TimeoutExpired:
				if ProvisioningService._site_has_app(site_folder, app):
					logger.warning(
						"Install timed out for %s on %s but app is present; continuing",
						app,
						site_folder,
					)
					continue
				raise RuntimeError(f"Timed out installing {app} on {site_folder}")
			if result.returncode != 0:
				if ProvisioningService._site_has_app(site_folder, app):
					logger.warning(
						"Install returned error for %s on %s but app is present; continuing",
						app,
						site_folder,
					)
					continue
				logger.error("Failed to install %s on %s: %s", app, site_folder, result.stderr)
				raise RuntimeError(result.stderr or f"Failed to install {app}")
			logger.info("Installed %s on %s", app, site_folder)

	@staticmethod
	def migrate_site(site_folder: str):
		bench_path = "/home/frappeuser/frappe-bench"
		result = subprocess.run(
			["bench", "--site", site_folder, "migrate"],
			cwd=bench_path,
			capture_output=True,
			text=True,
			timeout=1800,
			check=False,
		)
		if result.returncode != 0:
			raise RuntimeError(result.stderr or "Site migration failed")

	@staticmethod
	def pre_flight_checks():
		"""Perform pre-flight checks before site creation"""
		try:
			logger = frappe.logger("erpgenex_saas")
			logger.info("Starting pre-flight checks")
			
			# Check MariaDB connectivity
			password_manager = PasswordManager()
			mariadb_root_password = password_manager.get_mariadb_root_password()
			
			try:
				frappe.db.sql("SELECT 1")
				logger.info("MariaDB connectivity check passed")
			except Exception as e:
				logger.error(f"MariaDB connectivity check failed: {str(e)}")
				return False
			
			# Check disk space
			bench_path = "/home/frappeuser/frappe-bench"
			sites_path = os.path.join(bench_path, "sites")
			disk_usage = shutil.disk_usage(sites_path)
			free_space_gb = disk_usage.free / (1024**3)
			
			if free_space_gb < 1:  # Less than 1GB free
				logger.error(f"Insufficient disk space: {free_space_gb:.2f}GB free")
				return False
			
			logger.info(f"Disk space check passed: {free_space_gb:.2f}GB free")
			
			# Check SaaS Settings
			try:
				saas_settings = frappe.get_single("SaaS Settings")
				if not saas_settings.database_password:
					logger.error("Database password not set in SaaS Settings")
					return False
				if not saas_settings.mariadb_root_password:
					logger.error("MariaDB root password not set in SaaS Settings")
					return False
				logger.info("SaaS Settings check passed")
			except Exception as e:
				logger.error(f"SaaS Settings check failed: {str(e)}")
				return False
			
			logger.info("Pre-flight checks completed successfully")
			return True
			
		except Exception as e:
			logger.error(f"Pre-flight checks failed: {str(e)}")
			return False

	@staticmethod
	def _read_site_db_name(folder_name: str) -> str | None:
		bench_path = "/home/frappeuser/frappe-bench"
		site_config_path = os.path.join(bench_path, "sites", folder_name, "site_config.json")
		if not os.path.exists(site_config_path):
			return None
		with open(site_config_path, encoding="utf-8") as config_file:
			config = json.load(config_file)
		return config.get("db_name")

	@staticmethod
	def _root_sql(query: str, params=None):
		import pymysql

		root_password = PasswordManager().get_mariadb_root_password()
		connection = pymysql.connect(
			host="localhost",
			user="root",
			password=root_password,
			charset="utf8mb4",
		)
		try:
			with connection.cursor() as cursor:
				cursor.execute(query, params or ())
				return cursor.fetchall()
		finally:
			connection.close()

	@staticmethod
	def cleanup_failed_tenant(tenant_name: str, site_folder: str | None = None, reason: str | None = None) -> dict:
		"""Remove a failed tenant site folder/database and free runtime resources."""
		logger = frappe.logger("erpgenex_saas")
		if not tenant_name or not frappe.db.exists("SaaS Tenant", tenant_name):
			return {"success": False, "message": "Tenant not found"}

		tenant = frappe.get_doc("SaaS Tenant", tenant_name)
		folder_name = site_folder or tenant.site_folder or tenant.site_name

		DeploymentService.release_tenant_resources(tenant_name)
		database_removed = True
		folder_removed = True
		if folder_name:
			database_removed = ProvisioningService.rollback_database(folder_name)
			folder_removed = ProvisioningService.rollback_site_folder(folder_name)

		tenant.reload()
		tenant.status = "Archived"
		tenant.service_status = "Stopped"
		tenant.health_status = "Unknown"
		tenant.site_folder = None
		tenant.site_name = None
		tenant.site_url = None
		tenant.access_url = None
		tenant.port_number = None
		tenant.provisioned_on = None
		tenant.flags.ignore_version = True
		tenant.save(ignore_permissions=True)

		request_name = frappe.db.get_value(
			"Provisioning Request",
			{"tenant": tenant_name, "status": ["in", ["Queued", "Running"]]},
			"name",
			order_by="creation desc",
		)
		if request_name:
			frappe.db.set_value(
				"Provisioning Request",
				request_name,
				{
					"status": "Failed",
					"last_message": reason or "Provisioning failed and tenant was cleaned up",
				},
				update_modified=True,
			)
		wizard_name = frappe.db.get_value(
			"Activity Selection Wizard",
			{"tenant_name": tenant_name},
			"name",
			order_by="creation desc",
		)
		if wizard_name:
			frappe.db.set_value(
				"Activity Selection Wizard",
				wizard_name,
				{
					"status": "فشل",
					"provisioning_status": "فشل التجهيز وتم تنظيف الموقع",
					"error_message": reason or "فشل إنشاء الموقع وتم حذف الملفات تلقائيًا",
				},
				update_modified=True,
			)
		frappe.db.commit()

		logger.info(
			"Cleaned tenant %s after failure. folder=%s database_removed=%s folder_removed=%s reason=%s",
			tenant_name,
			folder_name,
			database_removed,
			folder_removed,
			reason or "",
		)
		return {
			"success": bool(database_removed and folder_removed),
			"message": "تم حذف ملفات وقاعدة بيانات الموقع تلقائيًا" if folder_name else "تم تحرير موارد الموقع",
			"site_folder": folder_name,
			"database_removed": database_removed,
			"folder_removed": folder_removed,
		}

	@staticmethod
	def rollback_database(folder_name):
		"""Rollback database creation"""
		try:
			logger = frappe.logger("erpgenex_saas")
			bench_path = "/home/frappeuser/frappe-bench"
			site_config_path = os.path.join(bench_path, "sites", folder_name, "site_config.json")
			
			# Read database name from site_config.json
			db_name = None
			if os.path.exists(site_config_path):
				import json
				with open(site_config_path, 'r') as f:
					config = json.load(f)
				db_name = config.get('db_name')
			
			if not db_name:
				# Fallback to folder name
				db_name = folder_name.replace('-', '_').replace('.', '_')
			
			logger.info(f"Rolling back database: {db_name}")
			
			# Drop database
			try:
				ProvisioningService._root_sql(f"DROP DATABASE IF EXISTS `{db_name}`")
				logger.info(f"Dropped database: {db_name}")
			except Exception as e:
				logger.warning(f"Failed to drop database {db_name}: {str(e)}")
			
			# Drop user
			try:
				ProvisioningService._root_sql(f"DROP USER IF EXISTS `{db_name}`@`%`")
				ProvisioningService._root_sql(f"DROP USER IF EXISTS `{db_name}`@`localhost`")
				logger.info(f"Dropped user: {db_name}")
			except Exception as e:
				logger.warning(f"Failed to drop user {db_name}: {str(e)}")
			
			# Flush privileges
			try:
				ProvisioningService._root_sql("FLUSH PRIVILEGES")
				logger.info("Flushed privileges")
			except Exception as e:
				logger.warning(f"Failed to flush privileges: {str(e)}")
			
			logger.info(f"Database rollback completed for {db_name}")
			return True
		except Exception as e:
			logger.error(f"Database rollback failed: {str(e)}")
			return False

	@staticmethod
	def rollback_site_folder(folder_name):
		"""Rollback site folder creation"""
		try:
			logger = frappe.logger("erpgenex_saas")
			bench_path = "/home/frappeuser/frappe-bench"
			site_path = os.path.join(bench_path, "sites", folder_name)
			
			if os.path.exists(site_path):
				logger.info(f"Rolling back site folder: {folder_name}")
				shutil.rmtree(site_path)
				logger.info(f"Site folder rollback completed for {folder_name}")
			else:
				logger.info(f"Site folder does not exist: {folder_name}")
			
			return True
		except Exception as e:
			logger.error(f"Site folder rollback failed: {str(e)}")
			return False

	@staticmethod
	def verify_database(folder_name):
		"""Verify database creation"""
		try:
			logger = frappe.logger("erpgenex_saas")
			bench_path = "/home/frappeuser/frappe-bench"
			site_config_path = os.path.join(bench_path, "sites", folder_name, "site_config.json")
			
			db_name = ProvisioningService._read_site_db_name(folder_name)
			if not db_name:
				logger.error("site_config.json not found for %s", folder_name)
				return False
			
			logger.info(f"Verifying database: {db_name}")
			
			result = ProvisioningService._root_sql("SHOW DATABASES LIKE %s", (db_name,))
			if not result:
				logger.error(f"Database {db_name} does not exist")
				return False
			
			logger.info(f"Database {db_name} verified")
			return True
		except Exception as e:
			logger.error(f"Database verification failed: {str(e)}")
			return False

	@staticmethod
	def verify_database_user(folder_name):
		"""Verify database user creation"""
		try:
			logger = frappe.logger("erpgenex_saas")
			bench_path = "/home/frappeuser/frappe-bench"
			site_config_path = os.path.join(bench_path, "sites", folder_name, "site_config.json")
			
			db_name = ProvisioningService._read_site_db_name(folder_name)
			if not db_name:
				logger.error("site_config.json not found for %s", folder_name)
				return False
			
			logger.info(f"Verifying database user: {db_name}")
			
			result = ProvisioningService._root_sql(
				"SELECT User FROM mysql.user WHERE User = %s",
				(db_name,),
			)
			if not result:
				logger.error(f"Database user {db_name} does not exist")
				return False
			
			logger.info(f"Database user {db_name} verified")
			return True
		except Exception as e:
			logger.error(f"Database user verification failed: {str(e)}")
			return False

	@staticmethod
	def create_site(site_name, tenant_name):
		"""Create actual Frappe site in /home/frappeuser/frappe-bench/sites"""
		import re
		try:
			logger = frappe.logger("erpgenex_saas")
			bench_path = "/home/frappeuser/frappe-bench"

			if not site_name:
				logger.error("create_site called with empty site_name for tenant %s", tenant_name)
				return False

			# Sanitize site name to prevent directory traversal and injection attacks
			site_name = re.sub(r'[^a-zA-Z0-9\-_.]', '-', site_name)[:100]
			site_name = re.sub(r'\.{2,}', '.', site_name).strip('-_.')

			logger.info("create_site called with site_name=%s, tenant_name=%s", site_name, tenant_name)
			
			# Pre-flight checks
			logger.info("Running pre-flight checks...")
			if not ProvisioningService.pre_flight_checks():
				logger.error("Pre-flight checks failed, aborting site creation")
				return False
			logger.info("Pre-flight checks passed")
			
			# Initialize password manager
			password_manager = PasswordManager()
			
			# Get server configuration
			saas_settings = frappe.get_single("SaaS Settings")
			server_ip = saas_settings.server_ip or "192.168.1.2"
			server_port = saas_settings.server_port or "8088"
			
			# Get passwords from PasswordManager
			database_password = password_manager.get_db_password()
			mariadb_root_password = password_manager.get_mariadb_root_password()
			
			# Generate random admin password for the user
			admin_password = password_manager.generate_password(length=12)
			
			folder_name = site_name
			db_name = folder_name.replace("-", "_").replace(".", "_")
			
			# Ensure database name doesn't conflict with reserved names
			reserved_names = ['sys', 'mysql', 'information_schema', 'performance_schema', 'test']
			if db_name.lower() in reserved_names:
				db_name = f"saas_{db_name}"
			
			# Validate database name length (MySQL limit is 64 characters)
			db_name = db_name[:60]
			
			# Check if site already exists
			site_path = os.path.join(bench_path, "sites", folder_name)
			logger.info(f"Checking if site exists at {site_path}")
			if os.path.exists(site_path):
				logger.info(f"Site {folder_name} already exists, skipping creation")
				return True
			logger.info(f"Site does not exist, proceeding with creation")
			
			# Check for orphaned databases and clean them up (disabled for performance)
			# This check is slow and should be run periodically instead of on every site creation
			logger.info("Skipping orphaned database check for performance")
			
			# Create the site using bench new-site command
			logger.info(f"Creating new site: {folder_name} (will be accessible on {site_name})")
			
			# Use bench new-site command with password from settings
			# Use admin-password for site admin and mariadb-root-password for MariaDB authentication
			# Use db-name and db-password for explicit database configuration
			command = [
				"bench",
				"new-site",
				folder_name,
				"--admin-password", admin_password,
				"--mariadb-root-password", mariadb_root_password,
				"--db-name", db_name,
				"--db-password", database_password,
				"--mariadb-user-host-login-scope=%",
				"--force",
			]
			
			result = subprocess.run(
				command,
				cwd=bench_path,
				capture_output=True,
				text=True,
				timeout=300  # 5 minutes timeout
			)
			
			logger.info(f"Site creation subprocess returned code: {result.returncode}")
			logger.info(f"Full STDOUT: {result.stdout}")
			if result.stderr:
				logger.error(f"Full STDERR: {result.stderr}")
			
			if result.returncode == 0:
				logger.info(f"Site {folder_name} created successfully with password from settings")
				
				# Verify database creation
				if not ProvisioningService.verify_database(folder_name):
					logger.error("Database verification failed, rolling back")
					ProvisioningService.rollback_database(folder_name)
					ProvisioningService.rollback_site_folder(folder_name)
					return False
				
				# Verify database user creation
				if not ProvisioningService.verify_database_user(folder_name):
					logger.error("Database user verification failed, rolling back")
					ProvisioningService.rollback_database(folder_name)
					ProvisioningService.rollback_site_folder(folder_name)
					return False
				
				# Update site_config.json with the correct database password
				site_config_path = os.path.join(bench_path, "sites", folder_name, "site_config.json")
				if os.path.exists(site_config_path):
					import json
					with open(site_config_path, 'r') as f:
						config = json.load(f)
					config['db_password'] = database_password
					config['omnexa_auto_install_full_stack_on_core'] = 0
					config['omnexa_install_all_github_apps'] = 0
					with open(site_config_path, 'w') as f:
						json.dump(config, f, indent=2)
					logger.info(f"Updated database password in site_config.json")
				
				ProvisioningService.set_admin_password(folder_name, admin_password)

				try:
					frappe.db.set_value(
						"SaaS Tenant",
						tenant_name,
						{
							"admin_username": "Administrator",
							"admin_password": admin_password,
							"site_folder": folder_name,
						},
						update_modified=False,
					)
					logger.info("Saved admin credentials to tenant %s", tenant_name)
				except Exception as e:
					logger.error("Failed to save admin credentials: %s", str(e))
				
				return True
			else:
				logger.error(f"Failed to create site {folder_name}: {result.stderr}")
				# Rollback on failure
				ProvisioningService.rollback_database(folder_name)
				ProvisioningService.rollback_site_folder(folder_name)
				return False
				
		except subprocess.TimeoutExpired:
			logger.error(f"Site creation timed out for {site_name}")
			ProvisioningService.rollback_database(site_name)
			ProvisioningService.rollback_site_folder(site_name)
			return False
		except Exception as e:
			logger.error(f"Error creating site {site_name}: {str(e)}")
			ProvisioningService.rollback_database(site_name)
			ProvisioningService.rollback_site_folder(site_name)
			return False

	@staticmethod
	def set_admin_password(folder_name: str, admin_password: str):
		bench_path = "/home/frappeuser/frappe-bench"
		result = subprocess.run(
			["bench", "--site", folder_name, "set-admin-password", admin_password],
			cwd=bench_path,
			capture_output=True,
			text=True,
			timeout=60,
			check=False,
		)
		if result.returncode != 0:
			frappe.logger("erpgenex_saas").warning(
				"Failed to set admin password for %s: %s", folder_name, result.stderr
			)
