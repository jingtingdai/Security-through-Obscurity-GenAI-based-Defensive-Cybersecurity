# Quick Start: PostgreSQL Audit Triggers with Logstash

## Prerequisites
- Docker and Docker Compose installed
- PostgreSQL database running (via Docker Compose)

## Setup Steps

### 1. Create Audit Triggers in PostgreSQL
```bash
psql -h localhost -U myuser -d thesisdb -f setup_audit_triggers.sql
```

### 2. Restart Logstash
```bash
cd app/docker
docker-compose restart logstash
```

### 3. Verify Setup

**Test the triggers:**
```sql
-- Connect to PostgreSQL
psql -h localhost -U myuser -d thesisdb

-- Test INSERT
INSERT INTO tablename (row_number, Shipment_ID, Origin_Warehouse) 
VALUES (9999, 'TEST001', 'WAREHOUSE_A');

-- Test UPDATE
UPDATE tablename SET Origin_Warehouse = 'WAREHOUSE_B' WHERE row_number = 9999;

-- Test DELETE
DELETE FROM tablename WHERE row_number = 9999;

-- Check audit log
SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10;
```


**Verify in Kibana:**
1. Open http://localhost:5601
2. Go to Discover
3. View the audit logs

## What Gets Logged

Every INSERT, UPDATE, and DELETE operation on monitored tables will log:
- Table name
- Operation type (INSERT/UPDATE/DELETE)
- Old data (for UPDATE/DELETE)
- New data (for INSERT/UPDATE)
- Changed fields (for UPDATE only)
- User name
- Application name
- Client IP address
- Transaction ID
- Timestamp
- Row identifier (primary key)


