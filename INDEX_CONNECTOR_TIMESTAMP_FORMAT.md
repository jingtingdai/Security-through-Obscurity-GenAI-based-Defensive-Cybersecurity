# Index Connector Timestamp Format (UTC)

## Current Format

Your current timestamp format:
```json
{
  "@timestamp": "{{context.date}}"
}
```

This produces: `YYYY-MM-DDTHH:mm:ss.sssZ` format (already UTC)

## Issue

The `{{context.date}}` variable might not always be in the exact format needed, or you want to ensure it's explicitly formatted as UTC.

## Solutions

### Option 1: Use @timestamp Field Directly (Recommended)

If you want to use the timestamp from the matched document:

```json
{
  "@timestamp": "{{context.hits.hits.0._source.@timestamp}}"
}
```

This uses the timestamp from the first matching document.

### Option 2: Format Current Date as UTC

For Kibana index connectors, you can format the date explicitly:

```json
{
  "@timestamp": "{{date}}"
}
```

Or with explicit UTC formatting:

```json
{
  "@timestamp": "{{date 'YYYY-MM-DDTHH:mm:ss.SSS[Z]'}}"
}
```

### Option 3: Use ISO 8601 Format

```json
{
  "@timestamp": "{{date 'ISO8601'}}"
}
```

### Option 4: Manual UTC Format (Most Reliable)

```json
{
  "@timestamp": "{{date 'yyyy-MM-ddTHH:mm:ss.SSSZ'}}"
}
```

Note: Use lowercase `yyyy` for year in date formatting.

## Complete Document Example

### Recommended Format

```json
{
  "@timestamp": "{{date 'yyyy-MM-ddTHH:mm:ss.SSSZ'}}",
  "alert_name": "{{context.rule.name}}",
  "rule_id": "{{rule.id}}",
  "alert_id": "{{alert.id}}",
  "message": "{{context.message}}",
  "severity": "high",
  "source": {
    "user": "{{context.hits.hits.0._source.user}}",
    "app": "{{context.hits.hits.0._source.app}}",
    "database": "{{context.hits.hits.0._source.db}}",
    "client_ip": "{{context.hits.hits.0._source.client}}"
  },
  "matched_documents": "{{context.hits.total.value}}"
}
```

### Alternative: Use Document Timestamp

If you want to use the timestamp from the matched document (which is already in UTC):

```json
{
  "@timestamp": "{{context.hits.hits.0._source.@timestamp}}",
  "alert_name": "{{context.rule.name}}",
  "rule_id": "{{rule.id}}",
  "alert_id": "{{alert.id}}",
  "message": "{{context.message}}",
  "source": {
    "user": "{{context.hits.hits.0._source.user}}",
    "app": "{{context.hits.hits.0._source.app}}"
  }
}
```

## Date Format Patterns

Available format patterns (use lowercase for year):

| Pattern | Example Output | Notes |
|---------|---------------|-------|
| `yyyy-MM-ddTHH:mm:ss.SSSZ` | `2025-11-12T14:30:45.123Z` | Full UTC with milliseconds |
| `yyyy-MM-ddTHH:mm:ssZ` | `2025-11-12T14:30:45Z` | UTC without milliseconds |
| `yyyy-MM-dd HH:mm:ss` | `2025-11-12 14:30:45` | Without timezone (not recommended) |
| `ISO8601` | `2025-11-12T14:30:45.123Z` | ISO 8601 format |

## How to Update

1. **Go to**: Kibana → Stack Management → Connectors
2. **Find**: `app_index` connector
3. **Edit** → **Document** section
4. **Update** the `@timestamp` field to one of the formats above
5. **Save**

## Testing

After updating, test by:

1. **Trigger an alert** (or wait for it to trigger)
2. **Check the indexed document**:
   ```bash
   curl "http://localhost:9200/alerts-*/_search?pretty&sort=@timestamp:desc" | head -50
   ```
3. **Verify timestamp format**:
   - Should be: `2025-11-12T14:30:45.123Z`
   - Should end with `Z` (UTC indicator)
   - Should be parseable by Elasticsearch

## Important Notes

1. **UTC Indicator**: The `Z` at the end indicates UTC timezone
2. **Elasticsearch**: Automatically parses ISO 8601 timestamps
3. **Date Format**: Use lowercase `yyyy` (not `YYYY`) for year
4. **Time Field**: Make sure your index pattern has `@timestamp` as the time field

## Troubleshooting

If timestamp is not in UTC:

1. **Check the format**: Ensure it ends with `Z`
2. **Verify date function**: Use `{{date 'yyyy-MM-ddTHH:mm:ss.SSSZ'}}`
3. **Check Elasticsearch mapping**: The `@timestamp` field should be `date` type
4. **Test format**: Try a simple format first: `{{date}}`

## Example: Your Current Document Structure

Update from:
```json
{
  "@timestamp": "{{context.date}}",
  "rule_id": "{{rule.id}}",
  "rule_name": "{{rule.name}}",
  "alert_id": "{{alert.id}}",
  "context_message": "{{context.message}}",
  "app": "{{context.app}}"
}
```

To:
```json
{
  "@timestamp": "{{date 'yyyy-MM-ddTHH:mm:ss.SSSZ'}}",
  "rule_id": "{{rule.id}}",
  "rule_name": "{{rule.name}}",
  "alert_id": "{{alert.id}}",
  "context_message": "{{context.message}}",
  "app": "{{context.app}}"
}
```

This ensures the timestamp is explicitly formatted as UTC in the required format.

