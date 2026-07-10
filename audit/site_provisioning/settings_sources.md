# Settings Sources Analysis

## Database Configuration Settings

### MariaDB Root Password
**Source**: SaaS Settings DocType
**Field**: `mariadb_root_password`
**File**: `erpgenex_saas/doctype/saas_settings/saas_settings.json`
**Lines**: 98-105
```json
{
  "fieldname": "mariadb_root_password",
  "fieldtype": "Password",
  "label": "MariaDB Root Password",
  "default": "Microhard2610",
  "description": "MariaDB root password for site creation (only visible to System Manager)",
  "read_only": 0,
  "hidden": 0,
  "no_copy": 1,
  "password": 1
}
```

**Retrieval Method**: Via PasswordManager service
**File**: `erpgenex_saas/services/password_manager.py`
**Function**: `get_mariadb_root_password()`
**Lines**: 47-56
```python
def get_mariadb_root_password(self):
    """Get MariaDB root password from SaaS Settings"""
    try:
        saas_settings = frappe.get_single("SaaS Settings")
        password = saas_settings.mariadb_root_password
        if not password:
            # Fallback to default
            password = "Microhard2610"
        return password
    except Exception as e:
        self.logger.error(f"Failed to get MariaDB root password: {str(e)}")
        return "Microhard2610"
```

**Usage in Provisioning**: Line 243 in provisioning.py
```python
mariadb_root_password = password_manager.get_mariadb_root_password()
```

### Database Password
**Source**: SaaS Settings DocType
**Field**: `database_password`
**File**: `erpgenex_saas/doctype/saas_settings/saas_settings.json`
**Lines**: 87-96
```json
{
  "fieldname": "database_password",
  "fieldtype": "Password",
  "label": "Database Password",
  "default": "Microhard2610",
  "description": "Default password for new sites (only visible to System Manager)",
  "read_only": 0,
  "hidden": 0,
  "no_copy": 1,
  "password": 1
}
```

**Retrieval Method**: Via PasswordManager service
**File**: `erpgenex_saas/services/password_manager.py`
**Function**: `get_db_password()`
**Lines**: 33-45
```python
def get_db_password(self):
    """Get database password from SaaS Settings"""
    try:
        saas_settings = frappe.get_single("SaaS Settings")
        password = saas_settings.database_password
        if not password:
            # Fallback to default
            password = "Microhard2610"
        return password
    except Exception as e:
        self.logger.error(f"Failed to get database password: {str(e)}")
        return "Microhard2610"
```

**Usage in Provisioning**: Line 242 in provisioning.py
```python
database_password = password_manager.get_db_password()
```

### DB Host
**Source**: Not explicitly configured in SaaS Settings
**Default**: localhost (Frappe default)
**Status**: ❌ Not configurable via SaaS Settings
**Recommendation**: Add to SaaS Settings for flexibility

### DB Port
**Source**: Not explicitly configured in SaaS Settings
**Default**: 3306 (MariaDB default)
**Status**: ❌ Not configurable via SaaS Settings
**Recommendation**: Add to SaaS Settings for flexibility

## Server Configuration Settings

### Server IP
**Source**: SaaS Settings DocType
**Field**: `server_ip`
**File**: `erpgenex_saas/doctype/saas_settings/saas_settings.json`
**Lines**: 41-46
```json
{
  "fieldname": "server_ip",
  "fieldtype": "Data",
  "label": "Server IP",
  "default": "192.168.1.2",
  "description": "Server IP address for sites"
}
```

**Usage in Provisioning**: Line 238 in provisioning.py
```python
server_ip = saas_settings.server_ip or "192.168.1.2"
```

### Server Port
**Source**: SaaS Settings DocType
**Field**: `server_port`
**File**: `erpgenex_saas/doctype/saas_settings/saas_settings.json`
**Lines**: 48-53
```json
{
  "fieldname": "server_port",
  "fieldtype": "Int",
  "label": "Server Port",
  "default": "8088",
  "description": "Server port for sites"
}
```

**Usage in Provisioning**: Line 239 in provisioning.py
```python
server_port = saas_settings.server_port or "8088"
```

### Platform Domain
**Source**: SaaS Settings DocType
**Field**: `platform_domain`
**File**: `erpgenex_saas/doctype/saas_settings/saas_settings.json`
**Lines**: 35-39
```json
{
  "fieldname": "platform_domain",
  "fieldtype": "Data",
  "label": "Platform Domain",
  "default": "erpgenex.com"
}
```

**Usage in Provisioning**: Lines 91, 101, 221 in provisioning.py

## Port Configuration Settings

### Base Port
**Source**: SaaS Settings DocType
**Field**: `base_port`
**File**: `erpgenex_saas/doctype/saas_settings/saas_settings.json`
**Lines**: 63-69
```json
{
  "fieldname": "base_port",
  "fieldtype": "Int",
  "label": "Base Port",
  "default": "8001",
  "depends_on": "eval:doc.site_distribution_method == 'Port'",
  "description": "Starting port number for port-based distribution (port 80 reserved for main site)"
}
```

### Max Port
**Source**: SaaS Settings DocType
**Field**: `max_port`
**File**: `erpgenex_saas/doctype/saas_settings/saas_settings.json`
**Lines**: 71-77
```json
{
  "fieldname": "max_port",
  "fieldtype": "Int",
  "label": "Max Port",
  "default": "8888",
  "depends_on": "eval:doc.site_distribution_method == 'Port'",
  "description": "Maximum port number for sites (8000-8888)"
}
```

### Port Increment
**Source**: SaaS Settings DocType
**Field**: `port_increment`
**File**: `erpgenex_saas/doctype/saas_settings/saas_settings.json`
**Lines**: 79-85
```json
{
  "fieldname": "port_increment",
  "fieldtype": "Int",
  "label": "Port Increment",
  "default": "1",
  "depends_on": "eval:doc.site_distribution_method == 'Port'",
  "description": "Increment port by this number for each new site"
}
```

## Issues Identified

### Critical Issues
None - All settings are correctly sourced from SaaS Settings

### Medium Issues
1. **DB Host/Port Not Configurable**: Database host and port are not configurable via SaaS Settings
2. **Hardcoded Defaults**: Some defaults are hardcoded in code instead of settings

### Low Issues
1. **Default Domain Mismatch**: Default in JSON is "erpgenex.com" but actual is "erpgenex.local"
2. **Missing Validation**: No validation of settings values before use

## Recommendations

### High Priority
1. Add DB Host and DB Port to SaaS Settings
2. Add validation for all settings values
3. Fix default domain to match actual usage

### Medium Priority
1. Add settings documentation
2. Add settings import/export functionality
3. Add settings versioning

### Low Priority
1. Add settings change history
2. Add settings backup/restore
3. Add settings template system
