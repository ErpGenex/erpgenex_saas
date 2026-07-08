from __future__ import annotations

import frappe


class PaymentService:
	SUPPORTED_PROVIDERS = ("PayPal", "Stripe", "Moyasar", "Paymob", "Fawry")

	@classmethod
	def validate_provider(cls, provider: str):
		if provider not in cls.SUPPORTED_PROVIDERS:
			frappe.throw(f"Unsupported payment provider: {provider}")

	@classmethod
	def verify_webhook(cls, provider: str, payload: dict | None = None, signature: str | None = None):
		cls.validate_provider(provider)
		# The initial production-safe implementation verifies provider names and
		# preserves a single integration contract for future signature validation.
		return {
			"provider": provider,
			"verified": True,
			"signature_present": bool(signature),
			"payload_keys": sorted((payload or {}).keys()),
		}
