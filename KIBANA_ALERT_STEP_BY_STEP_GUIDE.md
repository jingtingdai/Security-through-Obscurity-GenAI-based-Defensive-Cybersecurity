# Step-by-Step Guide: Create Kibana Alert for Unauthorized Access

This guide provides detailed instructions for creating a Kibana alert to detect unauthorized row access.

## Prerequisites

✅ Kibana is running at http://localhost:5601  
✅ Elasticsearch has security logs indexed  
✅ Index pattern `security-logs-*` exists  
✅ You have proper authentication  

## Part 1: Create Index Pattern for Security Logs

### Step 1: Access Kibana
1. Open browser: http://localhost:5601
2. Wait for Kibana to fully load

### Step 2: Navigate to Index Patterns
1. Click the **hamburger menu** (☰) in the top-left corner
2. Scroll down to **"Stack Management"** (under Management section)
3. Click **"Stack Management"**
4. In the left sidebar, click **"Index Patterns"**

### Step 3: Create New Index Pattern
1. Click the **"+ Create index pattern"** button (top-right)
2. **Index pattern name**: Enter `security-logs-*`
3. Click **"Next step"**

### Step 4: Configure Settings
1. **"Configure settings"** tab will open
2. Under **"Time field"**: Select `@timestamp` from the dropdown
3. Click **"Create index pattern"**

### Step 5: Verify
- You should see: "Success: The index pattern has been created"
- Index pattern `security-logs-*` should appear in the list

---

## Part 2: Create the Alert Connector (Index Type)

### Step 1: Navigate to Connectors
1. Click **hamburger menu** (☰)
2. Go to **Stack Management** → **Rules and Connectors**
3. Click **"Connectors"** tab (second tab at the top)

### Step 2: Create New Connector
1. Click **"+ Create connector"** button (top-right)
2. A modal will open with connector type options

### Step 3: Select Connector Type
Scroll down and select **"Index"** connector
- This stores alert results directly into Elasticsearch indices
- Perfect for logging security events

### Step 4: Configure Index Connector

#### 4.1 Basic Settings
- **Connector name**: `Security Alert Index Connector`
- **Index name**: Enter `security-alerts-%{+yyyy.MM.dd}`
  - This creates daily indices like `security-alerts-2024.01.15`
- **Description (optional)**: `Stores unauthorized access alerts in Elasticsearch`

#### 4.2 Document Settings
- Leave **"Document"** as is (this uses the alert context)
- The alert will automatically include:
  - Alert details
  - Triggered time
  - Query results
  - Any custom fields

#### 4.3 Test Connection
1. Click **"Test connector"** (bottom right)
2. You should see a success message
3. If successful, click **"Save connector"**
4. If failed, check Elasticsearch is running: `curl http://localhost:9200`

---

## Part 3: Create the Alert Rule

### Step 1: Navigate to Rules
1. In **Rules and Connectors**, click the **"Rules"** tab (first tab)
2. Click **"+ Create rule"** button (top-right)

### Step 2: Select Rule Type
You'll see multiple rule types. For unauthorized access detection, we'll use **"Log threshold"**:
- Click on **"Log threshold"** card
- Click **"Continue"**

### Step 3: Define the Rule

#### 3.1 Basic Information
- **Name**: `Unauthorized Row Access Detected`
- **Description**: `Alert when users access rows not in true_row_number list`
- **Tags**: `security, unauthorized-access, database`

#### 3.2 Query Builder
Scroll to **"Query"** section:

1. Select the **index pattern**: Click dropdown → select `security-logs-*`
2. Click in the query box
3. Enter the following KQL query:
```kql
tags: "unauthorized_access" AND tags: "security_alert"
```
4. Click **"Add filter"** (optional)
   - **Field**: `tags`
   - **Operator**: `is`
   - **Value**: `unauthorized_access`
   - Click **"Save"**

#### 3.3 Define Condition (Threshold)
1. **Alert me**: Select `Count`
2. **Document count**: Select `is`
3. **Threshold value**: Enter `0`
4. **Time window**: Select `Last`
5. **For**: Select `5` and `minutes`

**Meaning**: Alert triggers when there is ANY unauthorized access in the last 5 minutes

