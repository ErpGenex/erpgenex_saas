#!/usr/bin/env python3
"""
Script to update SaaS Application prices based on paid/free app lists
"""
import frappe
from erpgenex_saas.constants import (
	INCLUDED_APPS,
	PAID_LICENSED_APPS,
	PAID_APP_MONTHLY_PRICES,
	PAID_APP_SOURCE_CODE_PRICES,
)

def execute():
	"""Update app prices based on their classification"""
	print("Updating SaaS Application prices...")
	
	# Get all active SaaS Applications
	apps = frappe.get_all("SaaS Application", filters={"is_active": 1
	}, fields=["name"])
	
	updated_count = 0
	for app in apps:
		app_name = app.name
		doc = frappe.get_doc("SaaS Application", app_name)
		
		if app_name in INCLUDED_APPS:
			# Core/included apps - free
			doc.monthly_price = 0
			doc.annual_price = 0
			doc.source_code_price = 0
			print(f"Updated (Free): {app_name}")
		elif app_name in PAID_LICENSED_APPS:
			# Paid licensed apps - use specific pricing
			doc.monthly_price = PAID_APP_MONTHLY_PRICES.get(app_name, 0)
			doc.annual_price = round(doc.monthly_price * 10, 2)
			doc.source_code_price = PAID_APP_SOURCE_CODE_PRICES.get(app_name, 0)
			print(f"Updated (Paid): {app_name} - Monthly: ${doc.monthly_price}, Source: ${doc.source_code_price}")
		else:
			# Other apps - free
			doc.monthly_price = 0
			doc.annual_price = 0
			doc.source_code_price = 0
			print(f"Updated (Free): {app_name}")
		
		doc.save(ignore_permissions=True)
		updated_count += 1
	
	print(f"Successfully updated {updated_count} applications")
	return updated_count

if __name__ == "__main__":
	execute()
