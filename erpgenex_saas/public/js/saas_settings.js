frappe.ui.form.on("SaaS Settings", {
	refresh(frm) {
		apply_paypal_labels(frm);
		localize_select_fields(frm);
		render_paypal_cards(frm);
		apply_paypal_visibility(frm);
	},
	paypal_enabled(frm) {
		apply_paypal_visibility(frm);
	},
	paypal_environment(frm) {
		apply_paypal_visibility(frm);
	},
});

function apply_paypal_visibility(frm) {
	const enabled = !!frm.doc.paypal_enabled;
	const environment = normalize_paypal_environment(frm.doc.paypal_environment);
	const sandbox = environment === "Sandbox";
	const liveFields = ["paypal_business_email", "paypal_merchant_id"];
	const sandboxFields = ["paypal_sandbox_business_email", "paypal_sandbox_merchant_id"];

	[...liveFields, ...sandboxFields].forEach((fieldname) => {
		frm.toggle_display(fieldname, true);
	});
	frm.toggle_display("paypal_mode_cards", true);
	frm.toggle_enable("paypal_business_email", enabled);
	frm.toggle_enable("paypal_merchant_id", enabled);
	frm.toggle_enable("paypal_sandbox_business_email", enabled);
	frm.toggle_enable("paypal_sandbox_merchant_id", enabled);

	frm.toggle_reqd("paypal_business_email", enabled && !sandbox);
	frm.toggle_reqd("paypal_sandbox_business_email", enabled && sandbox);
	frm.toggle_reqd("paypal_merchant_id", false);
	frm.toggle_reqd("paypal_sandbox_merchant_id", false);

	set_paypal_field_meta(frm, sandbox);
	update_paypal_card_state(frm, enabled, environment);
}

function is_arabic_language() {
	const lang = (frappe.boot?.lang || frappe.user?.language || "").toLowerCase();
	return lang.startsWith("ar");
}

function t(en, ar) {
	return is_arabic_language() ? ar : en;
}

