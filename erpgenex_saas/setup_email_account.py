import frappe
from erpgenex_saas.runtime_config import get_email_domain

def setup_default_email_account():
    """Setup default outgoing email account"""
    email_domain = get_email_domain()
    default_email = f"noreply@{email_domain}"
    try:
        # Check if email account already exists
        existing_accounts = frappe.get_all("Email Account", 
            filters={"email_id": default_email
	},
            fields=["name"]
        )
        
        if existing_accounts:
            print(f"Email account already exists: {existing_accounts[0]['name']}")
            return existing_accounts[0]['name']
        
        # Create default email account using sendmail instead of SMTP
        # This doesn't require SMTP validation
        email_account = frappe.new_doc("Email Account")
        email_account.email_id = default_email
        email_account.email_account_name = "Default Outgoing Email"
        email_account.enable_outgoing = 1
        email_account.use_smtp = 0  # Use sendmail instead of SMTP
        email_account.default_outgoing = 1
        email_account.add_to_auto_email_list = 1
        
        email_account.save(ignore_permissions=True)
        
        print(f"✅ Email account created: {email_account.name}")
        print(f"   Email ID: {email_account.email_id}")
        print(f"   Using sendmail (no SMTP validation required)")
        
        return email_account.name
        
    except Exception as e:
        print(f"Error setting up email account: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    setup_default_email_account()
