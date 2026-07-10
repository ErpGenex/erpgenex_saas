import frappe


def execute():
	"""
	Add max_sites field to SaaS Plan DocType
	"""
	doc = frappe.get_doc("DocType", "SaaS Plan")
	
	# Check if field already exists
	field_exists = False
	for field in doc.fields:
		if field.fieldname == "max_sites":
			field_exists = True
			break
	
	if not field_exists:
		# Add the field
		doc.append("fields", {
			"fieldname": "max_sites",
			"fieldtype": "Int",
			"label": "Maximum Sites",
			"description": "Maximum number of sites allowed for this plan (leave empty for unlimited)",
			"insert_after": "maximum_users"
		})
		doc.save()
		frappe.db.commit()
		frappe.clear_cache()
		print("Added max_sites field to SaaS Plan DocType")
	else:
		print("max_sites field already exists in SaaS Plan DocType")