function apply_paypal_labels(frm) {
	const labels = {
		platform_section: t("Platform", "المنصة"),
		github_section: t("GitHub Distribution", "توزيع GitHub"),
		deployment_section: t("Deployment Settings", "إعدادات النشر"),
		legacy_section: t("Legacy (Auto-synced)", "قديم (متزامن تلقائيًا)"),
		pricing_section: t("Pricing", "التسعير"),
		payment_section: t("Payments", "المدفوعات"),
		security_section: t("Security", "الأمان"),
		platform_domain: t("Platform Domain", "نطاق المنصة"),
		database_password: t("Database Password", "كلمة مرور قاعدة البيانات"),
		mariadb_root_password: t("MariaDB Root Password", "كلمة مرور MariaDB الرئيسية"),
		github_organization: t("GitHub Organization", "مؤسسة GitHub"),
		github_access_token: t("GitHub Access Token", "رمز وصول GitHub"),
		default_download_expiry_hours: t("Default Download Expiry Hours", "ساعات انتهاء التحميل الافتراضية"),
		require_private_repositories: t("Require Private Repositories", "اشتراط المستودعات الخاصة"),
		default_trial_days: t("Default Trial Days", "أيام الفترة التجريبية الافتراضية"),
		default_grace_period_days: t("Default Grace Period Days", "أيام فترة السماح الافتراضية"),
		deployment_mode: t("Deployment Mode", "وضع النشر"),
		start_port: t("Start Port", "منفذ البداية"),
		end_port: t("End Port", "منفذ النهاية"),
		server_host: t("Server Host", "مضيف الخادم"),
		use_https: t("Use HTTPS", "استخدم HTTPS"),
		root_domain: t("Root Domain", "النطاق الجذري"),
		subdomain_pattern: t("Subdomain Pattern", "نمط النطاق الفرعي"),
		site_distribution_method: t("Site Distribution Method", "طريقة توزيع المواقع"),
		server_ip: t("Server IP", "عنوان IP للخادم"),
		server_port: t("Server Port", "منفذ الخادم"),
		base_port: t("Base Port", "المنفذ الأساسي"),
		max_port: t("Max Port", "أقصى منفذ"),
		port_increment: t("Port Increment", "تزايد المنفذ"),
		extra_user_price: t("Extra User Price", "سعر المستخدم الإضافي"),
		extra_storage_price_per_gb: t("Extra Storage Price Per GB", "سعر التخزين الإضافي لكل جيجابايت"),
		paypal_enabled: t("Enable PayPal Payments", "تفعيل مدفوعات باي بال"),
		paypal_environment: t("PayPal Mode", "وضع باي بال"),
		paypal_business_email: t("Live PayPal Business Email", "بريد باي بال للإنتاج"),
		paypal_sandbox_business_email: t("Sandbox PayPal Business Email", "بريد باي بال للاختبار"),
		paypal_merchant_id: t("Live PayPal Merchant ID", "معرّف التاجر للإنتاج"),
		paypal_sandbox_merchant_id: t("Sandbox PayPal Merchant ID", "معرّف التاجر للاختبار"),
		stripe_ready: t("Stripe Ready", "جاهز لـ Stripe"),
		moyasar_ready: t("Moyasar Ready", "جاهز لـ Moyasar"),
		api_rate_limit_per_minute: t("API Rate Limit Per Minute", "حد معدل طلبات API في الدقيقة"),
		enable_audit_log: t("Enable Audit Log", "تفعيل سجل التدقيق"),
	};

	Object.entries(labels).forEach(([fieldname, label]) => {
		frm.set_df_property(fieldname, "label", label);
	});

	frm.set_df_property(
		"paypal_enabled",
		"description",
		t("Turn this on to let customers pay through PayPal.", "فعّل هذا الخيار للسماح للعملاء بالدفع عبر باي بال.")
	);
	frm.set_df_property(
		"paypal_environment",
		"description",
		t("Choose which PayPal account and checkout URL should be used.", "اختر حساب باي بال ورابط الدفع الذي يجب استخدامه.")
	);
	frm.set_df_property("paypal_business_email", "description", t("Used only when PayPal Mode is Live.", "يُستخدم فقط عندما يكون وضع باي بال على الإنتاج."));
	frm.set_df_property(
		"paypal_sandbox_business_email",
		"description",
		t("Used only when PayPal Mode is Sandbox.", "يُستخدم فقط عندما يكون وضع باي بال على الاختبار.")
	);
	frm.set_df_property("paypal_merchant_id", "description", t("Optional merchant ID for Live mode.", "معرّف تاجر اختياري لوضع الإنتاج."));
	frm.set_df_property(
		"paypal_sandbox_merchant_id",
		"description",
		t("Optional merchant ID for Sandbox mode.", "معرّف تاجر اختياري لوضع الاختبار.")
	);
	frm.set_df_property(
		"platform_domain",
		"description",
		t("Legacy alias for Root Domain in Subdomain mode", "اسم بديل قديم للنطاق الجذري في وضع النطاق الفرعي")
	);
	frm.set_df_property("database_password", "description", t("Password used by the site database connection.", "كلمة المرور المستخدمة لاتصال قاعدة بيانات الموقع."));
	frm.set_df_property("mariadb_root_password", "description", t("MariaDB root password used by provisioning tasks.", "كلمة مرور MariaDB الرئيسية المستخدمة في مهام الإنشاء."));
	frm.set_df_property("github_organization", "description", t("GitHub organization that owns marketplace repositories.", "مؤسسة GitHub المالكة للمستودعات."));
	frm.set_df_property("github_access_token", "description", t("Required for private repository downloads.", "مطلوب لتنزيل المستودعات الخاصة."));
	frm.set_df_property("default_download_expiry_hours", "description", t("How long download links stay valid.", "مدة صلاحية روابط التحميل."));
	frm.set_df_property("require_private_repositories", "description", t("Enable this if private repositories should always be used.", "فعّل هذا الخيار إذا كان يجب استخدام المستودعات الخاصة دائمًا."));
	frm.set_df_property("default_trial_days", "description", t("Number of trial days for new tenants.", "عدد أيام التجربة للمستأجرين الجدد."));
	frm.set_df_property("default_grace_period_days", "description", t("Grace period after trial expiry.", "فترة السماح بعد انتهاء التجربة."));
	frm.set_df_property("deployment_mode", "description", t("Choose Port for port-based sites or Subdomain for subdomain-based sites.", "اختر المنفذ للمواقع المعتمدة على البورت أو النطاق الفرعي للمواقع المعتمدة على النطاق."));
	frm.set_df_property("start_port", "description", t("Lowest port in the allocation range.", "أقل منفذ في نطاق التخصيص."));
	frm.set_df_property("end_port", "description", t("Highest port in the allocation range.", "أعلى منفذ في نطاق التخصيص."));
	frm.set_df_property("server_host", "description", t("Host name or IP used for port-based deployment.", "اسم المضيف أو عنوان IP المستخدم في النشر المعتمد على البورت."));
	frm.set_df_property("use_https", "description", t("Enable HTTPS for port-based deployment.", "فعّل HTTPS للنشر المعتمد على البورت."));
	frm.set_df_property("root_domain", "description", t("Base domain used for subdomain routing.", "النطاق الأساسي المستخدم لتوجيه النطاقات الفرعية."));
	frm.set_df_property("subdomain_pattern", "description", t("Pattern used to build tenant subdomains.", "النمط المستخدم لإنشاء النطاقات الفرعية للمستأجرين."));
	frm.set_df_property("extra_user_price", "description", t("Price for each additional user.", "سعر كل مستخدم إضافي."));
	frm.set_df_property("extra_storage_price_per_gb", "description", t("Price for each additional GB of storage.", "سعر كل جيجابايت إضافي من التخزين."));
	frm.set_df_property("api_rate_limit_per_minute", "description", t("Maximum API calls allowed per minute.", "الحد الأقصى لطلبات API المسموح بها في الدقيقة."));
	frm.set_df_property("enable_audit_log", "description", t("Store security and lifecycle events in the audit log.", "حفظ أحداث الأمان ودورة الحياة في سجل التدقيق."));
}

