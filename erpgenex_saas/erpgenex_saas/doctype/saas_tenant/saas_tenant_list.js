frappe.listview_settings['SaaS Tenant'] = {
	add_fields: ["admin_username", "admin_password", "site_url", "status", "access_url"],
	get_indicator: function(doc) {
		if (doc.status === "Active") {
			return [__("Active"), "green", "status,=,Active"];
		} else if (doc.status === "Draft") {
			return [__("Draft"), "grey", "status,=,Draft"];
		} else if (doc.status === "Provisioning") {
			return [__("Provisioning"), "orange", "status,=,Provisioning"];
		} else if (doc.status === "Suspended") {
			return [__("Suspended"), "red", "status,=,Suspended"];
		} else if (doc.status === "Archived") {
			return [__("Archived"), "darkgrey", "status,=,Archived"];
		}
	},
	onload: function(listview) {
		// Add custom button for deleting tenant
		listview.page.add_action_item('Delete Tenant', function() {
			let selected_docs = listview.get_checked_items();
			if (selected_docs.length === 0) {
				frappe.msgprint(__('Please select at least one tenant to delete'));
				return;
			}
			
			frappe.confirm(
				__('Are you sure you want to delete {0} tenant(s)? This action cannot be undone.', [selected_docs.length]),
				function() {
					selected_docs.forEach(function(doc) {
						frappe.call({
							method: 'erpgenex_saas.api.customer.archive_site',
							args: {
								tenant: doc.name
							},
							callback: function(r) {
								if (r.message && r.message.success) {
									frappe.msgprint(__('Tenant {0} deleted successfully', [doc.name]));
									listview.refresh();
								}
							}
						});
					});
				}
			);
		});
	}
};
