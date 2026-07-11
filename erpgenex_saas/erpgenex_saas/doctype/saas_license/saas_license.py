import frappe
from frappe.model.document import Document
import secrets
import hashlib
import json
from datetime import datetime, timedelta


class SaaSLicense(Document):
	def validate(self):
		"""Validate license before saving"""
		if not self.license_key:
			self.generate_license_key()

		if not self.license_hash:
			self.generate_license_hash()

	def generate_license_key(self):
		"""Generate a unique license key"""
		if not self.license_key:
			# Generate a 32-character hex string
			self.license_key = secrets.token_hex(16).upper()
			# Format as XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX-XXXX
			self.license_key = '-'.join([self.license_key[i:i+4] for i in range(0, 32, 4)])

	def generate_license_hash(self):
		"""Generate a hash for license verification"""
		if self.license_key and self.subscription:
			# Create hash from license key and subscription details
			hash_data = f"{self.license_key}-{self.subscription}-{self.license_type}"
			self.license_hash = hashlib.sha256(hash_data.encode()).hexdigest()

	def verify_license(self):
		"""Verify if the license is valid"""
		if not self.is_active:
			return False, "License is not active"

		if self.expiry_date and self.expiry_date < datetime.now().date():
			return False, "License has expired"

		if self.max_users and self.current_users > self.max_users:
			return False, "User limit exceeded"

		# Verify hash
		if self.license_key and self.license_hash:
			hash_data = f"{self.license_key}-{self.subscription}-{self.license_type}"
			expected_hash = hashlib.sha256(hash_data.encode()).hexdigest()
			if expected_hash != self.license_hash:
				return False, "License integrity check failed"

		return True, "License is valid"

	def renew_license(self, duration_months=12):
		"""Renew license for specified duration"""
		if self.expiry_date:
			new_expiry = self.expiry_date + timedelta(days=duration_months*30)
		else:
			new_expiry = datetime.now().date() + timedelta(days=duration_months*30)

		self.expiry_date = new_expiry
		self.is_active = 1
		self.generate_license_hash()
		self.save()

	def revoke_license(self):
		"""Revoke the license"""
		self.is_active = 0
		self.revocation_date = datetime.now().date()
		self.revocation_reason = "Manually revoked"
		self.save()

	@staticmethod
	def create_license(subscription, license_type="Standard", max_users=None, duration_months=12):
		"""Create a new license for a subscription"""
		license_doc = frappe.new_doc("SaaS License")
		license_doc.subscription = subscription
		license_doc.license_type = license_type
		license_doc.max_users = max_users or 10
		license_doc.expiry_date = datetime.now().date() + timedelta(days=duration_months*30)
		license_doc.is_active = 1
		license_doc.current_users = 0
		license_doc.generate_license_key()
		license_doc.generate_license_hash()
		license_doc.insert()
		return license_doc

	@staticmethod
	def validate_license_key(license_key):
		"""Validate a license key"""
		license_doc = frappe.get_all("SaaS License", 
			filters={"license_key": license_key, "is_active": 1},
			fields=["name", "subscription", "license_type", "expiry_date", "max_users", "current_users"]
		)

		if not license_doc:
			return False, "Invalid license key"

		license_doc = frappe.get_doc("SaaS License", license_doc[0].name)
		return license_doc.verify_license()