function localize_select_fields(frm) {
	localize_select_options(frm, "deployment_mode", {
		Port: t("Port", "البورت"),
		Subdomain: t("Subdomain", "النطاق الفرعي"),
	});
	localize_select_options(frm, "site_distribution_method", {
		Port: t("Port", "البورت"),
		Subdomain: t("Subdomain", "النطاق الفرعي"),
	});
	localize_select_options(frm, "paypal_environment", {
		Live: t("Live", "مباشر"),
		Sandbox: t("Sandbox", "بيئة اختبار"),
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

function normalize_paypal_environment(value) {
	const normalized = (value || "Live").trim().toLowerCase();
	return normalized === "sandbox" ? "Sandbox" : "Live";
}

function set_paypal_field_meta(frm, sandbox) {
	frm.set_df_property("paypal_business_email", "description", t("Used only when PayPal Mode is Live.", "يُستخدم فقط عندما يكون وضع باي بال على الإنتاج."));
	frm.set_df_property("paypal_sandbox_business_email", "description", t("Used only when PayPal Mode is Sandbox.", "يُستخدم فقط عندما يكون وضع باي بال على الاختبار."));
	frm.set_df_property("paypal_merchant_id", "description", t("Optional merchant ID for Live mode.", "معرّف تاجر اختياري لوضع الإنتاج."));
	frm.set_df_property("paypal_sandbox_merchant_id", "description", t("Optional merchant ID for Sandbox mode.", "معرّف تاجر اختياري لوضع الاختبار."));
}

function render_paypal_cards(frm) {
	const cardsField = frm.fields_dict.paypal_mode_cards;
	if (!cardsField || !cardsField.$wrapper) {
		return;
	}

	cardsField.$wrapper.html(`
		<div class="egx-paypal-cards" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;margin-top:10px;">
			<div class="egx-paypal-card egx-paypal-card--live" data-paypal-card="live" style="border:1px solid #dbe2ea;border-radius:16px;background:#ffffff;box-shadow:0 1px 2px rgba(15,23,42,0.05);overflow:hidden;">
				<div class="egx-paypal-card__header" style="display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 16px;background:linear-gradient(135deg,#eff6ff,#ffffff);border-bottom:1px solid #e2e8f0;">
					<div>
						<div style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#2563eb;">${t("Live", "مباشر")}</div>
						<div style="font-size:15px;font-weight:600;color:#0f172a;">${t("Production credentials", "بيانات الإنتاج")}</div>
					</div>
					<span class="egx-paypal-card__badge" data-paypal-badge="live" style="display:inline-flex;align-items:center;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:700;background:#cbd5e1;color:#334155;">${t("Inactive", "غير نشطة")}</span>
				</div>
				<div class="egx-paypal-card__body" data-paypal-card-body="live" style="padding:16px;"></div>
			</div>
			<div class="egx-paypal-card egx-paypal-card--sandbox" data-paypal-card="sandbox" style="border:1px solid #dbe2ea;border-radius:16px;background:#ffffff;box-shadow:0 1px 2px rgba(15,23,42,0.05);overflow:hidden;">
				<div class="egx-paypal-card__header" style="display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 16px;background:linear-gradient(135deg,#fff7ed,#ffffff);border-bottom:1px solid #e2e8f0;">
					<div>
						<div style="font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.08em;color:#ea580c;">${t("Sandbox", "بيئة اختبار")}</div>
						<div style="font-size:15px;font-weight:600;color:#0f172a;">${t("Test credentials", "بيانات الاختبار")}</div>
					</div>
					<span class="egx-paypal-card__badge" data-paypal-badge="sandbox" style="display:inline-flex;align-items:center;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:700;background:#cbd5e1;color:#334155;">${t("Inactive", "غير نشطة")}</span>
				</div>
				<div class="egx-paypal-card__body" data-paypal-card-body="sandbox" style="padding:16px;"></div>
			</div>
		</div>
		<div class="egx-paypal-summary" style="margin-top:12px;font-size:12px;color:#64748b;line-height:1.5;"></div>
	`);

	move_paypal_fields(frm, "live", ["paypal_business_email", "paypal_merchant_id"]);
	move_paypal_fields(frm, "sandbox", ["paypal_sandbox_business_email", "paypal_sandbox_merchant_id"]);
}

function move_paypal_fields(frm, cardName, fieldnames) {
	const body = frm.fields_dict.paypal_mode_cards?.$wrapper?.find(`[data-paypal-card-body="${cardName}"]`);
	if (!body || !body.length) {
		return;
	}

	fieldnames.forEach((fieldname) => {
		const field = frm.get_field(fieldname);
		if (field && field.$wrapper && field.$wrapper.length) {
			field.$wrapper.appendTo(body);
		}
	});
}

function update_paypal_card_state(frm, enabled, environment) {
	const sandbox = environment === "Sandbox";
	const liveActive = enabled && !sandbox;
	const sandboxActive = enabled && sandbox;
	const liveCard = frm.fields_dict.paypal_mode_cards?.$wrapper?.find('[data-paypal-card="live"]');
	const sandboxCard = frm.fields_dict.paypal_mode_cards?.$wrapper?.find('[data-paypal-card="sandbox"]');
	const summary = frm.fields_dict.paypal_mode_cards?.$wrapper?.find(".egx-paypal-summary");
	const liveBadge = frm.fields_dict.paypal_mode_cards?.$wrapper?.find('[data-paypal-badge="live"]');
	const sandboxBadge = frm.fields_dict.paypal_mode_cards?.$wrapper?.find('[data-paypal-badge="sandbox"]');

	set_card_style(liveCard, liveActive, enabled);
	set_card_style(sandboxCard, sandboxActive, enabled);
	set_badge_state(liveBadge, liveActive, enabled ? "Live" : "Off");
	set_badge_state(sandboxBadge, sandboxActive, enabled ? "Sandbox" : "Off");

	if (summary && summary.length) {
		summary.html(
			!enabled
				? t("PayPal is disabled. Turn it on to edit the production and sandbox cards.", "تم تعطيل PayPal. فعّله لتعديل بطاقتي الإنتاج والاختبار.")
				: sandbox
					? t("The sandbox card is active. Production credentials remain saved but inactive.", "بطاقة بيئة الاختبار نشطة. بيانات الإنتاج محفوظة لكنها غير فعالة.")
					: t("The production card is active. Sandbox credentials remain saved but inactive.", "بطاقة الإنتاج نشطة. بيانات الاختبار محفوظة لكنها غير فعالة.")
		);
	}
}

function set_card_style(card, active, enabled) {
	if (!card || !card.length) {
		return;
	}

	const isSandbox = card.data("paypalCard") === "sandbox";
	const border = !enabled
		? "#e2e8f0"
		: active
			? isSandbox
				? "#fdba74"
				: "#93c5fd"
			: "#e2e8f0";
	const background = !enabled
		? "#f8fafc"
		: active
			? isSandbox
				? "linear-gradient(135deg,#fff7ed,#ffffff)"
				: "linear-gradient(135deg,#eff6ff,#ffffff)"
			: "#ffffff";
	const opacity = enabled ? "1" : "0.72";
	const shadow = active ? "0 8px 24px rgba(15,23,42,0.12)" : "0 1px 2px rgba(15,23,42,0.05)";

	card.attr(
		"style",
		`border:1px solid ${border};border-radius:16px;background:${background};box-shadow:${shadow};overflow:hidden;opacity:${opacity};transition:all .2s ease;`
	);
}

function set_badge_state(badge, active, label) {
	if (!badge || !badge.length) {
		return;
	}

	const color = active ? "#ffffff" : "#334155";
	const background = active ? (label === "Sandbox" ? "#ea580c" : "#2563eb") : "#cbd5e1";
	badge.text(active ? t("Active", "نشطة") : t("Inactive", "غير نشطة"));
	badge.attr(
		"style",
		`display:inline-flex;align-items:center;border-radius:999px;padding:4px 10px;font-size:12px;font-weight:700;background:${background};color:${color};`
	);
}

function render_paypal_notice(frm, enabled, environment) {
	const noticeField = frm.fields_dict.paypal_mode_cards;
	if (!noticeField || !noticeField.$wrapper) {
		return;
	}

	const sandbox = environment === "Sandbox";
	const url = sandbox ? "https://www.sandbox.paypal.com/cgi-bin/webscr" : "https://www.paypal.com/cgi-bin/webscr";
	const summary = noticeField.$wrapper.find(".egx-paypal-summary");
	if (summary && summary.length) {
		summary.html(`${t("Checkout URL", "رابط الدفع")}: <code>${url}</code>`);
	}
}
