"""FastAPI application for Logic-Guard-Layer."""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from logic_guard_layer import __version__
from logic_guard_layer.config import settings
from logic_guard_layer.core.orchestrator import Orchestrator, get_orchestrator, reset_orchestrator
from logic_guard_layer.models.responses import (
    ValidationRequest,
    ValidationResponse,
    ValidationResult,
)
from logic_guard_layer.ontology.constraints import get_all_constraints

logger = logging.getLogger(__name__)

# Paths for templates and static files
from pathlib import Path

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
STATIC_DIR = BASE_DIR / "web" / "static"

# Store for validation history (in-memory for simplicity)
validation_history: list[dict] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting Logic-Guard-Layer v{__version__}")
    yield
    # Cleanup
    await reset_orchestrator()
    logger.info("Logic-Guard-Layer shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Logic-Guard-Layer",
    description="Neuro-symbolic validation layer for LLM outputs",
    version=__version__,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR)) if TEMPLATES_DIR.exists() else None


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": __version__,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/validate", response_model=ValidationResponse)
async def validate_text(request: ValidationRequest):
    """Validate and optionally correct text.

    Args:
        request: Validation request with text and options

    Returns:
        ValidationResponse with results
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        orchestrator = await get_orchestrator()
        orchestrator.auto_correct = request.auto_correct

        result = await orchestrator.process(request.text)

        response = ValidationResponse(
            result=ValidationResult(
                is_valid=result.is_valid,
                violations=result.final_violations,
                corrected_text=result.final_text if result.was_corrected else None,
                iterations=result.correction_result.iterations if result.correction_result else 1,
            ),
            processing_time_ms=result.total_processing_time_ms,
        )

        # Store in history
        validation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "input_text": request.text[:100] + "..." if len(request.text) > 100 else request.text,
            "is_valid": result.is_valid,
            "violations_count": len(result.final_violations),
            "was_corrected": result.was_corrected,
            "processing_time_ms": result.total_processing_time_ms,
        })

        # Keep only last 100 entries
        if len(validation_history) > 100:
            validation_history.pop(0)

        return response

    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/constraints")
async def get_constraints():
    """Get all active validation constraints."""
    constraints = get_all_constraints()
    return {
        "constraints": [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type.value,
                "expression": c.expression,
                "description": c.description,
            }
            for c in constraints
        ]
    }


@app.get("/api/ontology")
async def get_ontology():
    """Get the maintenance ontology schema."""
    from logic_guard_layer.data import SCHEMA_PATH

    if SCHEMA_PATH.exists():
        import json
        with open(SCHEMA_PATH) as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Ontology schema not found")


@app.get("/api/ontology/graph")
async def get_ontology_graph():
    """Get ontology data formatted for graph visualization."""
    from logic_guard_layer.data import SCHEMA_PATH
    import json

    if not SCHEMA_PATH.exists():
        raise HTTPException(status_code=404, detail="Ontology schema not found")

    with open(SCHEMA_PATH) as f:
        schema = json.load(f)

    definitions = schema.get("definitions", {})
    concepts = definitions.get("concepts", {})
    properties = definitions.get("properties", {})
    constraints_def = definitions.get("constraints", [])

    # Build nodes
    nodes = []
    for name, data in concepts.items():
        # Determine category
        if name in ["Component", "RotatingComponent", "StaticComponent", "Motor",
                    "ElectricMotor", "Pump", "HydraulicPump", "VacuumPump",
                    "Valve", "ControlValve", "ShutoffValve", "Container",
                    "Sensor", "PressureSensor", "TemperatureSensor",
                    "Komponente", "RotierendeKomponente", "StatischeKomponente",
                    "Elektromotor", "Hydraulikpumpe", "Vakuumpumpe",
                    "Ventil", "Regelventil", "Absperrventil", "Behaelter",
                    "Drucksensor", "Temperatursensor"]:
            category = "component"
        elif name in ["Event", "MaintenanceEvent", "FailureEvent", "MeasurementEvent",
                      "Ereignis", "Wartungsereignis", "Ausfallereignis", "Messereignis"]:
            category = "event"
        else:
            category = "other"

        # Translate names to English
        name_map = {
            "Komponente": "Component",
            "RotierendeKomponente": "RotatingComponent",
            "StatischeKomponente": "StaticComponent",
            "Elektromotor": "ElectricMotor",
            "Pumpe": "Pump",
            "Hydraulikpumpe": "HydraulicPump",
            "Vakuumpumpe": "VacuumPump",
            "Ventil": "Valve",
            "Regelventil": "ControlValve",
            "Absperrventil": "ShutoffValve",
            "Behaelter": "Container",
            "Drucksensor": "PressureSensor",
            "Temperatursensor": "TemperatureSensor",
            "Ereignis": "Event",
            "Wartungsereignis": "MaintenanceEvent",
            "Ausfallereignis": "FailureEvent",
            "Messereignis": "MeasurementEvent",
            "Anlage": "Plant",
            "Techniker": "Technician",
        }

        display_name = name_map.get(name, name)
        parent = data.get("parent")
        parent_display = name_map.get(parent, parent) if parent else None

        nodes.append({
            "id": display_name,
            "original_id": name,
            "type": "class",
            "category": category,
            "description": data.get("description", ""),
            "parent": parent_display,
            "children": [name_map.get(c, c) for c in data.get("children", [])],
        })

    # Build edges (subclass relationships)
    edges = []
    for node in nodes:
        if node["parent"]:
            edges.append({
                "source": node["id"],
                "target": node["parent"],
                "type": "subclass",
                "label": "is-a",
            })

    # Add object property edges
    obj_props = properties.get("object", {})
    prop_name_map = {
        "hatKomponente": "hasComponent",
        "istTeilVon": "isPartOf",
        "hatWartung": "hasMaintenance",
        "durchgefuehrtVon": "performedBy",
    }
    for prop_id, prop_data in obj_props.items():
        prop_name = prop_name_map.get(prop_id, prop_id)
        domains = prop_data.get("domain", [])
        ranges = prop_data.get("range", [])
        for domain in domains:
            for range_cls in ranges:
                domain_name = name_map.get(domain, domain) if 'name_map' in dir() else domain
                range_name = name_map.get(range_cls, range_cls) if 'name_map' in dir() else range_cls
                edges.append({
                    "source": domain_name,
                    "target": range_name,
                    "type": "object_property",
                    "label": prop_name,
                })

    # Format datatype properties
    dt_props = properties.get("datatype", {})
    datatype_properties = []
    dt_prop_name_map = {
        "hatBetriebsstunden": "operatingHours",
        "hatMaxLebensdauer": "maxLifespan",
        "hatWartungsintervall": "maintenanceInterval",
        "hatSeriennummer": "serialNumber",
        "hatDruckBar": "pressureBar",
        "hatTemperaturC": "temperatureC",
        "hatDatum": "date",
        "hatDrehzahl": "rpm",
        "hatStatus": "status",
    }
    for prop_id, prop_data in dt_props.items():
        prop_name = dt_prop_name_map.get(prop_id, prop_id)
        datatype_properties.append({
            "id": prop_name,
            "original_id": prop_id,
            "description": prop_data.get("description", ""),
            "domain": prop_data.get("domain", []),
            "range": prop_data.get("range", ""),
            "constraints": prop_data.get("constraints", {}),
        })

    # Get constraints
    constraints = get_all_constraints()
    constraints_data = [
        {
            "id": c.id,
            "name": c.name,
            "type": c.type.value,
            "expression": c.expression,
            "description": c.description,
        }
        for c in constraints
    ]

    return {
        "nodes": nodes,
        "edges": edges,
        "datatype_properties": datatype_properties,
        "constraints": constraints_data,
    }


@app.get("/api/history")
async def get_history(limit: int = 20):
    """Get validation history."""
    return {
        "history": validation_history[-limit:],
        "total": len(validation_history),
    }


@app.get("/api/info")
async def get_info():
    """Get system information."""
    return {
        "version": __version__,
        "model": settings.openrouter_model,
        "max_iterations": settings.max_correction_iterations,
        "api_configured": bool(settings.openrouter_api_key),
    }


# ============================================================================
# Frontend Routes
# ============================================================================


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main page."""
    if templates is None:
        return HTMLResponse(content="<h1>Logic-Guard-Layer</h1><p>Templates not found. API available at /api/</p>")
    return templates.TemplateResponse("index.html", {
        "request": request,
        "version": __version__,
    })


