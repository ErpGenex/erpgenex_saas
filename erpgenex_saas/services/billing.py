from __future__ import annotations

import frappe
from frappe.utils import nowdate

from erpgenex_saas.services.pricing import PricingService


class BillingService:
	@staticmethod
	def create_invoice_for_subscription(subscription_name: str):
		subscription = frappe.get_doc("SaaS Subscription", subscription_name)
		breakdown = PricingService.calculate(
			base_amount=subscription.base_amount or 0,
			apps_amount=subscription.apps_amount or 0,
			extra_users_amount=subscription.extra_users_amount or 0,
			extra_storage_amount=subscription.extra_storage_amount or 0,
			extra_services_amount=subscription.extra_services_amount or 0,
		)

		invoice = frappe.get_doc(
			{
				"doctype": "SaaS Invoice",
				"tenant": subscription.tenant,
				"subscription": subscription.name,
				"invoice_date": nowdate(),
				"status": "Draft",
				"currency": "USD",
				"amount_due": breakdown.total_amount
	}
		)
		invoice.insert(ignore_permissions=True)
		return invoice

	@staticmethod
	def register_payment(invoice_name: str, amount: float, provider: str, transaction_id: str):
		invoice = frappe.get_doc("SaaS Invoice", invoice_name)
		payment = frappe.get_doc(
			{
				"doctype": "SaaS Payment",
				"tenant": invoice.tenant,
				"invoice": invoice.name,
				"provider": provider,
				"transaction_id": transaction_id,
				"amount": amount,
				"status": "Verified"
	}
		)
		payment.insert(ignore_permissions=True)

		if float(amount) >= float(invoice.amount_due or 0):
			invoice.status = "Paid"
			invoice.paid_amount = amount
		else:
			invoice.status = "Partially Paid"
			invoice.paid_amount = amount
		invoice.save(ignore_permissions=True)
		return payment

	@staticmethod
	def create_invoice_for_source_purchase(source_purchase: str):
		purchase = frappe.get_doc("SaaS Source Purchase", source_purchase)
		invoice = frappe.get_doc(
			{
				"doctype": "SaaS Invoice",
				"tenant": purchase.tenant,
				"invoice_date": nowdate(),
				"status": "Draft",
				"currency": purchase.currency or "USD",
				"amount_due": purchase.amount or 0
	}
		)
		invoice.insert(ignore_permissions=True)
		purchase.invoice = invoice.name
		purchase.save(ignore_permissions=True)
		return invoice
