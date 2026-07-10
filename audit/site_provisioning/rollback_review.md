# Rollback Mechanism Review

## Current Rollback Status
**Status**: ❌ NOT IMPLEMENTED

## Current Error Handling

### Site Creation Error Handling
**Location**: Lines 333-338 in provisioning.py
```python
except subprocess.TimeoutExpired:
    logger.error(f"Site creation timed out for {site_name}")
    return False
except Exception as e:
    logger.error(f"Error creating site {site_name}: {str(e)}")
    return False
```

**Issues**:
- No cleanup of partial site creation
- No database deletion
- No database user deletion
- No site folder deletion
- No temporary file cleanup
- No status update to Failed

### Provisioning Error Handling
**Location**: Lines 201-206 in provisioning.py
```python
except Exception:
    request.status = "Failed"
    request.last_message = frappe.get_traceback(with_context=True)
    request.save(ignore_permissions=True)
    logger.error("Provisioning failed for request %s", request_name)
    raise
```

**Issues**:
- No cleanup of created resources
- No database deletion
- No site folder deletion
- No domain record deletion
- No tenant status update
- No notification of failure

## Orphaned Data Risks

### Database Orphans
- **Risk**: High
- **Scenario**: Site creation fails after database creation
- **Impact**: Unused databases consume space
- **Cleanup**: Manual intervention required

### Database User Orphans
- **Risk**: High
- **Scenario**: Site creation fails after user creation
- **Impact**: Unused users consume resources
- **Cleanup**: Manual intervention required

### Site Folder Orphans
- **Risk**: Medium
- **Scenario**: Site creation fails after folder creation
- **Impact**: Unused folders consume disk space
- **Cleanup**: Manual intervention required

### Domain Record Orphans
- **Risk**: Low
- **Scenario**: Provisioning fails after domain creation
- **Impact**: Inconsistent domain records
- **Cleanup**: Manual intervention required

### Tenant Record Orphans
- **Risk**: Low
- **Scenario**: Provisioning fails with tenant in wrong state
- **Impact**: Tenant status inconsistent
- **Cleanup**: Manual status update required

## Required Rollback Mechanisms

### 1. Database Rollback
**Function**: `rollback_database(site_name)`
**Actions**:
- Connect to MariaDB as root
- Drop database if exists
- Drop database user if exists
- Revoke all privileges
- Flush privileges

**Implementation**:
```python
def rollback_database(site_name):
    """Rollback database creation"""
    try:
        # Get database name from site name
        db_name = site_name.replace('-', '_').replace('.', '_')
        
        # Get MariaDB root password
        password_manager = PasswordManager()
        root_password = password_manager.get_mariadb_root_password()
        
        # Drop database
        frappe.db.sql(f"DROP DATABASE IF EXISTS `{db_name}`")
        
        # Drop user
        frappe.db.sql(f"DROP USER IF EXISTS `{db_name}`@`localhost`")
        
        # Flush privileges
        frappe.db.sql("FLUSH PRIVILEGES")
        
        logger.info(f"Database rollback completed for {db_name}")
        return True
    except Exception as e:
        logger.error(f"Database rollback failed: {str(e)}")
        return False
```

### 2. Site Folder Rollback
**Function**: `rollback_site_folder(folder_name)`
**Actions**:
- Check if folder exists
- Delete folder recursively
- Verify deletion

**Implementation**:
```python
def rollback_site_folder(folder_name):
    """Rollback site folder creation"""
    try:
        bench_path = "/home/frappeuser/frappe-bench"
        site_path = os.path.join(bench_path, "sites", folder_name)
        
        if os.path.exists(site_path):
            shutil.rmtree(site_path)
            logger.info(f"Site folder rollback completed for {folder_name}")
            return True
        else:
            logger.info(f"Site folder does not exist: {folder_name}")
            return True
    except Exception as e:
        logger.error(f"Site folder rollback failed: {str(e)}")
        return False
```

### 3. Domain Record Rollback
**Function**: `rollback_domain_record(tenant_name)`
**Actions**:
- Find domain records for tenant
- Delete domain records
- Verify deletion

**Implementation**:
```python
def rollback_domain_record(tenant_name):
    """Rollback domain record creation"""
    try:
        domains = frappe.get_all("SaaS Domain", 
            filters={"tenant": tenant_name})
        
        for domain in domains:
            frappe.delete_doc("SaaS Domain", domain.name)
        
        logger.info(f"Domain record rollback completed for {tenant_name}")
        return True
    except Exception as e:
        logger.error(f"Domain record rollback failed: {str(e)}")
        return False
```

