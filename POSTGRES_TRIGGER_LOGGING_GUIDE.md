# PostgreSQL Trigger Function Logging Guide

This guide explains how to set up trigger functions in PostgreSQL to log all INSERT, UPDATE, and DELETE operations, and configure Logstash to ingest these logs.

## Overview

We'll create:
1. An audit log table to store all database changes
2. A trigger function that logs INSERT, UPDATE, and DELETE operations
3. Triggers on your tables to call this function
4. Logstash JDBC input to read from the audit table

## Step 1: Create Audit Log Table

Connect to your PostgreSQL database and run the following SQL:

```sql
-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255) NOT NULL,
    operation VARCHAR(10) NOT NULL, -- 'INSERT', 'UPDATE', or 'DELETE'
    old_data JSONB,
    new_data JSONB,
    changed_fields JSONB, -- For UPDATE operations, shows what changed
    user_name VARCHAR(255),
    application_name VARCHAR(255),
    client_address INET,
    transaction_id BIGINT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    row_id VARCHAR(255) -- Primary key or identifier of the affected row
);

-- Create index for better query performance
CREATE INDEX idx_audit_log_table_name ON audit_log(table_name);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_log_operation ON audit_log(operation);
CREATE INDEX idx_audit_log_user_name ON audit_log(user_name);
```

## Step 2: Create Trigger Function

Create a universal trigger function that works for any table:

```sql
-- Create trigger function for logging INSERT, UPDATE, DELETE
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    old_json JSONB;
    new_json JSONB;
    changed_fields JSONB := '{}'::JSONB;
    row_id_value VARCHAR(255);
    table_pk_column VARCHAR(255);
BEGIN
    -- Determine the primary key column name
    -- This assumes your tables have a primary key
    SELECT column_name INTO table_pk_column
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    WHERE tc.table_name = TG_TABLE_NAME
        AND tc.constraint_type = 'PRIMARY KEY'
    LIMIT 1;
    
    -- Convert OLD and NEW records to JSONB
    IF TG_OP = 'DELETE' THEN
        old_json := to_jsonb(OLD);
        new_json := NULL;
        -- Get row identifier
        IF table_pk_column IS NOT NULL THEN
            EXECUTE format('SELECT ($1).%I', table_pk_column) INTO row_id_value USING OLD;
        ELSE
            row_id_value := NULL;
        END IF;
    ELSIF TG_OP = 'UPDATE' THEN
        old_json := to_jsonb(OLD);
        new_json := to_jsonb(NEW);
        -- Get row identifier
        IF table_pk_column IS NOT NULL THEN
            EXECUTE format('SELECT ($1).%I', table_pk_column) INTO row_id_value USING NEW;
        ELSE
            row_id_value := NULL;
        END IF;
        
        -- Calculate changed fields for UPDATE
        SELECT jsonb_object_agg(key, jsonb_build_object('old', old_json->key, 'new', new_json->key))
        INTO changed_fields
        FROM jsonb_each(new_json)
        WHERE (old_json->key) IS DISTINCT FROM (new_json->key);
    ELSIF TG_OP = 'INSERT' THEN
        old_json := NULL;
        new_json := to_jsonb(NEW);
        -- Get row identifier
        IF table_pk_column IS NOT NULL THEN
            EXECUTE format('SELECT ($1).%I', table_pk_column) INTO row_id_value USING NEW;
        ELSE
            row_id_value := NULL;
        END IF;
    END IF;
    
    -- Insert audit log record
    INSERT INTO audit_log (
        table_name,
        operation,
        old_data,
        new_data,
        changed_fields,
        user_name,
        application_name,
        client_address,
        transaction_id,
        row_id
    ) VALUES (
        TG_TABLE_NAME,
        TG_OP,
        old_json,
        new_json,
        changed_fields,
        current_user,
        current_setting('application_name', true),
        inet_client_addr(),
        txid_current(),
        row_id_value
    );
    
    -- Return appropriate record
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;
```

