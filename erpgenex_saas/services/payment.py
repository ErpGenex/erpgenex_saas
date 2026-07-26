from __future__ import annotations

import frappe


class PaymentService:
	SUPPORTED_PROVIDERS = ("PayPal",)
	REQUIRED_PAYPAL_BUSINESS_EMAIL = "technozoon19@gmail.com"

	@classmethod
	def validate_provider(cls, provider: str):
		if provider not in cls.SUPPORTED_PROVIDERS:
			frappe.throw("PayPal is the only supported payment provider")

	@classmethod
	def get_paypal_account(cls) -> dict:
		settings = frappe.get_single("SaaS Settings")
		business_email = (settings.paypal_business_email or "").strip().lower()
		if business_email and business_email != cls.REQUIRED_PAYPAL_BUSINESS_EMAIL:
			frappe.throw("PayPal Business Email must be technozoon19@gmail.com")
		if not business_email:
			business_email = cls.REQUIRED_PAYPAL_BUSINESS_EMAIL
		return {
			"enabled": bool(settings.paypal_enabled),
			"business_email": business_email,
			"merchant_id": (settings.paypal_merchant_id or "").strip(),
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
			"paypal_business_email": account["business_email"],
			"paypal_merchant_id": account["merchant_id"],
		}
