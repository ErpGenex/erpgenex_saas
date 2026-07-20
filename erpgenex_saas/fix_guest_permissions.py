import frappe

def fix_guest_permissions():
    """Fix Guest role permissions to allow user registration"""
    try:
        # Get Guest role
        guest_role = frappe.get_doc("Role", "Guest")
        print(f"Guest Role found: {guest_role.name}")
        
        # Check existing permissions
        existing_perms = frappe.get_all("DocPerm", 
            filters={"role": "Guest", "parenttype": "User"
	},
            fields=["*"]
        )
        
        has_user_permission = False
        for perm in existing_perms:
            if perm.get("read") or perm.get("write") or perm.get("create"):
                has_user_permission = True
                print(f"Guest already has User permission: {perm}")
                break
        
        if not has_user_permission:
            print("Adding User permission to Guest role...")
            # Get User DocType
            user_doctype = frappe.get_doc("DocType", "User")
            for perm in user_doctype.permissions:
                if perm.role == "Guest":
                    perm.read = 1
                    perm.write = 1
                    perm.create = 1
                    perm.delete = 0
                    perm.submit = 0
                    perm.cancel = 0
                    perm.amend = 0
                    break
            else:
                # Add new permission
                user_doctype.append("permissions", {
                    "role": "Guest",
                    "read": 1,
                    "write": 1,
                    "create": 1,
                    "delete": 0,
                    "submit": 0,
                    "cancel": 0,
                    "amend": 0
                })
            user_doctype.save(ignore_permissions=True)
            print("✅ User permission added to Guest role")
        
        # Check SaaS Customer Account permissions
        customer_account_perms = frappe.get_all("DocPerm", 
            filters={"role": "Guest", "parenttype": "SaaS Customer Account"
	},
            fields=["*"]
        )
        
        has_customer_account_permission = False
        for perm in customer_account_perms:
            if perm.get("read") or perm.get("write") or perm.get("create"):
                has_customer_account_permission = True
                print(f"Guest already has SaaS Customer Account permission: {perm}")
                break
        
        if not has_customer_account_permission:
            print("Adding SaaS Customer Account permission to Guest role...")
            try:
                customer_account_doctype = frappe.get_doc("DocType", "SaaS Customer Account")
                for perm in customer_account_doctype.permissions:
                    if perm.role == "Guest":
                        perm.read = 1
                        perm.write = 1
                        perm.create = 1
                        perm.delete = 0
                        perm.submit = 0
                        perm.cancel = 0
                        perm.amend = 0
                        break
                else:
                    # Add new permission
                    customer_account_doctype.append("permissions", {
                        "role": "Guest",
                        "read": 1,
                        "write": 1,
                        "create": 1,
                        "delete": 0,
                        "submit": 0,
                        "cancel": 0,
                        "amend": 0
                    })
                customer_account_doctype.save(ignore_permissions=True)
                print("✅ SaaS Customer Account permission added to Guest role")
            except Exception as e:
                print(f"Warning: Could not add SaaS Customer Account permission: {str(e)}")
        
        print("\n✅ Guest permissions updated successfully")
        return True
        
    except Exception as e:
        print(f"Error updating Guest permissions: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_guest_permissions()