## Step 3: Create Triggers on Your Tables

Apply the trigger to your tables. Here are examples for your existing tables:

```sql
-- Create trigger on test1021 table
CREATE TRIGGER audit_trigger_test1021
    AFTER INSERT OR UPDATE OR DELETE ON test1021
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

-- Create trigger on Users table
CREATE TRIGGER audit_trigger_users
    AFTER INSERT OR UPDATE OR DELETE ON "Users"
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

-- If you have other tables, create triggers for them too:
-- CREATE TRIGGER audit_trigger_<table_name>
--     AFTER INSERT OR UPDATE OR DELETE ON <table_name>
--     FOR EACH ROW
--     EXECUTE FUNCTION audit_trigger_function();
```

## Step 4: Install JDBC Driver for Logstash

You need to add the PostgreSQL JDBC driver to Logstash. Create a directory structure and download the driver:

1. Create a directory for JDBC drivers in your Logstash setup:

```bash
mkdir -p app/docker/logstash/jdbc
```

2. Download the PostgreSQL JDBC driver:

```bash
cd app/docker/logstash/jdbc
wget https://jdbc.postgresql.org/download/postgresql-42.7.1.jar
```

Or manually download from: https://jdbc.postgresql.org/download/

## Step 5: Update Docker Compose for Logstash

Update your `docker-compose.yml` to mount the JDBC driver:

```yaml
logstash:
  image: docker.elastic.co/logstash/logstash:8.14.3
  container_name: logstash
  depends_on:
    - elasticsearch
  volumes:
    - ./logstash/pipeline:/usr/share/logstash/pipeline
    - ./logs:/logs
    - ../app/backend:/app/logs
    - ./logstash/jdbc:/usr/share/logstash/vendor/jdbc  # Add JDBC driver
  ports:
    - "5044:5044"
    - "9600:9600"
  environment:
    - LS_JAVA_OPTS=-Xmx512m -Xms512m
  networks:
    - thesis-net
```

## Step 6: Update Logstash Configuration

Add JDBC input to your `logstash.conf` to read from the audit_log table. Here's the updated configuration:

```ruby
input {
  beats {
    port => 5044
  }
  file {
    path => "/logs/postgresql.log"
    start_position => "beginning"
    sincedb_path => "/dev/null"
    type => "postgresql"
  }
  file {
    path => "/app/logs/unauthorized_access.log"
    start_position => "beginning"
    sincedb_path => "/dev/null"
    type => "security"
    codec => "plain"
  }
  
  # JDBC input for audit_log table
  jdbc {
    jdbc_connection_string => "jdbc:postgresql://postgres:5432/thesisdb"
    jdbc_user => "myuser"
    jdbc_password => "mypassword"
    jdbc_driver_library => "/usr/share/logstash/vendor/jdbc/postgresql-42.7.1.jar"
    jdbc_driver_class => "org.postgresql.Driver"
    jdbc_paging_enabled => true
    jdbc_page_size => 50000
    statement => "SELECT * FROM audit_log WHERE timestamp > :sql_last_value ORDER BY timestamp ASC"
    schedule => "*/5 * * * *"  # Run every 5 minutes
    type => "audit_log"
    use_column_value => true
    tracking_column => "timestamp"
    tracking_column_type => "timestamp"
    last_run_metadata_path => "/usr/share/logstash/.logstash_jdbc_last_run_audit"
    clean_run => false
  }
}

filter {
  # ... existing filters ...
  
  # Filter for audit log entries
  if [type] == "audit_log" {
    mutate {
      add_tag => ["database_audit", "trigger_log"]
      rename => {
        "table_name" => "audit_table"
        "operation" => "audit_operation"
        "user_name" => "audit_user"
        "application_name" => "audit_app"
        "client_address" => "audit_client"
        "transaction_id" => "audit_transaction_id"
        "row_id" => "audit_row_id"
      }
    }
    
    # Parse JSONB fields if they exist
    if [old_data] {
      mutate {
        add_field => { "has_old_data" => "true" }
      }
    }
    
    if [new_data] {
      mutate {
        add_field => { "has_new_data" => "true" }
      }
    }
    
    if [changed_fields] and [changed_fields] != "{}" {
      mutate {
        add_field => { "has_changes" => "true" }
      }
    }
    
    # Add specific tags based on operation
    if [audit_operation] == "INSERT" {
      mutate {
        add_tag => ["insert_operation"]
      }
    } else if [audit_operation] == "UPDATE" {
      mutate {
        add_tag => ["update_operation"]
      }
    } else if [audit_operation] == "DELETE" {
      mutate {
        add_tag => ["delete_operation"]
      }
    }
  }
}

output {
  # ... existing outputs ...
  
  # Output audit logs to Elasticsearch
  if "database_audit" in [tags] {
    elasticsearch {
      hosts => ["http://elasticsearch:9200"]
      index => "postgres-audit-logs-%{+YYYY.MM.dd}"
    }
  }
  
  # ... rest of outputs ...
}
```

