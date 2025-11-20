# Quick Start: PostgreSQL Audit Triggers with Logstash

## Prerequisites
- Docker and Docker Compose installed
- PostgreSQL database running (via Docker Compose)
- Access to the database

## Setup Steps

### 1. Download JDBC Driver
```bash
./setup_jdbc_driver.sh
```

Or manually:
```bash
mkdir -p app/docker/logstash/jdbc
cd app/docker/logstash/jdbc
wget https://jdbc.postgresql.org/download/postgresql-42.7.1.jar
```

### 2. Create Audit Triggers in PostgreSQL
```bash
psql -h localhost -U myuser -d thesisdb -f setup_audit_triggers.sql
```

Or connect to PostgreSQL and run the SQL manually:
```bash
psql -h localhost -U myuser -d thesisdb
\i setup_audit_triggers.sql
```

### 3. Restart Logstash
```bash
cd app/docker
docker-compose restart logstash
```

Or restart all services:
```bash
cd app/docker
docker-compose down
docker-compose up -d
```

### 4. Verify Setup

**Test the triggers:**
```sql
-- Connect to PostgreSQL
psql -h localhost -U myuser -d thesisdb

-- Test INSERT
INSERT INTO test1021 (row_number, Shipment_ID, Origin_Warehouse) 
VALUES (9999, 'TEST001', 'WAREHOUSE_A');

-- Test UPDATE
UPDATE test1021 SET Origin_Warehouse = 'WAREHOUSE_B' WHERE row_number = 9999;

-- Test DELETE
DELETE FROM test1021 WHERE row_number = 9999;

-- Check audit log
SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10;
```

**Check Logstash logs:**
```bash
docker logs logstash
```

**Verify in Kibana:**
1. Open http://localhost:5601
2. Go to Discover
3. Create index pattern: `postgres-audit-logs-*`
4. View the audit logs

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

## Files Modified

- ✅ `app/docker/logstash/pipeline/logstash.conf` - Added JDBC input and filters
- ✅ `app/docker/docker-compose.yml` - Added JDBC driver volume mount
- ✅ `setup_audit_triggers.sql` - SQL script to create triggers
- ✅ `setup_jdbc_driver.sh` - Script to download JDBC driver

## Troubleshooting

**JDBC driver not found:**
- Ensure `postgresql-42.7.1.jar` is in `app/docker/logstash/jdbc/`
- Check Logstash logs: `docker logs logstash | grep -i jdbc`

**No audit logs appearing:**
- Verify triggers exist: `SELECT * FROM pg_trigger WHERE tgname LIKE 'audit_trigger%';`
- Check if data exists in `audit_log` table
- Verify Logstash JDBC connection in logs

**Logstash not reading from audit_log:**
- Check JDBC connection string matches your database settings
- Verify database credentials are correct
- Check `sql_last_value` file exists: `docker exec logstash ls -la /usr/share/logstash/.logstash_jdbc_last_run_audit`

## Next Steps

- Monitor audit log table size: `SELECT COUNT(*), pg_size_pretty(pg_total_relation_size('audit_log')) FROM audit_log;`
- Set up retention policy for old audit logs
- Create Kibana dashboards for audit log analysis
- Set up alerts for suspicious operations

