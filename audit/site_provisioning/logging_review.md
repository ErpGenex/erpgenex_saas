# Logging Review

## Current Logging Status
**Status**: ⚠️ PARTIALLY IMPLEMENTED

## Logging Implementation

### Logger Initialization
**Location**: Line 28, 230, 344 in provisioning.py
```python
logger = frappe.logger("erpgenex_saas")
```

**Assessment**: ✅ Good
- Uses Frappe's built-in logger
- Named logger for easy filtering
- Consistent usage

### Current Logging Points

#### 1. Provisioning Start
**Location**: Line 31
```python
request.last_message = "Provisioning started"
request.execution_log = "Queued request picked up by worker\n"
```
**Assessment**: ✅ Good

#### 2. Server Configuration
**Location**: Lines 80-83
```python
request.execution_log += f"Using dedicated server: {server_ip}\n"
request.execution_log += f"Domain: {domain_name}\n"
if enable_ssl:
    request.execution_log += "SSL enabled\n"
```
**Assessment**: ✅ Good

#### 3. Business Activity
**Location**: Lines 112-114
```python
request.execution_log += f"Business Activity: {business_activity}\n"
request.execution_log += f"Site Distribution Method: {site_distribution_method}\n"
request.execution_log += f"Apps to install: {', '.join(str(app) for app in apps_to_install)}\n"
```
**Assessment**: ✅ Good

#### 4. Site Creation
**Location**: Lines 122, 130, 137
```python
request.execution_log += f"Creating actual site: {tenant.site_name}\n"
request.execution_log += f"Site created successfully\n"
request.execution_log += f"Site creation failed, continuing with database record only\n"
```
**Assessment**: ✅ Good

#### 5. Site Creation Details
**Location**: Lines 267, 289, 300
```python
logger.info(f"Creating new site: {folder_name} (will be accessible on {site_name})")
logger.info(f"Site {folder_name} created successfully with password from settings")
logger.info(f"Updated database password in site_config.json")
```
**Assessment**: ✅ Good

#### 6. Admin Credentials
**Location**: Lines 319-322
```python
logger.info(f"Saved admin credentials to tenant {tenant_name}")
logger.info(f"Admin Username: {tenant.admin_username}")
logger.info(f"Admin Password: {tenant.admin_password}")  # ❌ SECURITY ISSUE
logger.info(f"Site URL: {tenant.site_url}")
```
**Assessment**: ❌ CRITICAL - Password logged in plain text

#### 7. App Installation
**Location**: Lines 348, 354, 371, 372
```python
logger.info(f"Installing apps on site {folder_name}")
logger.info(f"Installing {app} on {folder_name}")
logger.error(f"Failed to install {app} on {folder_name}: {result.stderr}")
logger.info(f"Successfully installed {app} on {folder_name}")
```
**Assessment**: ✅ Good

#### 8. Admin Password Setting
**Location**: Lines 382, 401
```python
logger.info(f"Setting admin password for site {folder_name}")
logger.info(f"Successfully set admin password for {folder_name}")
```
**Assessment**: ✅ Good

#### 9. Nginx Configuration
**Location**: Lines 404, 421, 424, 428, 441, 443, 444
```python
logger.info(f"Setting nginx port for {folder_name} to {target_port}")
logger.warning(f"nginx not available or failed to set port: {result.stderr}")
logger.info(f"Successfully set nginx port for {folder_name} to {target_port}")
logger.info(f"Reloading nginx to apply configuration")
logger.info(f"Successfully reloaded nginx")
logger.info(f"Site {folder_name} configured to be accessible on {server_ip}:{target_port}")
logger.info(f"Access URL: http://{server_ip}:{target_port}")
```
**Assessment**: ✅ Good

#### 10. Provisioning Completion
**Location**: Lines 199-200
```python
logger.info("Provisioning completed for tenant %s with activity %s using %s distribution", 
    tenant.name, business_activity, site_distribution_method)
```
**Assessment**: ✅ Good

#### 11. Provisioning Failure
**Location**: Lines 202-205
```python
logger.error("Provisioning failed for request %s", request_name)
```
**Assessment**: ⚠️ Limited - No detailed error context

## Missing Logging Points

### Critical Missing Logs
1. **Pre-flight Checks**: No logging of pre-flight verification
2. **Database Creation**: No logging of database creation steps
3. **Database User Creation**: No logging of user creation
4. **Database Permissions**: No logging of permission assignment
5. **Rollback Operations**: No logging of rollback operations
6. **Performance Metrics**: No logging of operation durations

