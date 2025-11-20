# Fix Index Name Format Error

## Error

```
error indexing documents: Invalid index name [alerts-%{+YYYY.MM.dd}], must be lowercase
```

## Problem

Elasticsearch index names must be **lowercase only**. The date format pattern `%{+YYYY.MM.dd}` contains uppercase letters (`YYYY`), which is invalid.

## Solution

Use **lowercase** date format patterns. Here are the correct formats:

### Correct Index Name Patterns

#### Daily Indices (Recommended)
```
alerts-%{date:yyyy.MM.dd}
```
Creates: `alerts-2025.11.12`, `alerts-2025.11.13`, etc.

#### Alternative Daily Format
```
alerts-%{+yyyy.MM.dd}
```

#### Monthly Indices
```
alerts-%{date:yyyy.MM}
```
Creates: `alerts-2025.11`, `alerts-2025.12`, etc.

#### Weekly Indices
```
alerts-%{date:yyyy.ww}
```

#### Single Index (No Date)
```
alerts
```

## How to Fix

### In Kibana UI

1. **Go to**: Stack Management → Connectors
2. **Find**: `app_index` connector
3. **Edit** → **Index name** field
4. **Change from**: `alerts-%{+YYYY.MM.dd}` ❌
5. **Change to**: `alerts-%{date:yyyy.MM.dd}` ✅
6. **Save**

### Available Date Format Variables

In Kibana index connectors, you can use:

- `{{date}}` - Current date/time
- `{{date:yyyy.MM.dd}}` - Date format: 2025.11.12
- `{{date:yyyy-MM-dd}}` - Date format: 2025-11-12
- `{{date:yyyy.MM}}` - Month format: 2025.11
- `{{date:yyyy}}` - Year format: 2025

### Examples

| Pattern | Result | Notes |
|---------|--------|-------|
| `alerts-%{date:yyyy.MM.dd}` | `alerts-2025.11.12` | Daily indices |
| `alerts-%{date:yyyy-MM-dd}` | `alerts-2025-11-12` | Daily with hyphens |
| `alerts-%{date:yyyy.MM}` | `alerts-2025.11` | Monthly indices |
| `security-alerts-%{date:yyyy.MM.dd}` | `security-alerts-2025.11.12` | Custom prefix |
| `alerts` | `alerts` | Single index |

## Alternative: Using Mustache Template Syntax

Some Kibana versions use Mustache syntax:

```
alerts-{{date:yyyy.MM.dd}}
```

Or:

```
alerts-{{date 'yyyy.MM.dd'}}
```

## Testing

After updating, test by:

1. **Trigger your alert** (or wait for it to trigger)
2. **Check if index was created**:
   ```bash
   curl "http://localhost:9200/_cat/indices/alerts-*?v"
   ```
3. **Verify document was indexed**:
   ```bash
   curl "http://localhost:9200/alerts-*/_search?pretty" | head -50
   ```

## Common Mistakes

❌ **Wrong**:
- `alerts-%{+YYYY.MM.dd}` - Uppercase YYYY
- `alerts-%{YYYY.MM.dd}` - Uppercase YYYY
- `Alerts-%{date:yyyy.MM.dd}` - Uppercase A

✅ **Correct**:
- `alerts-%{date:yyyy.MM.dd}` - All lowercase
- `alerts-%{+yyyy.MM.dd}` - All lowercase
- `security-alerts-%{date:yyyy.MM.dd}` - All lowercase

## Quick Fix

**Change your index name to**:
```
alerts-%{date:yyyy.MM.dd}
```

This will create daily indices like:
- `alerts-2025.11.12`
- `alerts-2025.11.13`
- etc.

All lowercase, which is what Elasticsearch requires!

