---
description: Generate business logic specification for a specific endpoint
args:
  - name: api_name
    description: API name from gospelo-config.yaml
    required: true
  - name: method
    description: HTTP method (GET, POST, PUT, DELETE, PATCH)
    required: true
  - name: path
    description: Endpoint path
    required: true
---

# Generate Business Logic Specification

Generate comprehensive business logic specification for a specific FastAPI endpoint.

## Usage

```bash
/gospelo-fastapi-analize <api_name> <method> <path>
```

## Examples

```bash
/spec streaming POST /stream
/spec bff POST /api/v1/tenant/users/cognito/sync/batch
/spec bff GET /api/v1/tenant/users
```

## What This Does

1. **Analyzes the endpoint** specified by API name, HTTP method, and path
2. **Discovers services** used by the endpoint through AST analysis
3. **Generates specification** including:
   - Endpoint overview and purpose
   - Request/response schemas
   - Business logic flow
   - Service dependencies
   - Data transformations
   - Error handling

## How to Execute

Run this using Python with the MCP HTTP Client:

```python
PYTHONPATH=/Users/gorosun/projects/gorosun/gospelo-fastapi/src python3 << 'EOF'
from gospelo_fastapi.mcp_http_client import MCPHttpClient

with MCPHttpClient() as client:
    # Call the business logic spec generation tool
    result = client.call_tool(
        "fastapi_generate_business_logic_spec",
        {
            "api_name": "{{api_name}}",
            "method": "{{method}}",
            "path": "{{path}}"
        }
    )

    print(result[0]["text"])
EOF
```

## Generated Files

Specification is created in:

```
docs/api/<api_name>/specs/business-logic/<method>_<sanitized_path>.md
```

Example:
```
docs/api/streaming/specs/business-logic/POST_stream.md
docs/api/bff/specs/business-logic/POST_api_v1_tenant_users_cognito_sync_batch.md
```

## Prerequisites

Make sure the Remote MCP Server is running:

```bash
# Check server status
gospelo-fastapi health

# Start server if not running
gospelo-fastapi start --port 8766 &
```

---

**Updated**: 2025-11-23
**Version**: 2.0.0 (Simplified)