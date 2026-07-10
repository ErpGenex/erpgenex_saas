# Provisioning Flow Analysis

## Current Flow

### Entry Point
**File**: `erpgenex_saas/services/provisioning.py`
**Function**: `ProvisioningService.run(request_name: str)`
**Lines**: 27-206

### Flow Sequence

#### 1. Request Initialization (Lines 28-33)
```python
request = frappe.get_doc("Provisioning Request", request_name)
request.status = "Running"
request.last_message = "Provisioning started"
request.execution_log = "Queued request picked up by worker\n"
request.save(ignore_permissions=True)
```

#### 2. Service Initialization (Lines 35-44)
```python
progress_tracker = ProgressTracker()
password_manager = PasswordManager()
monitoring = MonitoringService()
progress_tracker.start(request.tenant)
monitoring.log_metrics(request.tenant)
```

#### 3. Configuration Parsing (Lines 47-53)
```python
provisioning_config = {}
if request.execution_log:
    try:
        provisioning_config = json.loads(request.execution_log)
    except json.JSONDecodeError:
        provisioning_config = {}
```

#### 4. SaaS Settings Retrieval (Lines 55-57)
```python
saas_settings = frappe.get_single("SaaS Settings")
site_distribution_method = saas_settings.site_distribution_method or "Subdomain"
```

#### 5. Tenant Configuration (Lines 61-103)
- Set tenant status to "Provisioning"
- Handle server type (dedicated vs shared)
- Generate site name based on distribution method
- Port-based: `platform_domain:port`
- Subdomain-based: `subdomain.platform_domain`

#### 6. Progress Update (Lines 68-69, 106-107)
```python
progress_tracker.update(request.tenant, "configuring_server", 10)
progress_tracker.update(request.tenant, "tenant_configured", 20)
```

#### 7. Site Creation (Lines 121-140)
```python
site_created = ProvisioningService.create_site(tenant.site_name, tenant.name)
```

#### 8. Tenant Activation (Lines 142-150)
```python
request.status = "Completed"
tenant.status = "Active"
tenant.provisioned_on = frappe.utils.now_datetime()
progress_tracker.update(request.tenant, "tenant_activated", 80)
```

#### 9. Domain Creation (Lines 152-167)
- Create domain record based on distribution method
- Call `DomainService.create_domain()`

#### 10. Subscription Update (Lines 169-173)
- Update subscription status if exists

#### 11. Notification (Lines 175-180)
- Send notification via `NotificationService.notify()`

#### 12. Audit Log (Lines 181-191)
- Log provisioning completion via `AuditService.log()`

#### 13. Progress Completion (Lines 193-197)
```python
progress_tracker.complete(request.tenant)
monitoring.log_metrics(request.tenant)
```

### Site Creation Sub-flow

#### Function: `create_site(site_name, tenant_name)`
**Lines**: 227-338

#### 1. Password Retrieval (Lines 233-246)
```python
password_manager = PasswordManager()
saas_settings = frappe.get_single("SaaS Settings")
database_password = password_manager.get_db_password()
mariadb_root_password = password_manager.get_mariadb_root_password()
admin_password = password_manager.generate_password(length=12)
```

#### 2. Folder Name Generation (Lines 248-258)
- Handle port-based sites: `domain_port_port`
- Handle subdomain sites: `subdomain.domain`

#### 3. Site Existence Check (Lines 260-264)
```python
site_path = os.path.join(bench_path, "sites", folder_name)
if os.path.exists(site_path):
    return True
```

#### 4. Bench New-Site Command (Lines 266-286)
```python
command = [
    "bench",
    "new-site",
    folder_name,
    "--admin-password", database_password,  # ❌ ISSUE: Should be admin_password
    "--mariadb-root-password", mariadb_root_password,
    "--no-mariadb-socket"
]
```

#### 5. Site Config Update (Lines 291-300)
```python
site_config_path = os.path.join(bench_path, "sites", folder_name, "site_config.json")
config['db_password'] = database_password
```

#### 6. Site Configuration (Line 303)
```python
ProvisioningService.configure_site(folder_name, site_name, server_ip, server_port, admin_password)
```

#### 7. Credential Saving (Lines 306-322)
```python
tenant.admin_username = "Administrator"
tenant.admin_password = admin_password
tenant.site_url = f"http://{server_ip}:{port}"
tenant.save(ignore_permissions=True)
```

### Site Configuration Sub-flow

#### Function: `configure_site(folder_name, access_name, server_ip, server_port, admin_password)`
**Lines**: 341-450

#### 1. App Installation (Lines 347-372)
```python
apps_to_install = ["frappe", "omnexa_core"]
for app in apps_to_install:
    bench --site folder_name install-app app
```

#### 2. Admin Password Setting (Lines 381-401)
```python
bench --site folder_name set-admin-password admin_password
```

#### 3. Nginx Port Configuration (Lines 404-424)
```python
bench set-nginx-port folder_name target_port
sudo nginx -s reload
```

## Issues Identified

### Critical Issues
1. **Line 275**: Admin password incorrectly set to database password
2. **Line 268-278**: No rollback on failure
3. **Line 290-300**: Manual config update indicates initial config is wrong

### Medium Issues
1. **Lines 351-352**: Hardcoded app list
2. **Lines 369-371**: App installation failures don't stop process
3. **Lines 420-422**: Nginx failures only logged as warnings

### Low Issues
1. **Line 231**: Hardcoded bench path
2. **Lines 323-326**: Credential saving failure doesn't fail process
3. **Line 428**: Hardcoded sudo command

## Recommended Flow Improvements

### 1. Add Pre-flight Checks
- Verify MariaDB connectivity
- Verify port availability
- Verify disk space
- Verify SaaS Settings integrity

### 2. Improve Error Handling
- Add specific error types
- Implement retry logic
- Add detailed error messages
- Implement rollback on failure

### 3. Enhance Logging
- Add structured logging
- Remove password logging
- Add performance metrics
- Add step-by-step logging

### 4. Add Rollback Mechanism
- Delete database on failure
- Delete database user on failure
- Delete site folder on failure
- Clean up temporary files

### 5. Improve Progress Tracking
- Add more granular steps
- Add estimated time remaining
- Add current operation details
- Add failure reason display
