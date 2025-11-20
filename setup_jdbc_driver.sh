#!/bin/bash

# Script to download PostgreSQL JDBC driver for Logstash
# This driver is required for Logstash to read from the audit_log table

echo "Setting up PostgreSQL JDBC driver for Logstash..."

# Create directory for JDBC driver
mkdir -p app/docker/logstash/jdbc

# Change to the JDBC directory
cd app/docker/logstash/jdbc

# Download PostgreSQL JDBC driver (version 42.7.1)
echo "Downloading PostgreSQL JDBC driver..."
curl -L -o postgresql-42.7.1.jar https://jdbc.postgresql.org/download/postgresql-42.7.1.jar

# Verify download
if [ -f "postgresql-42.7.1.jar" ]; then
    echo "✓ JDBC driver downloaded successfully!"
    echo "  Location: app/docker/logstash/jdbc/postgresql-42.7.1.jar"
    echo "  Size: $(du -h postgresql-42.7.1.jar | cut -f1)"
else
    echo "✗ Error: Failed to download JDBC driver"
    exit 1
fi

echo ""
echo "Next steps:"
echo "1. Run the SQL script: psql -h localhost -U myuser -d thesisdb -f ../../setup_audit_triggers.sql"
echo "2. Restart Docker containers: cd app/docker && docker-compose restart logstash"
echo "3. Check Logstash logs: docker logs logstash"

