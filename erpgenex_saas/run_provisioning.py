import frappe
import time

def run_provisioning_manually():
    """Run provisioning request manually"""
    try:
        start_time = time.time()
        
        # Get the latest provisioning request using direct SQL for speed
        request_name = frappe.db.get_value("Provisioning Request", 
            {"status": "Queued"}, 
            order_by="creation desc",
            fieldname="name"
        )
        
        if not request_name:
            print("No queued provisioning request found")
            return None
        
        print(f"Running provisioning request: {request_name}")
        print(f"Time to fetch request: {time.time() - start_time:.2f}s")
        
        # Run the provisioning
        from erpgenex_saas.services.provisioning import ProvisioningService
        provision_start = time.time()
        ProvisioningService.run(request_name)
        print(f"Provisioning time: {time.time() - provision_start:.2f}s")
        
        print(f"Provisioning completed")
        
        # Check the status
        request = frappe.get_doc("Provisioning Request", request_name)
        print(f"Final Status: {request.status}")
        print(f"Last Message: {request.last_message}")
        
        print(f"Total time: {time.time() - start_time:.2f}s")
        return request.status
        
    except Exception as e:
        print(f"Error running provisioning: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
