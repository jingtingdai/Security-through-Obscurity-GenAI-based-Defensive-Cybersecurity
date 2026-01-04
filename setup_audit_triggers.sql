-- PostgreSQL Audit Trigger Setup Script
-- This script creates:
-- 1. An audit_log table to store all database changes
-- 2. A trigger function that logs INSERT, UPDATE, DELETE operations
-- 3. Triggers on your tables

-- Step 1: Create audit log table
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

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_audit_log_table_name ON audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_name ON audit_log(user_name);

-- Step 2: Create trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    old_json JSONB;
    new_json JSONB;
    changed_fields JSONB := '{}'::JSONB;
    row_id_value VARCHAR(255);
    table_pk_column VARCHAR(255);
    app_name VARCHAR(255);
BEGIN
    -- Skip INSERT operations from frontend application
    IF TG_OP = 'INSERT' THEN
        app_name := current_setting('application_name', true);
        IF app_name = 'frontend' THEN
            RETURN NEW;
        END IF;
    END IF;
    
    -- Determine the primary key column name
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

-- Step 3: Create triggers on existing tables
-- Drop existing triggers if they exist (to allow re-running this script)
DROP TRIGGER IF EXISTS tablename ON tablename; -- Replace tablename with the name of the table you want to audit
DROP TRIGGER IF EXISTS audit_trigger_users ON "Users";

-- Create trigger on table
CREATE TRIGGER audit_trigger_tablename
    AFTER INSERT OR UPDATE OR DELETE ON tablename
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

-- Create trigger on Users table
CREATE TRIGGER audit_trigger_users
    AFTER INSERT OR UPDATE OR DELETE ON "Users"
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger_function();

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Audit triggers have been successfully created!';
    RAISE NOTICE 'Triggers are active on: tablename, Users';
END $$;

