#!/bin/bash

# Script to download PostgreSQL JDBC driver for Logstash
# This driver is required for Logstash to read from the audit_log table

# Create directory for JDBC driver
mkdir -p app/docker/logstash/jdbc

# Change to the JDBC directory
cd app/docker/logstash/jdbc

# Download PostgreSQL JDBC driver (version 42.7.1)
curl -L -o postgresql-42.7.1.jar https://jdbc.postgresql.org/download/postgresql-42.7.1.jar

