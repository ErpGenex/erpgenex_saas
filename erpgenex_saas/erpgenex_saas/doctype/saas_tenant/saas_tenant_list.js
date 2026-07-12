frappe.listview_settings['SaaS Tenant'] = {
	add_fields: ["admin_username", "admin_password", "site_url", "status", "access_url", "site_folder"],
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
		// Add custom button for copying admin password
		listview.page.add_menu_item(__('Copy Admin Password'), function() {
			let selected_docs = listview.get_checked_items();
			if (selected_docs.length === 0) {
				frappe.msgprint(__('Please select at least one tenant'));
				return;
			}
			if (selected_docs.length > 1) {
				frappe.msgprint(__('Please select only one tenant to copy password'));
				return;
			}
			let doc = selected_docs[0];
			if (doc.admin_password) {
				navigator.clipboard.writeText(doc.admin_password).then(function() {
					frappe.msgprint(__('Password copied to clipboard'));
				}, function() {
					frappe.msgprint(__('Failed to copy password'));
				});
			} else {
				frappe.msgprint(__('No password available for this tenant'));
			}
		}, true);

		// Add custom button for installing core apps
		listview.page.add_menu_item(__('Install Core Apps'), function() {
			let selected_docs = listview.get_checked_items();
			if (selected_docs.length === 0) {
				frappe.msgprint(__('Please select at least one tenant'));
				return;
			}
			if (selected_docs.length > 1) {
				frappe.msgprint(__('Please select only one tenant'));
				return;
			}
			let doc = selected_docs[0];
			if (!doc.site_folder) {
				frappe.msgprint(__('Site folder not available for this tenant'));
				return;
			}
			frappe.confirm(
				__('Are you sure you want to install core apps for {0}?', [doc.name]),
				function() {
					frappe.call({
						method: 'erpgenex_saas.services.provisioning.install_core_apps',
						args: {
							site_folder: doc.site_folder
						},
						callback: function(r) {
							if (r.message) {
								frappe.msgprint(r.message);
								listview.refresh();
							}
						}
					});
				}
			);
		}, true);

		// Add custom button for deleting tenant with cleanup
		listview.page.add_menu_item(__('Delete Tenant (with Cleanup)'), function() {
			let selected_docs = listview.get_checked_items();
			if (selected_docs.length === 0) {
				frappe.msgprint(__('Please select at least one tenant to delete'));
				return;
			}

			let warning_message = __('Are you sure you want to delete {0} tenant(s)? This will also delete the site folder, database, and all related subscriptions. This action cannot be undone.', [selected_docs.length]);

			frappe.confirm(
				warning_message,
				function() {
					selected_docs.forEach(function(doc) {
						frappe.model.delete_doc('SaaS Tenant', doc.name, function() {
							frappe.msgprint(__('Tenant {0} deleted successfully with cleanup', [doc.name]));
							listview.refresh();
						});
					});
				}
			);
		}, true);
	}
};
