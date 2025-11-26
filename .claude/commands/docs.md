---
description: Generate API documentation using gospelo-fastapi CLI
args:
  - name: api_name
    description: API name from gospelo-config.yaml (optional - generates all enabled APIs if omitted)
    required: false
---

# Generate API Documentation

Generate comprehensive API documentation using the `gospelo-fastapi docs` command.

## Usage

```bash
# Generate docs for a specific API
/gospelo-fastapi-docs <api_name>

# Generate docs for all enabled APIs
/gospelo-fastapi-docs
```

## Examples

```bash
/gospelo-fastapi-docs bff          # Generate documentation for bff API
/gospelo-fastapi-docs streaming    # Generate documentation for streaming API
/gospelo-fastapi-docs              # Generate docs for all enabled APIs
```

## What You Need to Do

{{#if api_name}}
### Single API Generation

Run the following command using the Bash tool:

```bash
gospelo-fastapi docs {{api_name}}
```

This will:
1. Start documentation generation for the `{{api_name}}` API
2. Return a session ID for tracking progress
3. Generate documentation in `docs/api/{{api_name}}/`

{{else}}
### All APIs Generation

1. **Get list of enabled APIs:**
   ```bash
   gospelo-fastapi list
   ```

2. **Use TodoWrite to create tasks** for each enabled API

3. **Generate docs for each API:**
   ```bash
   gospelo-fastapi docs <api_name>
   ```

4. **Update TODO status** after each API completes

5. **Report summary** with all generated documentation

{{/if}}

## Monitor Progress

After generation starts, you can monitor progress:

```bash
# Follow the latest session
gospelo-monitor --follow-latest

# Check specific session
gospelo-monitor --session <session_id>

# List all sessions
gospelo-monitor --list
```

## Generated Documentation

Documentation is created in:

```
docs/api/<api_name>/
├── README.md              # API overview
├── endpoints/             # Endpoint specifications
│   ├── README.md
│   └── *.md
├── models/                # Data model specifications
│   ├── README.md
│   └── *.md
└── openapi/               # OpenAPI specifications
    ├── openapi.json
    └── openapi.yaml
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
**Version**: 2.0.0 (CLI-based)