### Important Missing Logs
1. **Settings Retrieval**: No logging of settings values
2. **Password Generation**: No logging of password generation (should be masked)
3. **Port Allocation**: No logging of port allocation details
4. **Domain Creation**: No logging of domain creation
5. **Subscription Update**: No logging of subscription changes
6. **Notification Sending**: No logging of notification delivery

### Useful Missing Logs
1. **Memory Usage**: No logging of memory consumption
2. **Disk Usage**: No logging of disk space
3. **Network Status**: No logging of network connectivity
4. **Service Status**: No logging of service availability

## Logging Issues

### Critical Issues
1. **Password Logging**: Admin password logged in plain text (Line 321)
2. **No Rollback Logging**: No logging of rollback operations
3. **No Performance Logging**: No timing information

### Medium Issues
1. **Inconsistent Log Levels**: Mix of info/error/warning
2. **No Structured Logging**: Plain text logs instead of structured
3. **No Log Correlation**: No request ID in all logs
4. **No Error Context**: Limited error details in failure logs

### Low Issues
1. **No Log Rotation**: No log rotation configuration
2. **No Log Retention**: No log retention policy
3. **No Log Aggregation**: No centralized logging
4. **No Log Analysis**: No log analysis tools

## Recommended Logging Improvements

### Critical Priority
1. **Remove Password Logging**: Mask all passwords in logs
2. **Add Rollback Logging**: Log all rollback operations
3. **Add Performance Logging**: Log operation durations
4. **Add Error Context**: Add detailed error information

### High Priority
1. **Add Pre-flight Logging**: Log pre-flight check results
2. **Add Database Logging**: Log database creation steps
3. **Add Structured Logging**: Use structured log format
4. **Add Log Correlation**: Add request ID to all logs

### Medium Priority
1. **Add Settings Logging**: Log settings values (masked)
2. **Add Resource Logging**: Log memory and disk usage
3. **Add Network Logging**: Log network status
4. **Add Service Logging**: Log service availability

### Low Priority
1. **Add Log Rotation**: Configure log rotation
2. **Add Log Retention**: Define log retention policy
3. **Add Log Aggregation**: Implement centralized logging
4. **Add Log Analysis**: Implement log analysis

## Proposed Logging Structure

### Structured Log Format
```python
logger.info(json.dumps({
    "request_id": request_name,
    "tenant": tenant_name,
    "operation": "site_creation",
    "status": "started",
    "timestamp": frappe.utils.now_datetime().isoformat(),
    "duration": 0
}))
```

### Performance Logging
```python
import time

start_time = time.time()
# Operation
duration = time.time() - start_time

logger.info(json.dumps({
    "request_id": request_name,
    "operation": "database_creation",
    "duration": duration,
    "timestamp": frappe.utils.now_datetime().isoformat()
}))
```

### Error Logging
```python
try:
    # Operation
except Exception as e:
    logger.error(json.dumps({
        "request_id": request_name,
        "operation": "site_creation",
        "status": "failed",
        "error": str(e),
        "traceback": frappe.get_traceback(),
        "timestamp": frappe.utils.now_datetime().isoformat()
    }))
```

### Rollback Logging
```python
logger.info(json.dumps({
    "request_id": request_name,
    "operation": "rollback",
    "step": "database_deletion",
    "status": "started",
    "timestamp": frappe.utils.now_datetime().isoformat()
}))
```

## Logging Best Practices

### 1. Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical errors requiring immediate attention

### 2. Log Content
- Include request ID in all logs
- Include timestamp in all logs
- Include operation name in all logs
- Include status in all logs
- Mask sensitive information

### 3. Log Format
- Use structured logging (JSON)
- Use consistent field names
- Use ISO format for timestamps
- Use consistent error formats

### 4. Log Security
- Never log passwords
- Never log API keys
- Never log sensitive data
- Mask PII when necessary

### 5. Log Performance
- Log operation durations
- Log resource usage
- Log bottlenecks
- Log performance degradation

## Logging Checklist

- [ ] No passwords logged in plain text
- [ ] No sensitive data logged
- [ ] All logs include request ID
- [ ] All logs include timestamp
- [ ] All logs include operation name
- [ ] All logs include status
- [ ] Structured logging implemented
- [ ] Performance logging implemented
- [ ] Error logging includes context
- [ ] Rollback logging implemented
- [ ] Pre-flight logging implemented
- [ ] Database logging implemented
- [ ] Resource logging implemented
- [ ] Network logging implemented
- [ ] Service logging implemented
- [ ] Log rotation configured
- [ ] Log retention defined
- [ ] Log aggregation implemented
- [ ] Log analysis implemented
