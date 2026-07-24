from __future__ import annotations

import os
import frappe
import secrets
import string
import hashlib


class PasswordManager:
	"""Manages password generation and validation"""
	
	def __init__(self):
		self.logger = frappe.logger("erpgenex_saas")
		self._fallback_db_password = secrets.token_urlsafe(16)
		self.password_policy = {
			"min_length": 12,
			"require_uppercase": True,
			"require_lowercase": True,
			"require_numbers": True,
			"require_special": True
		}
	
	def generate_password(self, length: int = 12) -> str:
		"""Generate a random secure password"""
		try:
			# Define character sets
			uppercase = string.ascii_uppercase
			lowercase = string.ascii_lowercase
			numbers = string.digits
			special = "!@#$%^&*()_+-=[]{}|;:,.<>?"
			
			# Ensure password meets policy
			all_chars = uppercase + lowercase + numbers + special
			password = []
			
			# Add at least one of each required character type
			if self.password_policy["require_uppercase"]:
				password.append(secrets.choice(uppercase))
			if self.password_policy["require_lowercase"]:
				password.append(secrets.choice(lowercase))
			if self.password_policy["require_numbers"]:
				password.append(secrets.choice(numbers))
			if self.password_policy["require_special"]:
				password.append(secrets.choice(special))
			
			# Fill the rest with random characters
			while len(password) < length:
				password.append(secrets.choice(all_chars))
			
			# Shuffle the password
			secrets.SystemRandom().shuffle(password)
			
			return ''.join(password)
		except Exception as e:
			self.logger.error(f"Failed to generate password: {str(e)}")
			# Fallback to simple password
			return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
	
	def validate_password_strength(self, password: str) -> dict:
		"""Validate password strength against policy"""
		result = {
			"valid": True,
			"errors": []
		}
		
		if len(password) < self.password_policy["min_length"]:
			result["valid"] = False
			result["errors"].append(f"Password must be at least {self.password_policy['min_length']} characters")
		
		if self.password_policy["require_uppercase"] and not any(c.isupper() for c in password):
			result["valid"] = False
			result["errors"].append("Password must contain at least one uppercase letter")
		
		if self.password_policy["require_lowercase"] and not any(c.islower() for c in password):
			result["valid"] = False
			result["errors"].append("Password must contain at least one lowercase letter")
		
		if self.password_policy["require_numbers"] and not any(c.isdigit() for c in password):
			result["valid"] = False
			result["errors"].append("Password must contain at least one number")
		
		if self.password_policy["require_special"] and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
			result["valid"] = False
			result["errors"].append("Password must contain at least one special character")
		
		return result
	
	def hash_password(self, password: str) -> str:
		"""Hash a password using SHA256 with salt for better security"""
		try:
			# Use SHA256 with salt for hashing (improved security)
			salt = secrets.token_hex(16)
			hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
			return f"{salt}${hashed}"
		except Exception as e:
			self.logger.error(f"Failed to hash password: {str(e)}")
			return None
	
	def verify_password(self, password: str, hashed: str) -> bool:
		"""Verify a password against a hash with salt"""
		try:
			if not hashed or '$' not in hashed:
				return False
			salt, stored_hash = hashed.split('$', 1)
			password_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
			return password_hash == stored_hash
		except Exception as e:
			self.logger.error(f"Failed to verify password: {str(e)}")
			return False
	
	def get_db_password(self) -> str:
		"""Get database password from SaaS Settings"""
		try:
			saas_settings = frappe.get_single("SaaS Settings")
			return (
				saas_settings.database_password
				or frappe.conf.get("erpgenex_saas_db_password")
				or os.environ.get("ERPGENEX_SAAS_DB_PASSWORD")
				or self._fallback_db_password
			)
		except Exception as e:
			self.logger.error(f"Failed to get DB password: {str(e)}")
			return (
				frappe.conf.get("erpgenex_saas_db_password")
				or os.environ.get("ERPGENEX_SAAS_DB_PASSWORD")
				or self._fallback_db_password
			)
	
	def get_mariadb_root_password(self) -> str:
		"""Get MariaDB root password from SaaS Settings, with safe fallback."""
		try:
			saas_settings = frappe.get_single("SaaS Settings")
			candidates = [
				saas_settings.mariadb_root_password,
				frappe.conf.get("erpgenex_saas_mariadb_root_password"),
				os.environ.get("ERPGENEX_SAAS_MARIADB_ROOT_PASSWORD"),
				os.environ.get("MARIADB_ROOT_PASSWORD"),
				os.environ.get("MYSQL_ROOT_PASSWORD"),
			]
			for password in candidates:
				if password and self._can_connect_as_root(password):
					return password
		except Exception as e:
			self.logger.error("Failed to get MariaDB root password: %s", str(e))
		raise frappe.ValidationError(
			"MariaDB root password is not configured. Set SaaS Settings or ERPGENEX_SAAS_MARIADB_ROOT_PASSWORD."
		)

	def _can_connect_as_root(self, password: str) -> bool:
		try:
			import pymysql

			conn = pymysql.connect(
				host="localhost",
				user="root",
				password=password,
				charset="utf8mb4",
			)
			conn.close()
			return True
		except Exception:
			return False
	
	def generate_api_key(self) -> str:
		"""Generate a secure API key"""
		return secrets.token_urlsafe(32)
	
	def generate_secret_key(self) -> str:
		"""Generate a secure secret key"""
		return secrets.token_hex(32)
