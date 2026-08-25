frappe.ui.form.on("SaaS Tenant", {
	refresh(frm) {
		localize_tenant_labels(frm);
		localize_tenant_select_options(frm);
	},
});

function is_arabic_language() {
	const lang = (frappe.boot?.lang || frappe.user?.language || "").toLowerCase();
	return lang.startsWith("ar");
}

function t(en, ar) {
	return is_arabic_language() ? ar : en;
}

function localize_tenant_labels(frm) {
	const labels = {
		tenant_name: t("Tenant Name", "اسم المستأجر"),
		company_email: t("Company Email", "بريد الشركة"),
		subdomain: t("Subdomain", "النطاق الفرعي"),
		status: t("Status", "الحالة"),
		admin_username: t("Admin Username", "اسم مستخدم المدير"),
		admin_password: t("Admin Password", "كلمة مرور المدير"),
		site_url: t("Site URL", "رابط الموقع"),
		deployment_section: t("Deployment", "النشر"),
		deployment_mode: t("Deployment Mode", "وضع النشر"),
		site_name: t("Site Name", "اسم الموقع"),
		site_folder: t("Site Folder", "مجلد الموقع"),
		port_number: t("Port", "المنفذ"),
		domain: t("Domain", "النطاق"),
		access_url: t("Access URL", "رابط الوصول"),
		service_status: t("Service Status", "حالة الخدمة"),
		health_status: t("Health Status", "حالة الصحة"),
		last_health_check: t("Last Health Check", "آخر فحص صحة"),
		active_subscription: t("Active Subscription", "الاشتراك النشط"),
		provisioned_on: t("Provisioned On", "تاريخ التجهيز"),
		provisioning_progress: t("Provisioning Progress", "تقدم التجهيز"),
		credentials_section: t("Site Credentials", "بيانات الموقع"),
		branding_section: t("Branding", "العلامة التجارية"),
		brand_name: t("Brand Name", "اسم العلامة التجارية"),
		custom_domain: t("Custom Domain", "نطاق مخصص"),
		notes: t("Notes", "ملاحظات"),
	};

	Object.entries(labels).forEach(([fieldname, label]) => frm.set_df_property(fieldname, "label", label));

	frm.set_df_property("tenant_name", "description", t("Unique name used to identify the tenant.", "اسم فريد يستخدم لتعريف المستأجر."));
	frm.set_df_property("company_email", "description", t("Primary email address for tenant communication.", "البريد الإلكتروني الأساسي للتواصل مع المستأجر."));
	frm.set_df_property("subdomain", "description", t("Tenant subdomain slug.", "الاسم المختصر للنطاق الفرعي للمستأجر."));
	frm.set_df_property("site_name", "description", t("Internal site database name.", "اسم قاعدة بيانات الموقع الداخلية."));
	frm.set_df_property("site_folder", "description", t("Bench site folder name.", "اسم مجلد الموقع داخل bench."));
	frm.set_df_property("domain", "description", t("Tenant domain or mapped hostname.", "نطاق المستأجر أو اسم المضيف المعيّن."));
	frm.set_df_property("access_url", "description", t("Public access URL for the tenant.", "رابط الوصول العام للمستأجر."));
	frm.set_df_property("brand_name", "description", t("Brand shown in the tenant UI.", "العلامة المعروضة في واجهة المستأجر."));
	frm.set_df_property("custom_domain", "description", t("Optional custom domain assigned to the tenant.", "نطاق مخصص اختياري للمستأجر."));
	frm.set_df_property("notes", "description", t("Internal notes for operations or support.", "ملاحظات داخلية للتشغيل أو الدعم."));
}

function localize_tenant_select_options(frm) {
	localize_select_options(frm, "status", {
		Draft: t("Draft", "مسودة"),
		Provisioning: t("Provisioning", "جارٍ التجهيز"),
		Active: t("Active", "نشط"),
		Suspended: t("Suspended", "موقوف"),
		Archived: t("Archived", "مؤرشف"),
	});
	localize_select_options(frm, "deployment_mode", {
		Port: t("Port", "البورت"),
		Subdomain: t("Subdomain", "النطاق الفرعي"),
	});
	localize_select_options(frm, "site_distribution_method", {
		Port: t("Port", "البورت"),
		Subdomain: t("Subdomain", "النطاق الفرعي"),
	});
	localize_select_options(frm, "service_status", {
		Unknown: t("Unknown", "غير معروف"),
		Stopped: t("Stopped", "متوقف"),
		Starting: t("Starting", "جارٍ التشغيل"),
		Running: t("Running", "يعمل"),
		Failed: t("Failed", "فشل"),
	});
	localize_select_options(frm, "health_status", {
		Unknown: t("Unknown", "غير معروف"),
		Healthy: t("Healthy", "سليم"),
		Unhealthy: t("Unhealthy", "غير سليم"),
	});
}

function localize_select_options(frm, fieldname, translations) {
	const field = frm.get_field(fieldname);
	if (!field || !field.$input || !field.$input.length) {
		return;
	}

	field.$input.find("option").each(function () {
		const value = (this.value || this.textContent || "").trim();
		if (translations[value]) {
			this.textContent = translations[value];
		}
	});
}
