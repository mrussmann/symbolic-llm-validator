# API Reference

This document provides a complete reference for the Logic-Guard-Layer REST API.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Endpoints](#endpoints)
  - [Health & Status](#health--status)
  - [Validation](#validation)
  - [Constraints](#constraints)
  - [Ontology](#ontology)
  - [History](#history)
  - [Admin](#admin)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

---

## Overview

### Base URL

```
http://localhost:8000
```

### Content Type

All API endpoints accept and return JSON:

```
Content-Type: application/json
```

### Response Format

All responses follow this general structure:

```json
{
    "success": true,
    "data": { ... },
    "error": null
}
```

---

## Authentication

### Session-Based Authentication

Some endpoints require authentication via session cookies.

#### Login

```http
POST /login
Content-Type: application/x-www-form-urlencoded

username=admin&password=secret
```

**Response:** Redirects to `/` on success, `/login?error=1` on failure.

#### Logout

```http
GET /logout
```

**Response:** Redirects to `/`.

### Protected Endpoints

The following endpoints require authentication:
- `GET /admin`
- `GET /api/admin/status`
- `POST /api/admin/enable`
- `POST /api/admin/disable`
- `POST /api/ontology/upload`

---

## Endpoints

### Health & Status

#### GET /api/health

Check the health status of the service.

**Request:**
```http
GET /api/health
```

**Response:**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "model": "tngtech/deepseek-r1t2-chimera:free",
    "ontology_loaded": true
}
```

**Status Codes:**
- `200 OK` - Service is healthy
- `500 Internal Server Error` - Service is unhealthy

---

### Validation

#### POST /api/validate

Validate and optionally correct text against ontology constraints.

**Request:**
```http
POST /api/validate
Content-Type: application/json

{
    "text": "Motor M1 hat 25000 Betriebsstunden bei max 20000.",
    "schema_name": "maintenance",
    "max_iterations": 5,
    "auto_correct": true
}
```

**Parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `text` | string | Yes | - | Text to validate (min 1 char) |
| `schema_name` | string | No | `"maintenance"` | Ontology schema to use |
| `max_iterations` | integer | No | `5` | Max correction iterations (1-10) |
| `auto_correct` | boolean | No | `true` | Whether to auto-correct violations |

**Response (Success):**
```json
{
    "success": true,
    "data": {
        "component": {
            "name": "M1",
            "type": "Motor",
            "operating_hours": 18000,
            "max_lifespan": 20000
        }
    },
    "violations": [],
    "original_violations": [
        {
            "type": "RELATIONAL_ERROR",
            "constraint": "operating_hours <= max_lifespan",
            "message": "Operating hours (25000) exceed maximum lifespan (20000)",
            "property_name": "operating_hours",
            "actual_value": 25000,
            "expected_value": "<= 20000"
        }
    ],
    "iterations": 2,
    "checked_constraints": 8,
    "processing_time_ms": 1523.45,
    "confidence": 0.95,
    "corrected_text": "Motor M1 hat 18000 Betriebsstunden bei max 20000."
}
```

**Response (Validation Failed):**
```json
{
    "success": false,
    "data": null,
    "violations": [
        {
            "type": "RANGE_ERROR",
            "constraint": "operating_hours >= 0",
            "message": "Operating hours cannot be negative: -100",
            "property_name": "operating_hours",
            "actual_value": -100,
            "expected_value": ">= 0",
            "severity": "error"
        }
    ],
    "iterations": 5,
    "checked_constraints": 8,
    "processing_time_ms": 5234.12,
    "error": "Could not resolve all violations after 5 iterations"
}
```

**Status Codes:**
- `200 OK` - Request processed (check `success` field)
- `422 Unprocessable Entity` - Invalid request body
- `500 Internal Server Error` - Server error

---

#### POST /api/validate/stream

Validate text with Server-Sent Events (SSE) for real-time progress.

**Request:**
```http
POST /api/validate/stream
Content-Type: application/json

{
    "text": "Motor M1 hat 25000 Betriebsstunden.",
    "auto_correct": true
}
```

**Response (SSE Stream):**
```
event: status
data: {"stage": "parsing", "message": "Parsing input text..."}

event: status
data: {"stage": "validating", "message": "Checking constraints..."}

event: violation
data: {"type": "RELATIONAL_ERROR", "message": "..."}

event: status
data: {"stage": "correcting", "iteration": 1, "message": "Correcting..."}

event: result
data: {"success": true, "corrected_text": "...", "iterations": 2}

event: done
data: {}
```

---

### Constraints

#### GET /api/constraints

Get all validation constraints.

**Request:**
```http
GET /api/constraints
```

**Response:**
```json
{
    "constraints": [
        {
            "id": "C1",
            "name": "Operating hours non-negative",
            "type": "range",
            "expression": "operating_hours >= 0",
            "description": "Operating hours must be >= 0"
        },
        {
            "id": "C2",
            "name": "Maximum lifespan positive",
            "type": "range",
            "expression": "max_lifespan > 0",
            "description": "Maximum lifespan must be > 0"
        },
        {
            "id": "C3",
            "name": "Maintenance interval positive",
            "type": "range",
            "expression": "maintenance_interval > 0",
            "description": "Maintenance interval must be > 0"
        },
        {
            "id": "C4",
            "name": "Maintenance interval <= lifespan",
            "type": "relational",
            "expression": "maintenance_interval <= max_lifespan",
            "description": "Maintenance interval cannot exceed maximum lifespan"
        },
        {
            "id": "C5",
            "name": "Operating hours <= lifespan",
            "type": "relational",
            "expression": "operating_hours <= max_lifespan",
            "description": "Operating hours cannot exceed maximum lifespan"
        },
        {
            "id": "C6",
            "name": "Hydraulic pressure range",
            "type": "physical",
            "expression": "0 <= pressure_bar <= 350",
            "description": "Pressure must be within valid range (0-350 bar)"
        },
        {
            "id": "C7",
            "name": "Temperature range",
            "type": "physical",
            "expression": "-40 <= temperature_c <= 150",
            "description": "Temperature must be within valid range (-40 to 150°C)"
        },
        {
            "id": "C8",
            "name": "RPM range",
            "type": "physical",
            "expression": "0 <= rpm <= 10000",
            "description": "RPM must be within valid range (0-10000)"
        }
    ],
    "count": 8
}
```

---

### Ontology

#### GET /api/ontology

Get the active ontology schema.

**Request:**
```http
GET /api/ontology
```

**Response:**
```json
{
    "name": "maintenance",
    "version": "1.0.0",
    "description": "Maintenance domain ontology",
    "definitions": {
        "concepts": {
            "Component": {
                "description": "Base class for all components"
            },
            "Motor": {
                "description": "Electric motor",
                "parent": "RotatingComponent"
            }
        },
        "properties": {
            "operating_hours": {
                "type": "integer",
                "min": 0
            }
        },
        "constraints": [...]
    }
}
```

---

#### GET /api/ontology/graph

Get the ontology as a graph structure for visualization.

**Request:**
```http
GET /api/ontology/graph
```

**Response:**
```json
{
    "nodes": [
        {"id": "Component", "label": "Component", "type": "concept"},
        {"id": "Motor", "label": "Motor", "type": "concept"},
        {"id": "operating_hours", "label": "operating_hours", "type": "property"}
    ],
    "edges": [
        {"source": "Motor", "target": "Component", "label": "subClassOf"},
        {"source": "operating_hours", "target": "Component", "label": "domain"}
    ]
}
```

---

#### GET /api/ontologies

List all available ontologies.

**Request:**
```http
GET /api/ontologies
```

**Response:**
```json
{
    "ontologies": [
        {
            "name": "maintenance",
            "description": "Default maintenance ontology",
            "version": "1.0.0",
            "created_at": "2024-01-15T10:30:00Z",
            "concepts_count": 12,
            "constraints_count": 8,
            "is_default": true,
            "is_active": true
        },
        {
            "name": "custom-automotive",
            "description": "Custom automotive ontology",
            "version": "1.0.0",
            "created_at": "2024-01-20T14:00:00Z",
            "concepts_count": 8,
            "constraints_count": 5,
            "is_default": false,
            "is_active": false
        }
    ],
    "active": "maintenance"
}
```

---

#### POST /api/ontology/upload

Upload a custom ontology schema. **Requires authentication.**

**Request:**
```http
POST /api/ontology/upload
Content-Type: application/json
Cookie: session=...

{
    "name": "custom-ontology",
    "description": "My custom ontology",
    "schema": {
        "definitions": {
            "concepts": {
                "CustomComponent": {
                    "description": "Custom component type"
                }
            },
            "constraints": [
                {
                    "id": "CC1",
                    "name": "Custom constraint",
                    "expression": "value > 0"
                }
            ]
        }
    }
}
```

**Response (Success):**
```json
{
    "success": true,
    "name": "custom-ontology",
    "message": "Ontology uploaded successfully"
}
```

**Response (Validation Error):**
```json
{
    "success": false,
    "errors": [
        "Concept 'CustomComponent' missing 'description'",
        "Constraint 0 missing 'name'"
    ]
}
```

**Status Codes:**
- `200 OK` - Upload successful
- `400 Bad Request` - Schema validation failed
- `401 Unauthorized` - Authentication required

---

#### POST /api/ontology/activate

Activate an ontology for validation.

**Request:**
```http
POST /api/ontology/activate
Content-Type: application/json

{
    "name": "custom-ontology"
}
```

**Response:**
```json
{
    "success": true,
    "active": "custom-ontology"
}
```

---

#### DELETE /api/ontology/{name}

Delete a custom ontology. **Requires authentication.** Cannot delete the default ontology.

**Request:**
```http
DELETE /api/ontology/custom-ontology
Cookie: session=...
```

**Response:**
```json
{
    "success": true,
    "message": "Ontology 'custom-ontology' deleted"
}
```

---

### History

#### GET /api/history

Get validation history.

**Request:**
```http
GET /api/history
GET /api/history?limit=10
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Max number of entries to return |

**Response:**
```json
{
    "history": [
        {
            "id": "abc123",
            "timestamp": "2024-01-15T10:30:00Z",
            "input_text": "Motor M1 hat 25000 Betriebsstunden...",
            "success": true,
            "violations_count": 1,
            "iterations": 2,
            "processing_time_ms": 1523.45
        }
    ],
    "count": 1
}
```

---

### Admin

#### GET /api/admin/status

Get admin status. **Requires authentication.**

**Request:**
```http
GET /api/admin/status
Cookie: session=...
```

**Response:**
```json
{
    "enabled": true,
    "auto_correct_default": true,
    "max_iterations": 5,
    "model": "tngtech/deepseek-r1t2-chimera:free",
    "total_validations": 150,
    "success_rate": 0.87
}
```

---

#### POST /api/admin/enable

Enable the validation service. **Requires authentication.**

**Request:**
```http
POST /api/admin/enable
Cookie: session=...
```

**Response:**
```json
{
    "success": true,
    "enabled": true
}
```

---

#### POST /api/admin/disable

Disable the validation service. **Requires authentication.**

**Request:**
```http
POST /api/admin/disable
Cookie: session=...
```

**Response:**
```json
{
    "success": true,
    "enabled": false
}
```

---

## Error Handling

### Error Response Format

```json
{
    "detail": "Error message",
    "status_code": 400
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `400` | Bad Request - Invalid input |
| `401` | Unauthorized - Authentication required |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Resource not found |
| `422` | Unprocessable Entity - Validation failed |
| `429` | Too Many Requests - Rate limit exceeded |
| `500` | Internal Server Error |

### Validation Error Response

```json
{
    "detail": [
        {
            "loc": ["body", "text"],
            "msg": "field required",
            "type": "value_error.missing"
        },
        {
            "loc": ["body", "max_iterations"],
            "msg": "ensure this value is less than or equal to 10",
            "type": "value_error.number.not_le"
        }
    ]
}
```

---

## Rate Limiting

Rate limiting is handled by the OpenRouter API:

- **Free tier**: Limited requests per minute
- **Paid tier**: Higher limits based on plan

When rate limited, the API returns:

```json
{
    "error": "Rate limit exceeded",
    "retry_after": 60
}
```

---

## Code Examples

### Python (httpx)

```python
import httpx

async def validate_text(text: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/validate",
            json={
                "text": text,
                "auto_correct": True
            }
        )
        return response.json()
```

### JavaScript (fetch)

```javascript
async function validateText(text) {
    const response = await fetch('http://localhost:8000/api/validate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            text: text,
            auto_correct: true
        })
    });
    return response.json();
}
```

### cURL

```bash
# Validate text
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"text": "Motor M1 hat 5000 Betriebsstunden.", "auto_correct": true}'

# Get constraints
curl http://localhost:8000/api/constraints

# Get health status
curl http://localhost:8000/api/health
```

---

## WebSocket Support

Currently, the API does not support WebSocket connections. For real-time updates, use the SSE streaming endpoint (`/api/validate/stream`).