@app.get("/validate", response_class=HTMLResponse)
async def validate_page(request: Request):
    """Render the validation page."""
    if templates is None:
        return HTMLResponse(content="Templates not found")
    return templates.TemplateResponse("validate.html", {
        "request": request,
        "version": __version__,
    })


@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    """Render the history page."""
    if templates is None:
        return HTMLResponse(content="Templates not found")
    return templates.TemplateResponse("history.html", {
        "request": request,
        "version": __version__,
        "history": validation_history[-20:],
    })


@app.get("/ontology", response_class=HTMLResponse)
async def ontology_page(request: Request):
    """Render the ontology viewer page."""
    if templates is None:
        return HTMLResponse(content="Templates not found")

    constraints = get_all_constraints()
    return templates.TemplateResponse("ontology.html", {
        "request": request,
        "version": __version__,
        "constraints": [
            {
                "id": c.id,
                "name": c.name,
                "type": c.type.value,
                "expression": c.expression,
                "description": c.description,
            }
            for c in constraints
        ],
    })


@app.get("/visualization", response_class=HTMLResponse)
async def visualization_page(request: Request):
    """Render the ontology visualization page."""
    if templates is None:
        return HTMLResponse(content="Templates not found")

    return templates.TemplateResponse("visualization.html", {
        "request": request,
        "version": __version__,
    })


# ============================================================================
# Error Handlers
# ============================================================================


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    if templates and request.url.path.startswith("/api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    if templates:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return HTMLResponse(content="<h1>404 - Not Found</h1>", status_code=404)


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Handle 500 errors."""
    logger.error(f"Server error: {exc}")
    if templates:
        return templates.TemplateResponse("500.html", {"request": request}, status_code=500)
    return HTMLResponse(content="<h1>500 - Server Error</h1>", status_code=500)
