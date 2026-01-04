# Create Kibana Alert for Unauthorized Access

This guide provides detailed instructions for creating a Kibana alert to detect unauthorized access.

## Part 1: Create the Alert Rule

### Step 1: Navigate to Rules
1. Click **menu** (☰)
2. Go to **Stack Management** → **Alerts and Insights** 
3. Click the **"Rules"** tab
4. Click **"+ Create rule"** button

### Step 2: Select Rule Type
For unauthorized access detection, we'll use **"Elasticsearch query"**:


### Step 3: Define the Rule

#### 3.1 Basic Information
- **Name**: `audit_alert`
- **Select a data view**: `audit`

#### 3.2 Define your query

Define query as:
```kql
audit_app.keyword: exists AND NOT audit_app.keyword: frontend
 ```

#### 3.3 Define Condition (Threshold)
1. **WHEN**: `Count`
2. **OVER**: `all documents`
3. **IS ABOVE**: `0`
4. **FOR THE LAST**: `1 minute`

**Meaning**: Alert triggers when there is ANY unauthorized access in the last 1 minutes

#### 3.4 Time Window
- **Check every**: `1` minute


### Step 4: Add Action (Index Connector)

1. Scroll to **"Actions"** section
2. Click **"Add action"**
3. In **"Action dropdown"**, select **"Index"**
4. Configure the action:

#### Action Settings

**Name**: `Alert Index`

**Message** (what gets stored in the index):
```json
{
  "@timestamp": "{{date}}",
  "alert_name": "{{rule.name}}",
  "rule_id": "{{rule.id}}",
  "alert_id": "{{alert.id}}",
  "message": "{{context.message}}",
  "severity": "high"
}
```


---

## Part 2: Verify the Alert

### Step 1: Check Rule Status
1. Go to  **Rules**
2. Find "audit_alert"
3. Check **"State"** column:
   - Should show **"Enabled"**
4. Check **"Last run"**:
   - Should show recent timestamp or "Not started yet"

### Step 2: Test the Alert

Run CRUD operations directly from pgAdmin.

### Step 3: Check Alert Execution

1. Go back to **Alerts and Insights**  → **Alerts**
2. Refresh the page
3. Active alert should have triggered

### Step 4: View Alert in Index

1. Go to **Discover**
2. Select index: `Alert Index`
3. You should see the alert document
4. Expand to see all details


