window.erpgenexSaas = window.erpgenexSaas || {};

(function () {
	"use strict";

	const STORAGE_KEY = "egx_saas_cart";
	const STEPS = [
		"Creating Database",
		"Installing Apps",
		"Configuring SSL",
		"Creating Workspace",
		"Creating Users",
		"Preparing Dashboard",
	];

	function qs(sel, root) {
		return (root || document).querySelector(sel);
	}

	function qsa(sel, root) {
		return Array.from((root || document).querySelectorAll(sel));
	}

	function formatMoney(n) {
		return "$" + Number(n || 0).toFixed(0);
	}

	function escapeHtml(value) {
		return String(value == null ? "" : value).replace(/[&<>"']/g, (ch) => {
			const map = {
				"&": "&amp;",
				"<": "&lt;",
				">": "&gt;",
				'"': "&quot;",
				"'": "&#39;",
			};
			return map[ch] || ch;
		});
	}

	function getCart() {
		try {
			return JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
		} catch {
			return {};
		}
	}

	function setCart(cart) {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
	}

	function getQueryParam(name) {
		return new URLSearchParams(window.location.search).get(name);
	}

	function getRuntimeConfig() {
		return window.erpgenexSaasConfig || {};
	}

	function getPortalElement() {
		return qs(".egx-portal");
	}

	function getPortalDataset() {
		const portal = getPortalElement();
		return portal ? portal.dataset : {};
	}

	function getPaypalConfig() {
		const runtime = getRuntimeConfig();
		const dataset = getPortalDataset();
		const businessEmail =
			runtime.paypal_business_email ||
			runtime.paypalBusinessEmail ||
			dataset.paypalBusinessEmail ||
			"";
		const actionUrl =
			runtime.paypal_action_url ||
			runtime.paypal_url ||
			dataset.paypalActionUrl ||
			"https://www.paypal.com/cgi-bin/webscr";
		const runtimeEnabled = runtime.paypal_enabled;
		const enabledValue = dataset.paypalEnabled;
		const enabled =
			runtimeEnabled != null
				? Boolean(runtimeEnabled)
				: enabledValue != null
					? enabledValue === "1" || enabledValue === "true"
					: false;

		return {
			enabled,
			businessEmail,
			actionUrl,
		};
	}

	function getCurrentQueryObject() {
		return Object.fromEntries(new URLSearchParams(window.location.search).entries());
	}

	function buildUrl(path, params) {
		const url = new URL(path, window.location.origin);
		const query = params || {};
		Object.keys(query).forEach((key) => {
			const value = query[key];
			if (value !== undefined && value !== null && String(value) !== "") {
				url.searchParams.set(key, String(value));
			}
		});
		const lang = getQueryParam("lang");
		if (lang && !url.searchParams.has("lang")) {
			url.searchParams.set("lang", lang);
		}
		return url.toString();
	}

	function redirectToPayPal(options) {
		const paypal = getPaypalConfig();
		if (!paypal.enabled) {
			throw new Error("PayPal payments are disabled");
		}
		if (!paypal.businessEmail) {
			throw new Error("PayPal business email is not configured");
		}

		const form = document.createElement("form");
		form.method = "POST";
		form.action = options.actionUrl || paypal.actionUrl;
		form.target = "_top";
		form.style.display = "none";

		const fields = {
			cmd: "_xclick",
			business: paypal.businessEmail,
			currency_code: options.currencyCode || "USD",
			item_name: options.itemName || "ERPGenEx SaaS payment",
			item_number: options.invoice || options.reference || "",
			amount: Number(options.amount || 0).toFixed(2),
			return: options.returnUrl || window.location.href,
			cancel_return: options.cancelUrl || window.location.href,
			custom: options.custom ? JSON.stringify(options.custom) : "",
		};

		Object.entries(fields).forEach(([key, value]) => {
			if (value === "") return;
			const input = document.createElement("input");
			input.type = "hidden";
			input.name = key;
			input.value = value;
			form.appendChild(input);
		});

		if (options.notifyUrl) {
			const notify = document.createElement("input");
			notify.type = "hidden";
			notify.name = "notify_url";
			notify.value = options.notifyUrl;
			form.appendChild(notify);
		}

		document.body.appendChild(form);
		form.submit();
	}

	function getRootDomain() {
		return getRuntimeConfig().root_domain || window.location.hostname || "localhost";
	}

	function getScheme() {
		return window.location.protocol === "https:" ? "https" : "http";
	}

	/* ── Nav ── */
	function initNav() {
		const nav = qs(".egx-nav");
		if (!nav) return;

		window.addEventListener("scroll", () => {
			nav.classList.toggle("is-scrolled", window.scrollY > 12);
		});

		const path = window.location.pathname;
		qsa(".egx-nav__link").forEach((link) => {
			if (link.getAttribute("href") === path) link.classList.add("is-active");
		});

		const toggle = qs(".egx-nav__toggle");
		const links = qs(".egx-nav__links");
		if (toggle && links) {
			toggle.addEventListener("click", () => links.classList.toggle("is-open"));
		}
	}

	/* ── Counters ── */
	function initCounters() {
		qsa("[data-egx-counter]").forEach((el) => {
			const target = parseInt(el.dataset.egxCounter, 10) || 0;
			const suffix = el.dataset.egxSuffix || "";
			let current = 0;
			const step = Math.max(1, Math.floor(target / 40));
			const timer = setInterval(() => {
				current += step;
				if (current >= target) {
					current = target;
					clearInterval(timer);
				}
				el.textContent = current.toLocaleString() + suffix;
			}, 30);
		});
	}

	/* ── Pricing toggle ── */
	function initPricing() {
		const toggle = qs(".egx-billing-toggle");
		if (!toggle) return;

		const portal = qs(".egx-portal");
		const labelMonth = (portal && portal.dataset.i18nMonth) || "/ month";
		const labelYear = (portal && portal.dataset.i18nYear) || "/ year";

		const buttons = qsa(".egx-billing-toggle__btn", toggle);
		const cards = qsa(".egx-price-card");

		function setBilling(mode) {
			buttons.forEach((b) => b.classList.toggle("is-active", b.dataset.billing === mode));
			cards.forEach((card) => {
				const monthly = parseFloat(card.dataset.monthly || 0);
				const yearly = parseFloat(card.dataset.yearly || monthly * 10);
				const amount = mode === "yearly" ? yearly : monthly;
				const period = mode === "yearly" ? labelYear : labelMonth;
				const amountEl = qs(".egx-price-card__amount", card);
				const periodEl = qs(".egx-price-card__period", card);
				if (amountEl) amountEl.textContent = formatMoney(amount);
				if (periodEl) periodEl.textContent = period;
			});
		}

		buttons.forEach((btn) => {
			btn.addEventListener("click", () => setBilling(btn.dataset.billing));
		});
		setBilling("monthly");
	}

	/* ── Marketplace ── */
	function initMarketplace() {
		const grid = qs("#egx-app-grid");
		if (!grid) return;

		const cart = getCart();
		let total = 0;

		function updateTotal() {
			total = 0;
			const portal = qs(".egx-portal");
			const moLabel = (portal && portal.dataset.i18nMo) || " / mo";
			qsa(".egx-app-card", grid).forEach((card) => {
				const slug = card.dataset.slug;
				const price = parseFloat(card.dataset.price || 0);
				const toggle = qs('input[type="checkbox"]', card);
				if (toggle && toggle.checked) {
					total += price;
					cart[slug] = price;
				} else {
					delete cart[slug];
				}
			});
			setCart(cart);
			const totalEl = qs("#egx-marketplace-total");
			if (totalEl) totalEl.textContent = formatMoney(total) + moLabel;
		}

		qsa(".egx-app-card", grid).forEach((card) => {
			const slug = card.dataset.slug;
			const toggle = qs('input[type="checkbox"]', card);
			if (toggle && cart[slug]) {
				toggle.checked = true;
			}
			if (toggle) toggle.addEventListener("change", updateTotal);
			const installBtn = qs(".egx-app-install", card);
			if (installBtn) {
				installBtn.addEventListener("click", () => {
					if (toggle) {
						toggle.checked = !toggle.checked;
						updateTotal();
					}
				});
			}
		});
		updateTotal();
	}

	/* ── Checkout ── */
	function initCheckout() {
		const form = qs("#egx-checkout-form");
		if (!form || !window.frappe || !frappe.call) return;
		const paypalBtn = qs(".egx-paypal-btn");

		const plan = getQueryParam("plan") || "";
		const planSelect = qs('[name="plan"]', form);
		if (plan && planSelect) {
			for (const opt of planSelect.options) {
				if (opt.value === plan || opt.textContent.includes(plan)) {
					planSelect.value = opt.value;
					break;
				}
			}
		}

		const summaryPlan = qs("#egx-summary-plan");
		const summaryTotal = qs("#egx-summary-total");
		const summaryExtraUsers = qs("#egx-summary-extra-users");
		const summaryExtraStorage = qs("#egx-summary-extra-storage");
		const appsTotal = Object.values(getCart()).reduce((a, b) => a + b, 0);
		const portal = qs(".egx-portal");
		const extraUserPrice = parseFloat(portal?.dataset.extraUserPrice || 0);
		const extraStoragePrice = parseFloat(portal?.dataset.extraStoragePrice || 0);
		const extraUsersInput = qs('[name="extra_users"]', form);
		const extraStorageInput = qs('[name="extra_storage_gb"]', form);
		const checkoutQuery = new URLSearchParams(window.location.search);

		if (checkoutQuery.get("paypal_cancel")) {
			const box = qs("#egx-checkout-result");
			if (box) {
				box.innerHTML =
					'<div class="egx-card" style="border-color:var(--egx-warning);color:var(--egx-warning)">Payment was cancelled before completion. You can try again whenever you are ready.</div>';
			}
			window.history.replaceState({}, "", buildUrl("/saas/checkout", {
				plan: plan || "",
			}));
		}

		function refreshSummary() {
			const selected = planSelect && planSelect.selectedOptions[0];
			const base = selected ? parseFloat(selected.dataset.price || 0) : 0;
			const extraUsers = parseInt(extraUsersInput?.value || 0, 10) || 0;
			const extraStorage = parseFloat(extraStorageInput?.value || 0) || 0;
			const extraUsersTotal = extraUsers * extraUserPrice;
			const extraStorageTotal = extraStorage * extraStoragePrice;
			const total = base + appsTotal + extraUsersTotal + extraStorageTotal;
			if (summaryPlan) summaryPlan.textContent = selected ? selected.textContent : "—";
			if (summaryTotal) summaryTotal.textContent = formatMoney(total);
			if (summaryExtraUsers) summaryExtraUsers.textContent = `${extraUsers} × ${formatMoney(extraUsersTotal)}`;
			if (summaryExtraStorage) summaryExtraStorage.textContent = `${extraStorage} GB × ${formatMoney(extraStorageTotal)}`;
		}

		if (planSelect) planSelect.addEventListener("change", refreshSummary);
		if (extraUsersInput) extraUsersInput.addEventListener("input", refreshSummary);
		if (extraStorageInput) extraStorageInput.addEventListener("input", refreshSummary);
		refreshSummary();

		form.addEventListener("submit", function (event) {
			event.preventDefault();
			const data = Object.fromEntries(new FormData(form).entries());
			const btn = qs('[type="submit"]', form);
			if (btn) {
				btn.disabled = true;
				btn.textContent = "Processing…";
			}
			if (paypalBtn) paypalBtn.disabled = true;

			frappe.call({
				method: "erpgenex_saas.api.v1.guest_register",
				args: data,
				callback: function (response) {
					const result = response.message || {};
					if (result.invoice) {
						const selected = planSelect && planSelect.selectedOptions[0];
						const extraUsers = parseInt(extraUsersInput?.value || 0, 10) || 0;
						const extraStorage = parseFloat(extraStorageInput?.value || 0) || 0;
						const amount =
							parseFloat(selected?.dataset.price || 0) +
							appsTotal +
							(extraUsers * extraUserPrice) +
							(extraStorage * extraStoragePrice) || 49;
						const returnUrl = buildUrl("/saas/provisioning", {
							request: result.provisioning_request || "",
							tenant: result.tenant || "",
							invoice: result.invoice,
							amount: amount,
							paypal_return: 1,
						});
						const cancelUrl = buildUrl("/saas/checkout", {
							plan: data.plan || "",
							paypal_cancel: 1,
						});
						try {
							redirectToPayPal({
								invoice: result.invoice,
								amount: amount,
								itemName: `SaaS checkout for ${data.customer_name || "customer"}`,
								returnUrl,
								cancelUrl,
								custom: {
									flow: "checkout",
									request: result.provisioning_request || "",
									tenant: result.tenant || "",
									plan: data.plan || "",
									billing_cycle: data.billing_cycle || "",
									extra_users: extraUsers,
									extra_storage_gb: extraStorage,
								},
							});
						} catch (err) {
							const box = qs("#egx-checkout-result");
							if (box) {
								box.innerHTML =
									'<div class="egx-card" style="border-color:var(--egx-danger);color:var(--egx-danger)">' +
									escapeHtml(err.message || "Unable to open PayPal") +
									"</div>";
							}
							if (btn) {
								btn.disabled = false;
								btn.textContent = "Complete Secure Payment";
							}
							if (paypalBtn) paypalBtn.disabled = false;
						}
					} else {
						window.location.href = "/saas/dashboard";
					}
				},
				error: function (err) {
					const box = qs("#egx-checkout-result");
					if (box) {
						box.innerHTML =
							'<div class="egx-card" style="border-color:var(--egx-danger);color:var(--egx-danger)">' +
							(err.message || "Checkout failed") +
							"</div>";
					}
					if (btn) {
						btn.disabled = false;
						btn.textContent = "Complete Secure Payment";
					}
					if (paypalBtn) paypalBtn.disabled = false;
				},
			});
		});

		if (paypalBtn) {
			paypalBtn.addEventListener("click", () => {
				if (form.requestSubmit) {
					form.requestSubmit();
				} else {
					form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
				}
			});
		}
	}

	/* ── Provisioning ── */
	function initProvisioning() {
		const container = qs("#egx-provisioning");
		if (!container) return;

		const requestName = getQueryParam("request");
		const tenantName = getQueryParam("tenant");
		const progressBar = qs(".egx-progress__bar");
		const eta = qs("#egx-provisioning-eta");
		const steps = qsa(".egx-timeline__step");
		const details = document.createElement("div");

		let currentStep = 0;
		let pollTimer = null;
		let finalState = null;

		details.className = "egx-card egx-fade-in";
		details.style.marginTop = "1.25rem";
		details.innerHTML = `
			<h3 style="margin:0 0 0.75rem">Provisioning Details</h3>
			<p style="margin:0;color:var(--egx-text-muted)">Waiting for the provisioning worker to report status.</p>
		`;
		container.appendChild(details);

		function setStep(index) {
			steps.forEach((step, i) => {
				step.classList.toggle("is-done", i < index);
				step.classList.toggle("is-active", i === index);
			});
			const pct = Math.round(((index + 1) / STEPS.length) * 100);
			if (progressBar) progressBar.style.width = pct + "%";
			if (eta) eta.textContent = Math.max(1, STEPS.length - index) + " min remaining";
		}

		function stopPolling() {
			if (pollTimer) {
				clearInterval(pollTimer);
				pollTimer = null;
			}
		}

		function renderDetails(data) {
			if (!details) return;
			const status = data.status || data.request_status || "Unknown";
			const failed = Boolean(data.failed || status === "Failed");
			const summary =
				data.error_message ||
				data.message ||
				data.request_last_message ||
				"Provisioning is still running.";
			const errorDetails =
				data.error_details ||
				data.request_last_message ||
				data.request_execution_log ||
				"";
			const traceback = data.traceback || "";
			const stageLogs = Array.isArray(data.stage_logs) ? data.stage_logs : [];
			const progressPct = Number((data.progress && data.progress.progress) || 0);

			if (progressBar && progressPct > 0) {
				progressBar.style.width = Math.min(100, progressPct) + "%";
			}

			const statusChipClass = failed
				? "egx-status--pending"
				: status === "Completed" || data.completed
					? "egx-status--active"
					: "egx-status--pending";

			details.innerHTML = `
				<div style="display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;align-items:flex-start">
					<div>
						<h3 style="margin:0 0 0.5rem">Provisioning Details</h3>
						<p style="margin:0 0 0.75rem;color:var(--egx-text-muted)">
							Request: <strong>${escapeHtml(requestName || "—")}</strong>
							· Tenant: <strong>${escapeHtml(tenantName || data.tenant_name || "—")}</strong>
						</p>
					</div>
					<div class="egx-status ${statusChipClass}">${escapeHtml(status)}</div>
				</div>
				<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0.75rem;margin-top:1rem">
					<div><span style="color:var(--egx-text-muted)">Progress</span><div style="font-weight:700">${Math.round(progressPct)}%</div></div>
					<div><span style="color:var(--egx-text-muted)">Stage</span><div style="font-weight:700">${escapeHtml((data.progress && data.progress.step) || data.provisioning_status || "—")}</div></div>
					<div><span style="color:var(--egx-text-muted)">Request Status</span><div style="font-weight:700">${escapeHtml(data.request_status || status || "—")}</div></div>
					<div><span style="color:var(--egx-text-muted)">Tenant Status</span><div style="font-weight:700">${escapeHtml(data.tenant_status || "—")}</div></div>
				</div>
				<div style="margin-top:1rem;padding:1rem;border-radius:12px;background:rgba(15,23,42,.04)">
					<div style="color:var(--egx-text-muted);font-size:.85rem;margin-bottom:.4rem">Summary</div>
					<div style="font-weight:600;white-space:pre-wrap">${escapeHtml(summary)}</div>
				</div>
				${errorDetails ? `
					<div style="margin-top:1rem">
						<div style="color:var(--egx-text-muted);font-size:.85rem;margin-bottom:.4rem">Details</div>
						<pre style="max-height:240px;overflow:auto;background:#0f172a;color:#e2e8f0;padding:1rem;border-radius:10px;white-space:pre-wrap">${escapeHtml(errorDetails)}</pre>
					</div>
				` : ""}
				${traceback ? `
					<div style="margin-top:1rem">
						<div style="color:var(--egx-text-muted);font-size:.85rem;margin-bottom:.4rem">Traceback</div>
						<pre style="max-height:320px;overflow:auto;background:#111827;color:#f8fafc;padding:1rem;border-radius:10px;white-space:pre-wrap">${escapeHtml(traceback)}</pre>
					</div>
				` : ""}
				${stageLogs.length ? `
					<div style="margin-top:1rem">
						<div style="color:var(--egx-text-muted);font-size:.85rem;margin-bottom:.4rem">Stages</div>
						<table class="egx-table">
							<thead>
								<tr><th>Stage</th><th>Status</th><th>Duration</th><th>Start</th></tr>
							</thead>
							<tbody>
								${stageLogs.map((row) => `
									<tr>
										<td>${escapeHtml(row.stage || "—")}</td>
										<td>${escapeHtml(row.status || "—")}</td>
										<td>${escapeHtml(row.duration_seconds != null ? row.duration_seconds : "—")}</td>
										<td>${escapeHtml(row.start_time || "—")}</td>
									</tr>
								`).join("")}
							</tbody>
						</table>
					</div>
				` : ""}
			`;
		}

		function handleStatus(data) {
			if (!data) return;
			finalState = data;
			renderDetails(data);
			if (data.failed || data.status === "Failed") {
				stopPolling();
				return;
			}
			if (data.completed || data.status === "Completed" || data.tenant_status === "Active") {
				stopPolling();
				finish();
			}
		}

		function registerPaypalPayment(query) {
			if (!query.paypal_return || !query.invoice) {
				return Promise.resolve(null);
			}

			const transactionId =
				query.tx || query.paymentId || query.transaction_id || "PP-" + Date.now();
			const amount = parseFloat(query.amount || 0) || 0;

			return new Promise((resolve, reject) => {
				frappe.call({
					method: "erpgenex_saas.api.portal.register_invoice_payment",
					args: {
						invoice: query.invoice,
						provider: "PayPal",
						transaction_id: transactionId,
						amount: amount,
						payload: query,
					},
					callback: function (response) {
						resolve(response.message || {});
					},
					error: function (err) {
						reject(err);
					},
				});
			});
		}

		function pollStatus() {
			if (!requestName || !window.frappe || !frappe.call) return;
			frappe.call({
				method: "erpgenex_saas.api.v1.get_provisioning_status",
				args: { request_name: requestName },
				callback: function (response) {
					const payload = response.message || {};
					handleStatus(payload);
				},
			});
		}

		function finish() {
			stopPolling();
			setStep(STEPS.length);
			setTimeout(() => {
				const rootDomain = getRootDomain();
				const slug = tenantName ? tenantName.toLowerCase().replace(/\s+/g, "-") : "";
				window.location.href =
					"/saas/success?tenant=" + encodeURIComponent(tenantName || "") +
					"&site=" + encodeURIComponent(slug ? `${slug}.${rootDomain}` : "");
			}, 1200);
		}

		function runAnimation() {
			if (finalState && (finalState.failed || finalState.status === "Failed" || finalState.completed || finalState.status === "Completed")) {
				return;
			}
			if (currentStep >= STEPS.length) {
				finish();
				return;
			}
			setStep(currentStep);
			currentStep += 1;
			setTimeout(runAnimation, 1400);
		}

		function startProvisioning() {
			if (requestName && window.frappe && frappe.call) {
				frappe.call({
					method: "erpgenex_saas.api.v1.start_provisioning",
					args: { request_name: requestName },
					callback: function () {
						runAnimation();
						pollStatus();
						pollTimer = setInterval(pollStatus, 2500);
					},
					error: function () {
						runAnimation();
						pollStatus();
						pollTimer = setInterval(pollStatus, 2500);
					},
				});
			} else {
				runAnimation();
			}
		}

		const query = getCurrentQueryObject();
		if (query.paypal_return) {
			registerPaypalPayment(query)
				.then(() => {
					const cleanUrl = buildUrl("/saas/provisioning", {
						request: requestName || "",
						tenant: tenantName || "",
					});
					window.history.replaceState({}, "", cleanUrl);
					localStorage.removeItem(STORAGE_KEY);
					startProvisioning();
				})
				.catch((err) => {
					details.insertAdjacentHTML(
						"beforeend",
						`<div style="margin-top:1rem;color:#b91c1c;font-weight:600">${escapeHtml(
							err.message || "Unable to verify PayPal payment."
						)}</div>`
					);
				});
			return;
		}

		startProvisioning();
	}

	/* ── Success ── */
	function initSuccess() {
		const page = qs(".egx-success");
		if (!page) return;

		const tenant = getQueryParam("tenant") || "your-tenant";
		const rootDomain = getRootDomain();
		const site = getQueryParam("site") || `${tenant.toLowerCase().replace(/\s+/g, "-")}.${rootDomain}`;
		const urlEl = qs("#egx-success-url");
		if (urlEl) urlEl.textContent = `${getScheme()}://${site}`;

		const copyBtn = qs("#egx-copy-url");
		if (copyBtn) {
			copyBtn.addEventListener("click", () => {
				navigator.clipboard.writeText(`${getScheme()}://${site}`);
				copyBtn.textContent = "Copied!";
				setTimeout(() => (copyBtn.textContent = "Copy URL"), 2000);
			});
		}

		spawnConfetti();
	}

	function spawnConfetti() {
		const wrap = document.createElement("div");
		wrap.className = "egx-confetti";
		const colors = ["#4F46E5", "#7C3AED", "#22C55E", "#3B82F6", "#F59E0B"];
		for (let i = 0; i < 60; i++) {
			const piece = document.createElement("div");
			piece.className = "egx-confetti__piece";
			piece.style.left = Math.random() * 100 + "%";
			piece.style.background = colors[i % colors.length];
			piece.style.animationDelay = Math.random() * 2 + "s";
			piece.style.borderRadius = Math.random() > 0.5 ? "50%" : "2px";
			wrap.appendChild(piece);
		}
		document.body.appendChild(wrap);
		setTimeout(() => wrap.remove(), 4000);
	}

	/* ── Dashboard ── */
	function initDashboard() {
		const root = qs("#egx-dashboard-root");
		if (!root || root.dataset.nativeDashboard === "1" || !window.frappe || !frappe.call) return;

		root.innerHTML = '<div class="egx-skeleton" style="height:400px"></div>';

		frappe.call({
			method: "erpgenex_saas.api.customer.get_dashboard",
			callback: function (response) {
				renderDashboard(root, response.message || {});
			},
			error: function () {
				root.innerHTML =
					'<div class="egx-card egx-fade-in"><h3>Sign in required</h3><p class="egx-subtitle">Please <a href="/login">log in</a> to access your dashboard.</p><a class="egx-btn egx-btn--primary" href="/saas/register">Get Started</a></div>';
			},
		});
	}

	function renderDashboard(root, data) {
		const tenant = data.tenant || {};
		const sub = data.subscription || {};
		const invoices = data.invoices || [];
		const payments = data.payments || [];
		const domains = data.domains || [];
		const storagePct = 42;
		const cpuPct = 28;
		const ramPct = 56;

		const deploymentLogs = data.deployment_logs || [];
		const accessUrl = tenant.access_url || tenant.site_url;
		const openUrl = accessUrl || (tenant.site_name ? "https://" + tenant.site_name : "");

		root.innerHTML = `
			<div class="egx-dash__header egx-fade-in">
				<div>
					<span class="egx-eyebrow">Customer Dashboard</span>
					<h1 class="egx-section__title">${tenant.tenant_name || tenant.name || "Workspace"}</h1>
					<p class="egx-subtitle" style="margin:0">${accessUrl || tenant.site_name || "Provisioning…"} · <span class="egx-status egx-status--${(tenant.status || "").toLowerCase() === "active" ? "active" : "pending"}">${tenant.status || "Pending"}</span></p>
				</div>
				<div style="display:flex;gap:0.75rem;flex-wrap:wrap">
					<a class="egx-btn egx-btn--secondary egx-btn--sm" href="/saas/applications">Add Apps</a>
					<button class="egx-btn egx-btn--primary egx-btn--sm" type="button" id="egx-open-site">Open Site</button>
				</div>
			</div>

			<div class="egx-card egx-fade-in" style="margin-bottom:1.25rem">
				<h4 style="margin:0 0 1rem">Site Deployment</h4>
				<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem;font-size:0.92rem">
					<div><span style="color:var(--egx-text-muted)">Deployment Mode</span><div style="font-weight:700">${tenant.deployment_mode || "—"}</div></div>
					<div><span style="color:var(--egx-text-muted)">Port</span><div style="font-weight:700">${tenant.port_number || "—"}</div></div>
					<div><span style="color:var(--egx-text-muted)">Domain</span><div style="font-weight:700">${tenant.domain || tenant.site_name || "—"}</div></div>
					<div><span style="color:var(--egx-text-muted)">Service Status</span><div><span class="egx-status egx-status--${tenant.service_status === "Running" ? "active" : "pending"}">${tenant.service_status || "Unknown"}</span></div></div>
					<div><span style="color:var(--egx-text-muted)">Health Status</span><div><span class="egx-status egx-status--${tenant.health_status === "Healthy" ? "active" : "pending"}">${tenant.health_status || "Unknown"}</span></div></div>
					<div><span style="color:var(--egx-text-muted)">Last Check</span><div style="font-weight:700">${tenant.last_health_check || "—"}</div></div>
				</div>
				<div style="display:flex;gap:0.75rem;flex-wrap:wrap;margin-top:1rem">
					<button class="egx-btn egx-btn--outline egx-btn--sm" type="button" id="egx-restart-service">Restart Service</button>
					<button class="egx-btn egx-btn--ghost egx-btn--sm" type="button" id="egx-view-logs">View Logs</button>
				</div>
				<pre id="egx-site-logs" style="display:none;margin-top:1rem;max-height:240px;overflow:auto;background:#0f172a;color:#e2e8f0;padding:1rem;border-radius:8px;font-size:0.78rem"></pre>
			</div>

			<div class="egx-dash-tabs egx-fade-in" role="tablist">
				<button class="egx-dash-tab is-active" data-tab="overview" type="button">Overview</button>
				<button class="egx-dash-tab" data-tab="subscription" type="button">Subscription</button>
				<button class="egx-dash-tab" data-tab="domains" type="button">Domains</button>
			</div>

			<div id="egx-tab-overview" class="egx-tab-panel">
				<div class="egx-dash-grid">
					<div class="egx-card egx-metric-card"><div class="egx-metric-card__label">Plan</div><div class="egx-metric-card__value" style="font-size:1.2rem">${sub.plan || "—"}</div></div>
					<div class="egx-card egx-metric-card"><div class="egx-metric-card__label">Monthly Total</div><div class="egx-metric-card__value">${formatMoney(sub.total_amount || sub.base_amount)}</div></div>
					<div class="egx-card egx-metric-card"><div class="egx-metric-card__label">Invoices</div><div class="egx-metric-card__value">${invoices.length}</div></div>
					<div class="egx-card egx-metric-card"><div class="egx-metric-card__label">Payments</div><div class="egx-metric-card__value">${payments.length}</div></div>
				</div>
				<div class="egx-dash-grid" style="grid-template-columns:repeat(3,1fr)">
					<div class="egx-card"><h4 style="margin:0 0 1rem;font-size:0.95rem">Storage</h4>${ring(storagePct, "GB")}</div>
					<div class="egx-card"><h4 style="margin:0 0 1rem;font-size:0.95rem">CPU</h4>${ring(cpuPct, "%")}</div>
					<div class="egx-card"><h4 style="margin:0 0 1rem;font-size:0.95rem">RAM</h4>${ring(ramPct, "%")}</div>
				</div>
				<div class="egx-card" style="margin-top:1.25rem">
					<h4 style="margin:0 0 1rem">Usage Analytics</h4>
					<div class="egx-chart-bar">${[65, 45, 80, 55, 90, 70, 85].map((h) => `<div class="egx-chart-bar__item" style="height:${h}%"></div>`).join("")}</div>
				</div>
				<div class="egx-card" style="margin-top:1.25rem">
					<h4 style="margin:0 0 1rem">Recent Activity</h4>
					<table class="egx-table"><thead><tr><th>Event</th><th>Status</th><th>Date</th></tr></thead>
					<tbody>${deploymentLogs.map((log) => `<tr><td>${log.stage}</td><td><span class="egx-status egx-status--${log.status === "Success" ? "active" : "pending"}">${log.status}</span></td><td>${log.start_time || "—"}</td></tr>`).join("") || invoices.slice(0, 5).map((inv) => `<tr><td>Invoice ${inv.name}</td><td><span class="egx-status egx-status--${inv.status === "Paid" ? "active" : "pending"}">${inv.status}</span></td><td>${inv.invoice_date || "—"}</td></tr>`).join("") || "<tr><td colspan=3>No activity yet</td></tr>"}</tbody></table>
				</div>
			</div>

			<div id="egx-tab-subscription" class="egx-tab-panel" hidden>
				<div class="egx-card" style="margin-bottom:1.25rem">
					<h3 style="margin:0 0 0.5rem">${sub.plan || "No plan"}</h3>
					<p style="color:var(--egx-text-muted);margin:0 0 1.5rem">${sub.billing_cycle || ""} · Status: <span class="egx-status egx-status--active">${sub.status || "—"}</span></p>
					<div style="display:flex;gap:0.75rem;flex-wrap:wrap">
						<button class="egx-btn egx-btn--primary egx-btn--sm" type="button" data-sub-action="upgrade">Upgrade</button>
						<button class="egx-btn egx-btn--secondary egx-btn--sm" type="button" data-sub-action="downgrade">Downgrade</button>
						<button class="egx-btn egx-btn--outline egx-btn--sm" type="button" data-sub-action="pause">Pause</button>
						<button class="egx-btn egx-btn--ghost egx-btn--sm" type="button" data-sub-action="cancel">Cancel</button>
					</div>
				</div>
				<div class="egx-card">
					<h4 style="margin:0 0 1rem">Invoices & Payments</h4>
					<table class="egx-table"><thead><tr><th>Invoice</th><th>Amount</th><th>Status</th></tr></thead>
					<tbody>${invoices.map((inv) => `<tr><td>${inv.name}</td><td>${formatMoney(inv.amount_due)}</td><td><span class="egx-status egx-status--${inv.status === "Paid" ? "active" : "pending"}">${inv.status}</span></td></tr>`).join("") || "<tr><td colspan=3>No invoices</td></tr>"}</tbody></table>
				</div>
			</div>

			<div id="egx-tab-domains" class="egx-tab-panel" hidden>
				<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1.25rem">
					<h3 style="margin:0">Domain Management</h3>
					<button class="egx-btn egx-btn--primary egx-btn--sm" type="button" id="egx-add-domain">Add Domain</button>
				</div>
				<div class="egx-app-grid">${domains.map((d) => `
					<div class="egx-card">
						<div style="font-weight:700;margin-bottom:0.5rem">${d.domain_name}</div>
						<div style="font-size:0.85rem;color:var(--egx-text-muted);margin-bottom:0.75rem">DNS: <span class="egx-status egx-status--${d.status === "Verified" ? "active" : "pending"}">${d.status}</span> · SSL: ${d.ssl_status || "Pending"}</div>
						<button class="egx-btn egx-btn--outline egx-btn--sm" type="button">Verify</button>
					</div>`).join("") || '<div class="egx-card">No domains yet. Your primary subdomain will appear after provisioning.</div>'}
				</div>
			</div>`;

		qsa(".egx-dash-tab", root).forEach((tab) => {
			tab.addEventListener("click", () => {
				qsa(".egx-dash-tab", root).forEach((t) => t.classList.remove("is-active"));
				tab.classList.add("is-active");
				qsa(".egx-tab-panel", root).forEach((p) => (p.hidden = true));
				const panel = qs("#egx-tab-" + tab.dataset.tab, root);
				if (panel) panel.hidden = false;
			});
		});

		const openBtn = qs("#egx-open-site", root);
		if (openBtn && openUrl) {
			openBtn.addEventListener("click", () => window.open(openUrl, "_blank"));
		}

		const restartBtn = qs("#egx-restart-service", root);
		if (restartBtn && frappe.call) {
			restartBtn.addEventListener("click", () => {
				restartBtn.disabled = true;
				frappe.call({
					method: "erpgenex_saas.api.customer.restart_site_service",
					callback: () => initDashboard(),
					error: () => {
						restartBtn.disabled = false;
					},
				});
			});
		}

		const logsBtn = qs("#egx-view-logs", root);
		const logsBox = qs("#egx-site-logs", root);
		if (logsBtn && logsBox && frappe.call) {
			logsBtn.addEventListener("click", () => {
				frappe.call({
					method: "erpgenex_saas.api.customer.get_site_logs",
					callback: function (response) {
						logsBox.style.display = "block";
						logsBox.textContent = (response.message && response.message.logs) || "No logs available.";
					},
				});
			});
		}

		qsa("[data-sub-action]", root).forEach((btn) => {
			btn.addEventListener("click", () => {
				const action = btn.dataset.subAction;
				if (!sub.name || !frappe.call) return;
				const method =
					action === "pause"
						? "erpgenex_saas.api.v1.pause_subscription"
						: action === "cancel"
							? "erpgenex_saas.api.v1.cancel_subscription"
							: null;
				if (method) {
					frappe.call({ method, args: { subscription: sub.name }, callback: () => initDashboard() });
				} else if (action === "upgrade") {
					window.location.href = "/saas/pricing";
				}
			});
		});
	}

	function ring(pct, label) {
		const r = 34;
		const c = 2 * Math.PI * r;
		const offset = c - (pct / 100) * c;
		return `<div class="egx-ring"><svg width="80" height="80" viewBox="0 0 80 80"><circle cx="40" cy="40" r="${r}" fill="none" stroke="#E7EAF0" stroke-width="6"/><circle cx="40" cy="40" r="${r}" fill="none" stroke="url(#grad)" stroke-width="6" stroke-dasharray="${c}" stroke-dashoffset="${offset}" stroke-linecap="round"/><defs><linearGradient id="grad" x1="0%" y1="0%" x2="100%"><stop offset="0%" stop-color="#4F46E5"/><stop offset="100%" stop-color="#7C3AED"/></linearGradient></defs></svg><div class="egx-ring__label">${pct}${label === "%" ? "%" : ""}</div></div>`;
	}

	function isPortalPage() {
		const path = window.location.pathname || "";
		return (
			path.startsWith("/saas") ||
			!!document.querySelector(".egx-portal") ||
			!!document.querySelector("#egx-dashboard-root")
		);
	}

	/* ── Init ── */
	document.addEventListener("DOMContentLoaded", function () {
		if (!isPortalPage()) return;
		document.body.classList.add("egx-portal-body");
		initNav();
		initCounters();
		initPricing();
		initMarketplace();
		initCheckout();
		initProvisioning();
		initSuccess();
		initDashboard();
	});

	window.erpgenexSaas = window.erpgenexSaas || {};
	window.erpgenexSaas.redirectToPayPal = redirectToPayPal;
	window.erpgenexSaas.buildUrl = buildUrl;
	window.erpgenexSaas.getPaypalConfig = getPaypalConfig;
})();
