app_name = "erpgenex_saas"
app_title = "ERPGenex SaaS"
app_publisher = "ErpGenEx"
app_description = "Enterprise SaaS platform for ERPGenex"
app_email = "dev@erpgenex.com"
app_license = "mit"

# Apps
# ------------------

required_apps = ["frappe"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "erpgenex_saas",
# 		"logo": "/assets/erpgenex_saas/logo.png",
# 		"title": "ERPGenex SaaS",
# 		"route": "/erpgenex_saas",
# 		"has_permission": "erpgenex_saas.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# Portal assets are website-only (web_include_*). Do NOT load on Desk — breaks navbar/layout.
app_include_css = []
app_include_js = []

web_include_css = ["/assets/erpgenex_saas/css/erpgenex_saas.css"]
web_include_js = ["/assets/erpgenex_saas/js/erpgenex_saas.js"]

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "erpgenex_saas/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "erpgenex_saas/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
jinja = {
	"methods": "erpgenex_saas.api.website",
}

# Installation
# ------------

before_install = "erpgenex_saas.install.before_install"
after_install = "erpgenex_saas.install.after_install"
after_migrate = "erpgenex_saas.install.after_migrate"

# Uninstallation
# ------------

# before_uninstall = "erpgenex_saas.uninstall.before_uninstall"
# after_uninstall = "erpgenex_saas.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "erpgenex_saas.utils.before_app_install"
# after_app_install = "erpgenex_saas.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "erpgenex_saas.utils.before_app_uninstall"
# after_app_uninstall = "erpgenex_saas.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

notification_config = "erpgenex_saas.notifications.get_notification_config"

# Permissions
# -----------
permission_query_conditions = {
	"SaaS Tenant": "erpgenex_saas.permissions.get_tenant_permission_query",
	"SaaS Subscription": "erpgenex_saas.permissions.get_subscription_permission_query",
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"SaaS Plan": {
		"validate": "erpgenex_saas.events.validate_plan",
	},
	"SaaS Tenant": {
		"validate": "erpgenex_saas.events.validate_tenant",
		"on_update": "erpgenex_saas.events.sync_tenant_status",
	},
	"SaaS Subscription": {
		"validate": "erpgenex_saas.events.validate_subscription",
		"on_update": "erpgenex_saas.events.on_subscription_update",
	},
	"Provisioning Request": {
		"validate": "erpgenex_saas.events.validate_request",
	},
}

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"erpgenex_saas.tasks.process_due_provisioning_requests",
		"erpgenex_saas.tasks.expire_trials_and_grace_periods",
	],
	"daily": [
		"erpgenex_saas.tasks.generate_usage_snapshots",
		"erpgenex_saas.tasks.sync_marketplace_catalog",
	],
}

# Testing
# -------

# before_tests = "erpgenex_saas.install.before_tests"

# Overriding Methods
# ------------------------------
#
website_route_rules = [
	{"from_route": "/saas", "to_route": "saas"},
	{"from_route": "/saas/pricing", "to_route": "saas/pricing"},
	{"from_route": "/saas/register", "to_route": "saas/register"},
	{"from_route": "/saas/checkout", "to_route": "saas/checkout"},
	{"from_route": "/saas/provisioning", "to_route": "saas/provisioning"},
	{"from_route": "/saas/success", "to_route": "saas/success"},
	{"from_route": "/saas/dashboard", "to_route": "saas/dashboard"},
	{"from_route": "/saas/applications", "to_route": "saas/applications"},
	{"from_route": "/saas/features", "to_route": "saas/features"},
	{"from_route": "/saas/contact", "to_route": "saas/contact"},
	{"from_route": "/saas/faq", "to_route": "saas/faq"},
	{"from_route": "/saas/about", "to_route": "saas/about"},
	{"from_route": "/saas/docs", "to_route": "saas/docs"},
]

update_website_context = ["erpgenex_saas.api.website.update_website_context"]

role_home_page = {
	"SaaS Customer": "saas/dashboard",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "erpgenex_saas.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
before_request = ["erpgenex_saas.request_context.before_request"]
after_request = ["erpgenex_saas.request_context.after_request"]

# Job Events
# ----------
# before_job = ["erpgenex_saas.utils.before_job"]
# after_job = ["erpgenex_saas.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

auth_hooks = ["erpgenex_saas.auth.validate"]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