### 4. Tenant Status Rollback
**Function**: `rollback_tenant_status(tenant_name)`
**Actions**:
- Update tenant status to Failed
- Add failure reason
- Save tenant record

**Implementation**:
```python
def rollback_tenant_status(tenant_name, failure_reason):
    """Rollback tenant status"""
    try:
        tenant = frappe.get_doc("SaaS Tenant", tenant_name)
        tenant.status = "Failed"
        tenant.failure_reason = failure_reason
        tenant.save(ignore_permissions=True)
        
        logger.info(f"Tenant status rollback completed for {tenant_name}")
        return True
    except Exception as e:
        logger.error(f"Tenant status rollback failed: {str(e)}")
        return False
```

### 5. Subscription Rollback
**Function**: `rollback_subscription(subscription_name)`
**Actions**:
- Update subscription status
- Set provisioned flag to 0
- Save subscription record

**Implementation**:
```python
def rollback_subscription(subscription_name):
    """Rollback subscription"""
    try:
        subscription = frappe.get_doc("SaaS Subscription", subscription_name)
        subscription.status = "Draft"
        subscription.provisioned = 0
        subscription.save(ignore_permissions=True)
        
        logger.info(f"Subscription rollback completed for {subscription_name}")
        return True
    except Exception as e:
        logger.error(f"Subscription rollback failed: {str(e)}")
        return False
```

## Rollback Integration Points

### Site Creation Rollback
**Location**: After line 331 in provisioning.py
```python
if result.returncode == 0:
    # Success handling
else:
    logger.error(f"Failed to create site {folder_name}: {result.stderr}")
    # Rollback
    rollback_database(folder_name)
    rollback_site_folder(folder_name)
    return False
```

### Provisioning Rollback
**Location**: After line 206 in provisioning.py
```python
except Exception as e:
    request.status = "Failed"
    request.last_message = frappe.get_traceback(with_context=True)
    request.save(ignore_permissions=True)
    
    # Rollback
    rollback_database(tenant.site_name)
    rollback_site_folder(tenant.site_name)
    rollback_domain_record(tenant.name)
    rollback_tenant_status(tenant.name, str(e))
    if request.subscription:
        rollback_subscription(request.subscription)
    
    logger.error("Provisioning failed for request %s", request_name)
    raise
```

## Rollback Testing

### Test Scenarios
1. **Database Creation Failure**: Test rollback when database creation fails
2. **Site Creation Failure**: Test rollback when site creation fails
3. **App Installation Failure**: Test rollback when app installation fails
4. **Configuration Failure**: Test rollback when configuration fails
5. **Network Failure**: Test rollback when network fails
6. **Timeout**: Test rollback when operation times out

### Rollback Verification
- Database deleted
- Database user deleted
- Site folder deleted
- Domain records deleted
- Tenant status updated
- Subscription status updated
- No orphaned data

## Rollback Best Practices

### 1. Atomic Operations
- Each rollback step should be independent
- Failure of one step should not prevent others
- Log each rollback step

### 2. Idempotent Operations
- Rollback should be safe to run multiple times
- Check existence before deletion
- Handle non-existent resources gracefully

### 3. Comprehensive Logging
- Log all rollback operations
- Log rollback failures
- Log rollback completion

### 4. Error Handling
- Handle rollback errors gracefully
- Continue rollback even if one step fails
- Report all rollback failures

### 5. Notification
- Notify administrators of rollback
- Include rollback details in notification
- Include failure reason in notification

## Rollback Recommendations

### Critical Priority
1. **Implement Database Rollback**: Add database deletion on failure
2. **Implement Site Folder Rollback**: Add folder deletion on failure
3. **Implement Tenant Status Rollback**: Add status update on failure
4. **Implement Domain Record Rollback**: Add domain deletion on failure

### High Priority
1. **Implement Subscription Rollback**: Add subscription rollback on failure
2. **Add Rollback Logging**: Log all rollback operations
3. **Add Rollback Testing**: Test rollback scenarios
4. **Add Rollback Verification**: Verify rollback completion

### Medium Priority
1. **Add Rollback Retry**: Retry failed rollback operations
2. **Add Rollback Notification**: Notify on rollback
3. **Add Rollback Audit**: Audit rollback operations
4. **Add Rollback Metrics**: Track rollback frequency

### Low Priority
1. **Add Rollback Automation**: Automate cleanup of old orphaned data
2. **Add Rollback Scheduling**: Schedule periodic orphaned data cleanup
3. **Add Rollback Monitoring**: Monitor rollback operations
4. **Add Rollback Reporting**: Generate rollback reports
