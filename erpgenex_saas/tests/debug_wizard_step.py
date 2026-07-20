"""Step-by-step debug for activity wizard provisioning."""
from __future__ import annotations

import json
import traceback

import frappe

from erpgenex_saas.services.activity_bundles import get_apps_for_activity
from erpgenex_saas.services.customer_onboarding import (
	ensure_customer_user,
	ensure_trial_subscription,
	link_subscription_to_provisioning,
)


def _step(label, fn):
	print(f"STEP {label} ...")
	try:
		result = fn()
		frappe.db.commit()
		print(f"OK {label}", json.dumps(result, ensure_ascii=False, default=str) if result else "")
		return result
	except Exception:
		print(f"FAIL {label}")
		print(traceback.format_exc())
		raise


def run():
	suffix = frappe.generate_hash(length=6).lower()
	data = {
		"tenant_name": f"Construction Co {suffix
	}",
		"company_email": f"construction-{suffix
	}@example.com",
		"customer_password": "TestPass123!",
		"subdomain": f"construction-{suffix
	}",
		"business_activity": "مقاولات",
		"server_type": "سيرفر مشترك"
	}
	print("DATA", json.dumps(data, ensure_ascii=False))

	def insert_wizard():
		wizard = frappe.new_doc("Activity Selection Wizard")
		wizard.tenant_name = data["tenant_name"]
		wizard.company_email = data["company_email"]
		wizard.subdomain = data["subdomain"]
		wizard.business_activity = data["business_activity"]
		wizard.server_type = data["server_type"]
		wizard.insert(ignore_permissions=True)
		return wizard.name

	wizard_name = _step("insert_wizard", insert_wizard)
	wizard = frappe.get_doc("Activity Selection Wizard", wizard_name)

	def create_tenant():
		wizard.create_tenant()
		return wizard.tenant or data["tenant_name"]

	tenant_name = _step("create_tenant", create_tenant)
	wizard.reload()

	def create_request():
		wizard.create_provisioning_request()
		return frappe.db.get_value(
			"Provisioning Request",
			{"tenant": tenant_name
	},
			"name",
			order_by="creation desc",
		)

	request_name = _step("create_request", create_request)

	def onboard_user():
		return ensure_customer_user(
			data["company_email"],
			data["tenant_name"],
			data["customer_password"],
			tenant_name,
		)

	_step("ensure_user", onboard_user)

	def onboard_sub():
		return ensure_trial_subscription(tenant_name, data["company_email"])

	sub_info = _step("ensure_subscription", onboard_sub)

	def link_sub():
		link_subscription_to_provisioning(tenant_name, request_name)
		return request_name

	_step("link_subscription", link_sub)

	def run_provisioning():
		from erpgenex_saas.services.provisioning import ProvisioningService

		ProvisioningService.run(request_name)
		tenant = frappe.get_doc("SaaS Tenant", tenant_name)
		return {
			"status": tenant.status,
			"access_url": tenant.access_url or tenant.site_url,
			"site_folder": tenant.site_folder
	}

	result = _step("provisioning", run_provisioning)
	print("DONE", json.dumps(result, ensure_ascii=False, default=str))