## Step 7: Test the Setup

1. **Restart your Docker containers:**
```bash
cd app/docker
docker-compose down
docker-compose up -d
```

2. **Test the trigger by performing operations:**
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

3. **Verify in Kibana:**
   - Open Kibana at http://localhost:5601
   - Go to Discover
   - Select index pattern: `postgres-audit-logs-*`
   - You should see the audit log entries

## Step 8: Apply to All Tables (Optional)

To automatically create triggers for all existing tables, you can use this script:

```sql
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public' 
        AND tablename NOT IN ('audit_log', 'schema_migrations')  -- Exclude audit log itself
    LOOP
        EXECUTE format('
            DROP TRIGGER IF EXISTS audit_trigger_%I ON %I;
            CREATE TRIGGER audit_trigger_%I
                AFTER INSERT OR UPDATE OR DELETE ON %I
                FOR EACH ROW
                EXECUTE FUNCTION audit_trigger_function();
        ', r.tablename, r.tablename, r.tablename, r.tablename);
        
        RAISE NOTICE 'Created trigger for table: %', r.tablename;
    END LOOP;
END $$;
```

## Troubleshooting

1. **JDBC driver not found:**
   - Ensure the JDBC driver is in the correct path: `/usr/share/logstash/vendor/jdbc/`
   - Check Logstash logs: `docker logs logstash`

2. **Triggers not firing:**
   - Verify triggers exist: `SELECT * FROM pg_trigger WHERE tgname LIKE 'audit_trigger%';`
   - Check PostgreSQL logs for errors

3. **No data in Elasticsearch:**
   - Check Logstash logs: `docker logs logstash`
   - Verify JDBC connection settings
   - Check if `sql_last_value` file exists and has correct permissions

4. **Performance concerns:**
   - The audit log table can grow large. Consider:
     - Adding a retention policy (delete old records)
     - Partitioning the audit_log table by date
     - Archiving old records

## Maintenance

### Clean up old audit logs (optional):

```sql
-- Delete audit logs older than 90 days
DELETE FROM audit_log 
WHERE timestamp < NOW() - INTERVAL '90 days';
```

### Monitor audit log size:

```sql
SELECT 
    COUNT(*) as total_records,
    pg_size_pretty(pg_total_relation_size('audit_log')) as table_size
FROM audit_log;
```

## Summary

You now have:
- ✅ An audit_log table to store all database changes
- ✅ A trigger function that logs INSERT, UPDATE, DELETE operations
- ✅ Triggers on your tables
- ✅ Logstash configured to read audit logs via JDBC
- ✅ Audit logs indexed in Elasticsearch for analysis in Kibana

The audit logs will include:
- Table name and operation type
- Old and new data (as JSONB)
- Changed fields (for UPDATE operations)
- User, application, client IP
- Transaction ID and timestamp
- Row identifier

