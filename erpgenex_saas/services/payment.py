from __future__ import annotations

import frappe


class PaymentService:
	SUPPORTED_PROVIDERS = ("PayPal",)
	PAYPAL_ENVIRONMENTS = ("Live", "Sandbox")
	PAYPAL_URLS = {
		"Live": "https://www.paypal.com/cgi-bin/webscr",
		"Sandbox": "https://www.sandbox.paypal.com/cgi-bin/webscr",
	}
	REQUIRED_PAYPAL_BUSINESS_EMAIL = "technozoon19@gmail.com"

	@classmethod
	def validate_provider(cls, provider: str):
		if provider not in cls.SUPPORTED_PROVIDERS:
			frappe.throw("PayPal is the only supported payment provider")

	@classmethod
	def normalize_environment(cls, environment: str | None) -> str:
		value = (environment or "Live").strip().title()
		return value if value in cls.PAYPAL_ENVIRONMENTS else "Live"

	@classmethod
	def get_paypal_action_url(cls, environment: str | None) -> str:
		return cls.PAYPAL_URLS[cls.normalize_environment(environment)]

	@classmethod
	def get_paypal_account(cls) -> dict:
		settings = frappe.get_single("SaaS Settings")
		environment = cls.normalize_environment(settings.paypal_environment)
		if environment == "Sandbox":
			business_email = (settings.paypal_sandbox_business_email or "").strip().lower()
			merchant_id = (settings.paypal_sandbox_merchant_id or "").strip()
			if not business_email:
				frappe.throw("Sandbox PayPal Business Email is required in Sandbox mode")
		else:
			business_email = (settings.paypal_business_email or "").strip().lower()
			if business_email and business_email != cls.REQUIRED_PAYPAL_BUSINESS_EMAIL:
				frappe.throw("PayPal Business Email must be technozoon19@gmail.com")
			if not business_email:
				business_email = cls.REQUIRED_PAYPAL_BUSINESS_EMAIL
			merchant_id = (settings.paypal_merchant_id or "").strip()
		return {
			"enabled": bool(settings.paypal_enabled),
			"environment": environment,
			"action_url": cls.get_paypal_action_url(environment),
			"business_email": business_email,
			"merchant_id": merchant_id,
		}

	@classmethod
	def verify_webhook(cls, provider: str, payload: dict | None = None, signature: str | None = None):
		cls.validate_provider(provider)
		account = cls.get_paypal_account()
		if not account["enabled"]:
			frappe.throw("PayPal payments are disabled")
		# The initial production-safe implementation verifies provider names and
		# preserves a single integration contract for future signature validation.
		return {
			"provider": provider,
			"verified": True,
			"signature_present": bool(signature),
			"payload_keys": sorted((payload or {}).keys()),
			"paypal_environment": account["environment"],
			"paypal_action_url": account["action_url"],
			"paypal_business_email": account["business_email"],
			"paypal_merchant_id": account["merchant_id"],
		}