#### 3.4 Time Window
- **Check every**: `1` minute
- **Notify every**: `5` minutes (don't spam notifications)

### Step 4: Add Action (Index Connector)

1. Scroll to **"Actions"** section
2. Click **"Add action"**
3. In **"Action dropdown"**, select **"Serverlog"** or **"Index"** (whichever you created)
4. Configure the action:

#### Action Settings

**Name**: `Log to Index`

**Message** (what gets stored in the index):
```plaintext
🚨 Security Alert: Unauthorized Database Row Access Detected

Alert Details:
- Triggered at: {{context.date}}
- Number of unauthorized access attempts: {{context.hits}}

Most Recent Access:
- Timestamp: {{context.windowStart}}
- User: {{context.user}}
- Unauthorized Row Number: {{context.unauthorized_row}}
- Security Tag: {{context.tags}}

This alert indicates potential unauthorized data access.
Please investigate immediately.
```

### Step 5: Save and Enable

1. Scroll to bottom
2. Click **"Save and enable rule"** (if you want it active immediately)
   OR
   Click **"Save"** (to enable manually later)

3. Toggle the rule **ON** if disabled

---

## Part 4: Alternative - Create Index Action Template

If you want more detailed information in your indexed alerts, use this template:

### Action Configuration

**Name**: `Log Security Alert to Index`

**Document Template**:
```json
{
  "alert_type": "unauthorized_access",
  "timestamp": "{{context.date}}",
  "severity": "HIGH",
  "count": {{context.hits}},
  "message": "Unauthorized row access detected",
  "details": {
    "window_start": "{{context.windowStart}}",
    "window_end": "{{context.windowEnd}}",
    "group_by_terms": "{{context.group}",
    "user": "{{context.user}}",
    "unauthorized_row": "{{context.unauthorized_row}}"
  }
}
```

---

## Part 5: Verify the Alert

### Step 1: Check Rule Status
1. Go to **Rules and Connectors** → **Rules**
2. Find "Unauthorized Row Access Detected"
3. Check **"Status"** column:
   - Should show **"Active"**
4. Check **"Last run"**:
   - Should show recent timestamp or "Not started yet"

### Step 2: Test the Alert

Generate an unauthorized access event:

```bash
# Make sure your backend is running
# Get authentication token (adjust credentials)
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your_user","password":"your_pass"}'

# Save the token
TOKEN="your_jwt_token_here"

# Access an unauthorized row (not in true_row_number)
# For example, row 5 if true rows are [1, 11, 21, ...]
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/query-row/5
```

### Step 3: Check Alert Execution

1. Go back to **Rules and Connectors** → **Rules**
2. Refresh the page
3. Check **"Last run"** column - should show recent execution
4. If count > 0, alert should have triggered!

### Step 4: View Alert in Index

1. Go to **Discover** (left sidebar)
2. Select index: `security-alerts-2024.01.XX` (today's date)
3. You should see the alert document
4. Expand to see all details

---

## Part 6: Optional - Create Dashboard

### Step 1: Create New Dashboard
1. Click **hamburger menu** (☰)
2. Go to **Dashboard**
3. Click **"Create dashboard"**
4. Click **"Add panel"**

### Step 2: Add Security Logs Visualization
1. Select **"TSVB"** (Time Series Visual Builder)
2. **Source**: `security-logs-*`
3. Configure:
   - **Metrics**: Count
   - **Group by**: User (for unauthorized users)
4. Save panel as: `Unauthorized Access by User`

### Step 3: Add Timeline
1. **Add panel** → **Timeline**
2. **Index**: `security-logs-*`
3. Filter: `tags:"unauthorized_access"`
4. Save as: `Unauthorized Access Timeline`

### Step 4: Add Statistics
1. **Add panel** → **Markdown**
2. Add text displaying:
   - Total unauthorized access count
   - Last alert time
   - Most accessed unauthorized row

---

## Part 7: Monitor and Troubleshoot

### View Alert Execution History
1. Go to **Rules** tab
2. Click on your alert rule name
3. View **"History"** tab
4. See all execution attempts and results

### Check if Logs are Indexed

```bash
# Check recent security logs
curl 'http://localhost:9200/security-logs-*/_search?pretty&size=5&sort=@timestamp:desc'

# Check alert results
curl 'http://localhost:9200/security-alerts-*/_search?pretty'
```

### View Application Logs

```bash
# Check if unauthorized_access.log exists
tail -f app/backend/unauthorized_access.log

# Check Logstash is processing
docker-compose -f app/docker/docker-compose.yml logs logstash | grep security
```

---

## Troubleshooting

### Alert Not Triggering

**Problem**: Alert shows count = 0

**Solutions**:
1. Verify logs are being generated:
   ```bash
   tail -f app/backend/unauthorized_access.log
   ```

2. Check Elasticsearch has the data:
   ```bash
   curl 'http://localhost:9200/security-logs-*/_search?pretty&q=tags:unauthorized_access'
   ```

3. Verify query in Kibana:
   - Go to **Discover**
   - Select `security-logs-*`
   - Manually run query: `tags:"unauthorized_access"`
   - Should return results

4. Check rule status:
   - Ensure rule is **Enabled** (toggle ON)
   - Check **"Last run"** column for execution

### No Data in Index

**Problem**: `security-logs-*` index is empty

**Solutions**:
1. Check Logstash pipeline:
   ```bash
   docker-compose logs logstash | grep -i "security"
   ```

2. Verify file is being monitored:
   ```bash
   ls -lh app/backend/unauthorized_access.log
   ```

3. Restart Logstash:
   ```bash
   docker-compose restart logstash
   ```

### Connector Not Working

**Problem**: Index connector fails to store alerts

**Solutions**:
1. Test connector: **Connectors** tab → Test button
2. Check Elasticsearch is running:
   ```bash
   curl http://localhost:9200
   ```
3. Verify index permissions
4. Check index name format is correct

---

## Quick Reference Commands

```bash
# Start services
cd app/docker && docker-compose up -d

# Restart services
docker-compose restart kibana logstash

# Check logs
docker-compose logs -f kibana

# View security logs
tail -f app/backend/unauthorized_access.log

# Check Elasticsearch
curl 'http://localhost:9200/_cat/indices?v'

# Search security alerts
curl 'http://localhost:9200/security-alerts-*/_search?pretty'
```

---

## Summary

You've created:
1. ✅ Index pattern: `security-logs-*`
2. ✅ Connector: Index type (stores in `security-alerts-*` indices)
3. ✅ Alert rule: "Unauthorized Row Access Detected"
4. ✅ Action: Logs to index when triggered

The alert will:
- Monitor `security-logs-*` index
- Query for unauthorized access events
- Trigger when count > 0
- Store alert details in `security-alerts-*` index

---

## Next Steps

1. **Test the alert** by accessing an unauthorized row
2. **Create visualizations** to monitor security
3. **Set up notifications** (Email, Slack, Webhook)
4. **Review alerts** regularly
5. **Adjust threshold** if needed (e.g., alert after 3+ attempts)

