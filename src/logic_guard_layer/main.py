"""FastAPI application for Logic-Guard-Layer."""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, Optional

import secrets
import uuid
from fastapi import FastAPI, HTTPException, Request, Depends, status, Form, Cookie, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sse_starlette.sse import EventSourceResponse

from logic_guard_layer import __version__
from logic_guard_layer.config import settings
from logic_guard_layer.core.orchestrator import Orchestrator, get_orchestrator, reset_orchestrator
from logic_guard_layer.models.responses import (
    ValidationRequest,
    ValidationResponse,
    ValidationResult,
    OntologyUploadRequest,
    OntologyInfoResponse,
    OntologyListResponse,
)
from logic_guard_layer.ontology.constraints import get_all_constraints
from logic_guard_layer.ontology.manager import get_ontology_manager, OntologyInfo
from logic_guard_layer.data import SCHEMA_PATH, DATA_DIR

logger = logging.getLogger(__name__)

# Paths for templates and static files
from pathlib import Path

BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
STATIC_DIR = BASE_DIR / "web" / "static"

# Store for validation history (in-memory for simplicity)
validation_history: list[dict] = []

# Session store (in-memory)
sessions: dict[str, dict] = {}

# Application state
app_state = {
    "enabled_for_public": True,  # App enabled for non-authenticated users by default
}

# CSRF token store (maps session_id to csrf_token)
csrf_tokens: dict[str, str] = {}


def create_session(username: str) -> tuple[str, str]:
    """Create a new session and return (session_id, csrf_token)."""
    session_id = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "username": username,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow().timestamp() + settings.session_max_age,
    }
    csrf_tokens[session_id] = csrf_token
    return session_id, csrf_token


def get_session(session_id: str) -> Optional[dict]:
    """Get session data by ID, checking expiration."""
    session = sessions.get(session_id)
    if not session:
        return None

    # Check if session has expired
    if datetime.utcnow().timestamp() > session.get("expires_at", 0):
        delete_session(session_id)
        return None

    return session


def delete_session(session_id: str) -> None:
    """Delete a session and its CSRF token."""
    if session_id in sessions:
        del sessions[session_id]
    if session_id in csrf_tokens:
        del csrf_tokens[session_id]


def cleanup_expired_sessions() -> None:
    """Remove all expired sessions."""
    current_time = datetime.utcnow().timestamp()
    expired = [
        sid for sid, session in sessions.items()
        if current_time > session.get("expires_at", 0)
    ]
    for sid in expired:
        delete_session(sid)


def verify_credentials(username: str, password: str) -> bool:
    """Verify login credentials using constant-time comparison."""
    if not settings.is_admin_configured():
        return False

    correct_username = secrets.compare_digest(
        username.encode("utf8"),
        settings.admin_username.encode("utf8")
    )
    correct_password = secrets.compare_digest(
        password.encode("utf8"),
        settings.admin_password.encode("utf8")
    )
    return correct_username and correct_password


def verify_csrf_token(session_id: str, csrf_token: str) -> bool:
    """Verify CSRF token for a session."""
    expected_token = csrf_tokens.get(session_id)
    if not expected_token:
        return False
    return secrets.compare_digest(csrf_token, expected_token)


def get_current_user(session_id: Optional[str] = Cookie(None, alias="session_id")) -> Optional[str]:
    """Get current logged-in user from session cookie."""
    if not session_id:
        return None
    session = get_session(session_id)
    if session:
        return session["username"]
    return None


def require_admin(session_id: Optional[str] = Cookie(None, alias="session_id")) -> str:
    """Require admin authentication, return 401 if not authenticated."""
    if not settings.is_admin_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication not configured"
        )

    user = get_current_user(session_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user


def check_app_enabled(session_id: Optional[str] = Cookie(None, alias="session_id")):
    """Check if application is enabled for the current user."""
    # Logged-in users always have access
    user = get_current_user(session_id)
    if user:
        return

    # Non-authenticated users check public access
    if not app_state["enabled_for_public"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Application is currently disabled for public access. Please login to continue.",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting Logic-Guard-Layer v{__version__}")

    # Log security configuration warnings
    security_warnings = settings.validate_security_config()
    for warning in security_warnings:
        logger.warning(f"SECURITY: {warning}")

    # Initialize OntologyManager with default ontology
    ontology_manager = get_ontology_manager()
    if SCHEMA_PATH.exists():
        ontology_manager.load_default_ontology(SCHEMA_PATH)
        logger.info("Loaded default maintenance ontology")

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


# Security Headers Middleware
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS filter (legacy, but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://d3js.org https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        # Permissions Policy (previously Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )

        return response


# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)


# Rate Limiting Middleware
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(self, app, requests_limit: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = {}

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request, considering proxies."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited."""
        now = datetime.utcnow().timestamp()
        window_start = now - self.window_seconds

        # Get or create request list for this IP
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Remove old requests outside the window
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip] if ts > window_start
        ]

        # Check if over limit
        if len(self.requests[client_ip]) >= self.requests_limit:
            return True

        # Add current request
        self.requests[client_ip].append(now)
        return False

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/api/health":
            return await call_next(request)

        client_ip = self._get_client_ip(request)

        if self._is_rate_limited(client_ip):
            return Response(
                content=json.dumps({
                    "error": "Rate limit exceeded",
                    "retry_after": self.window_seconds
                }),
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(self.window_seconds)}
            )

        return await call_next(request)


# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    requests_limit=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window
)


# Add CORS middleware with secure configuration
cors_origins = settings.get_cors_origins()
if cors_origins:
    # Use configured origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    )
elif settings.debug:
    # In debug mode, allow localhost origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-CSRF-Token"],
    )
# If no origins configured and not in debug mode, CORS is not added (same-origin only)

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
async def validate_text(request: ValidationRequest, session_id: Optional[str] = Cookie(None, alias="session_id")):
    """Validate and optionally correct text.

    Args:
        request: Validation request with text and options

    Returns:
        ValidationResponse with results
    """
    # Check if application is enabled
    check_app_enabled(session_id)

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    try:
        logger.info(f"Validating text: {request.text[:100]}...")
        logger.info(f"Auto-correct: {request.auto_correct}")

        orchestrator = await get_orchestrator()
        orchestrator.auto_correct = request.auto_correct

        result = await orchestrator.process(request.text)

        # Get original violations (before any correction)
        original_violations = []
        if result.initial_consistency and result.initial_consistency.violations:
            original_violations = [
                v.model_dump() if hasattr(v, 'model_dump') else v
                for v in result.initial_consistency.violations
            ]

        logger.info(f"Validation result: is_valid={result.is_valid}, "
                   f"original_violations={len(original_violations)}, "
                   f"final_violations={len(result.final_violations)}")
        if original_violations:
            for v in original_violations:
                logger.info(f"  Original violation: {v}")

        response = ValidationResponse(
            success=result.is_valid,
            violations=[v.model_dump() if hasattr(v, 'model_dump') else v for v in result.final_violations],
            original_violations=original_violations,
            iterations=result.correction_result.iterations if result.correction_result else 1,
            processing_time_ms=result.total_processing_time_ms,
            corrected_text=result.final_text if result.was_corrected else None,
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


@app.post("/api/validate/stream")
async def validate_text_stream(request: ValidationRequest, session_id: Optional[str] = Cookie(None, alias="session_id")):
    """Validate text with Server-Sent Events for progress updates.

    Streams progress events as the validation pipeline executes.
    """
    # Check if application is enabled
    check_app_enabled(session_id)

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    async def event_generator() -> AsyncGenerator[dict, None]:
        """Generate SSE events for validation progress."""
        import time
        start_time = time.time()

        try:
            # Step 1: Initialize
            yield {
                "event": "progress",
                "data": json.dumps({
                    "step": "init",
                    "status": "running",
                    "message": "Initializing validation pipeline...",
                    "progress": 0
                })
            }

            orchestrator = await get_orchestrator()
            orchestrator.auto_correct = request.auto_correct

            yield {
                "event": "progress",
                "data": json.dumps({
                    "step": "init",
                    "status": "done",
                    "message": "Pipeline initialized",
                    "progress": 10
                })
            }

            # Step 2: Parse
            yield {
                "event": "progress",
                "data": json.dumps({
                    "step": "parse",
                    "status": "running",
                    "message": "Parsing text with LLM...",
                    "progress": 15
                })
            }

            await orchestrator._ensure_initialized()
            parsed_data = await orchestrator.parser.parse(request.text)
            raw_values = orchestrator.parser.extract_raw_values(parsed_data)

            # Build extracted info message
            extracted_info = []
            if raw_values.get("name"):
                extracted_info.append(f"Component: {raw_values['name']}")
            if raw_values.get("operating_hours"):
                extracted_info.append(f"Hours: {raw_values['operating_hours']}")
            if raw_values.get("max_lifespan"):
                extracted_info.append(f"Max lifespan: {raw_values['max_lifespan']}")
            if raw_values.get("pressure_bar"):
                extracted_info.append(f"Pressure: {raw_values['pressure_bar']} bar")
            if raw_values.get("temperature_c"):
                extracted_info.append(f"Temp: {raw_values['temperature_c']}°C")

            yield {
                "event": "progress",
                "data": json.dumps({
                    "step": "parse",
                    "status": "done",
                    "message": f"Extracted: {', '.join(extracted_info) if extracted_info else 'No data found'}",
                    "progress": 35,
                    "data": {"extracted": raw_values}
                })
            }

            # Step 3: Validate
            yield {
                "event": "progress",
                "data": json.dumps({
                    "step": "validate",
                    "status": "running",
                    "message": f"Checking {len(orchestrator.reasoner.constraints)} constraints + OWL reasoning...",
                    "progress": 40
                })
            }

            consistency = orchestrator.reasoner.check_consistency(raw_values)

            # Include OWL info in validation step
            owl_info = ""
            if hasattr(consistency, 'owl_violations_count') and consistency.owl_violations_count > 0:
                owl_info = f" ({consistency.owl_violations_count} from OWL reasoning)"

            if consistency.is_consistent:
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "step": "validate",
                        "status": "done",
                        "message": "All constraints satisfied (rules + OWL reasoning)",
                        "progress": 90
                    })
                }
                final_text = request.text
                final_violations = []
                original_violations = []
                was_corrected = False
            else:
                violation_msgs = [v.message for v in consistency.violations[:3]]
                yield {
                    "event": "progress",
                    "data": json.dumps({
                        "step": "validate",
                        "status": "done",
                        "message": f"Found {len(consistency.violations)} violation(s){owl_info}",
                        "progress": 50,
                        "data": {"violations": violation_msgs, "owl_violations": consistency.owl_violations_count if hasattr(consistency, 'owl_violations_count') else 0}
                    })
                }

                original_violations = [
                    v.model_dump() if hasattr(v, 'model_dump') else v
                    for v in consistency.violations
                ]

                if request.auto_correct:
                    # Step 4: Correct
                    yield {
                        "event": "progress",
                        "data": json.dumps({
                            "step": "correct",
                            "status": "running",
                            "message": "Auto-correcting violations with LLM...",
                            "progress": 55
                        })
                    }

                    correction = await orchestrator.corrector.correct(request.text)

                    if correction.is_consistent:
                        yield {
                            "event": "progress",
                            "data": json.dumps({
                                "step": "correct",
                                "status": "done",
                                "message": f"Corrected in {correction.iterations} iteration(s)",
                                "progress": 85
                            })
                        }
                    else:
                        yield {
                            "event": "progress",
                            "data": json.dumps({
                                "step": "correct",
                                "status": "warning",
                                "message": f"Could not fix all violations after {correction.iterations} iterations",
                                "progress": 85
                            })
                        }

                    final_text = correction.corrected_text
                    final_violations = [
                        v.model_dump() if hasattr(v, 'model_dump') else v
                        for v in correction.final_violations
                    ]
                    was_corrected = request.text != correction.corrected_text
                else:
                    yield {
                        "event": "progress",
                        "data": json.dumps({
                            "step": "correct",
                            "status": "skipped",
                            "message": "Auto-correction disabled",
                            "progress": 85
                        })
                    }
                    final_text = request.text
                    final_violations = original_violations
                    was_corrected = False

            # Step 5: Complete
            processing_time = (time.time() - start_time) * 1000

            yield {
                "event": "progress",
                "data": json.dumps({
                    "step": "complete",
                    "status": "done",
                    "message": f"Completed in {processing_time:.0f}ms",
                    "progress": 100
                })
            }

            # Final result
            result = {
                "success": len(final_violations) == 0,
                "violations": final_violations,
                "original_violations": original_violations,
                "corrected_text": final_text if was_corrected else None,
                "processing_time_ms": processing_time,
                "iterations": 1
            }

            yield {
                "event": "result",
                "data": json.dumps(result)
            }

            # Store in history
            validation_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "input_text": request.text[:100] + "..." if len(request.text) > 100 else request.text,
                "is_valid": result["success"],
                "violations_count": len(final_violations),
                "was_corrected": was_corrected,
                "processing_time_ms": processing_time,
            })
            if len(validation_history) > 100:
                validation_history.pop(0)

        except Exception as e:
            logger.error(f"Validation stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({
                    "step": "error",
                    "status": "error",
                    "message": str(e)
                })
            }

    return EventSourceResponse(event_generator())


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


@app.get("/api/owl/status")
async def get_owl_status():
    """Get OWL reasoning status and loaded ontology information."""
    from logic_guard_layer.ontology.loader import get_ontology_loader, load_ontology

    try:
        loader = load_ontology()
        concepts = loader.get_concepts() if loader.is_loaded else {}
        properties = loader.get_properties() if loader.is_loaded else {}

        return {
            "enabled": True,
            "loaded": loader.is_loaded,
            "concepts_count": len(concepts),
            "properties_count": len(properties),
            "concepts": list(concepts.keys()),
            "datatype_properties": [
                name for name, info in properties.items()
                if info.get("type") == "datatype"
            ],
            "object_properties": [
                name for name, info in properties.items()
                if info.get("type") == "object"
            ],
        }
    except Exception as e:
        logger.error(f"Error getting OWL status: {e}")
        return {
            "enabled": True,
            "loaded": False,
            "error": str(e),
            "concepts_count": 0,
            "properties_count": 0,
        }


@app.get("/api/owl/hierarchy")
async def get_owl_hierarchy():
    """Get the OWL class hierarchy for visualization."""
    from logic_guard_layer.ontology.loader import load_ontology

    try:
        loader = load_ontology()
        if not loader.is_loaded:
            return {"error": "OWL ontology not loaded", "hierarchy": []}

        concepts = loader.get_concepts()

        # Build hierarchy tree
        def build_tree(class_name: str, visited: set = None) -> dict:
            if visited is None:
                visited = set()
            if class_name in visited:
                return None
            visited.add(class_name)

            children = [
                name for name, parents in concepts.items()
                if class_name in parents and name not in visited
            ]

            return {
                "name": class_name,
                "children": [
                    build_tree(child, visited.copy())
                    for child in sorted(children)
                    if build_tree(child, visited.copy()) is not None
                ]
            }

        # Find root classes (no parents or only Thing as parent)
        roots = []
        for name, parents in concepts.items():
            if not parents or all(p in ["Thing", "owl.Thing"] for p in parents):
                # Skip violation marker classes for cleaner display
                if "Violation" not in name:
                    roots.append(name)

        hierarchy = [build_tree(root) for root in sorted(roots) if build_tree(root)]

        return {
            "hierarchy": hierarchy,
            "total_concepts": len(concepts),
        }
    except Exception as e:
        logger.error(f"Error getting OWL hierarchy: {e}")
        return {"error": str(e), "hierarchy": []}


@app.get("/api/owl/properties")
async def get_owl_properties():
    """Get OWL datatype properties with their ranges."""
    from logic_guard_layer.ontology.loader import load_ontology

    try:
        loader = load_ontology()
        if not loader.is_loaded:
            return {"error": "OWL ontology not loaded", "properties": []}

        properties = loader.get_properties()

        # Format properties for display
        formatted = []
        for name, info in properties.items():
            if info.get("type") == "datatype":
                formatted.append({
                    "name": name,
                    "domain": info.get("domain", []),
                    "range": info.get("range", "unknown"),
                })

        return {"properties": formatted}
    except Exception as e:
        logger.error(f"Error getting OWL properties: {e}")
        return {"error": str(e), "properties": []}


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


# ============================================================================
# Ontology Management Endpoints
# ============================================================================


@app.get("/api/ontologies", response_model=OntologyListResponse)
async def list_ontologies():
    """List all available ontologies."""
    manager = get_ontology_manager()
    active_name = manager.get_active_name()

    ontologies = []
    for info in manager.list_ontologies():
        ontologies.append(OntologyInfoResponse(
            name=info.name,
            description=info.description,
            version=info.version,
            created_at=info.created_at,
            concepts_count=info.concepts_count,
            constraints_count=info.constraints_count,
            is_default=info.is_default,
            is_active=(info.name == active_name),
        ))

    return OntologyListResponse(
        ontologies=ontologies,
        active=active_name,
    )


@app.post("/api/ontology/upload")
async def upload_ontology(request: OntologyUploadRequest):
    """Upload a new ontology schema."""
    manager = get_ontology_manager()

    errors = manager.register(
        name=request.name,
        schema=request.ontology_schema,
        description=request.description,
    )

    if errors:
        raise HTTPException(status_code=400, detail={"errors": errors})

    info = manager.get_info(request.name.strip().lower().replace(" ", "-"))
    return {
        "success": True,
        "message": f"Ontology '{request.name}' uploaded successfully",
        "ontology": {
            "name": info.name,
            "concepts_count": info.concepts_count,
            "constraints_count": info.constraints_count,
        }
    }


@app.get("/api/ontology/sample")
async def get_sample_ontology():
    """Get a sample ontology schema to show the expected format."""
    sample_path = DATA_DIR / "sample_ontology.json"
    if sample_path.exists():
        with open(sample_path) as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Sample ontology not found")


@app.get("/api/ontology/{name}")
async def get_ontology_by_name(name: str):
    """Get a specific ontology schema by name."""
    manager = get_ontology_manager()
    schema = manager.get(name)

    if schema is None:
        raise HTTPException(status_code=404, detail=f"Ontology '{name}' not found")

    return schema


@app.post("/api/ontology/{name}/activate")
async def activate_ontology(name: str):
    """Set an ontology as the active one for validation."""
    manager = get_ontology_manager()

    if not manager.set_active(name):
        raise HTTPException(status_code=404, detail=f"Ontology '{name}' not found")

    return {
        "success": True,
        "message": f"Ontology '{name}' is now active",
        "active": name,
    }


@app.delete("/api/ontology/{name}")
async def delete_ontology(name: str):
    """Delete a custom ontology (cannot delete default)."""
    manager = get_ontology_manager()

    if name == "maintenance":
        raise HTTPException(status_code=400, detail="Cannot delete the default ontology")

    if not manager.delete(name):
        raise HTTPException(status_code=404, detail=f"Ontology '{name}' not found")

    return {
        "success": True,
        "message": f"Ontology '{name}' deleted",
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
# Admin Endpoints
# ============================================================================


@app.get("/api/admin/status")
async def get_admin_status(user: str = Depends(require_admin)):
    """Get application status (admin only)."""
    return {
        "enabled_for_public": app_state["enabled_for_public"],
        "version": __version__,
        "validation_count": len(validation_history),
        "active_sessions": len(sessions),
    }


@app.post("/api/admin/enable")
async def enable_application(user: str = Depends(require_admin)):
    """Enable public access to the application (admin only)."""
    app_state["enabled_for_public"] = True
    logger.info(f"Public access ENABLED by admin: {user}")
    return {"success": True, "enabled_for_public": True, "message": "Public access enabled"}


@app.post("/api/admin/disable")
async def disable_application(user: str = Depends(require_admin)):
    """Disable public access to the application (admin only)."""
    app_state["enabled_for_public"] = False
    logger.info(f"Public access DISABLED by admin: {user}")
    return {"success": True, "enabled_for_public": False, "message": "Public access disabled"}


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


@app.get("/help", response_class=HTMLResponse)
async def help_page(request: Request):
    """Render the help/documentation page."""
    if templates is None:
        return HTMLResponse(content="Templates not found")

    return templates.TemplateResponse("help.html", {
        "request": request,
        "version": __version__,
    })


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, session_id: Optional[str] = Cookie(None, alias="session_id")):
    """Render the login page."""
    # If already logged in, redirect to admin
    if get_current_user(session_id):
        return RedirectResponse(url="/admin", status_code=303)

    if templates is None:
        return HTMLResponse(content="Templates not found")

    return templates.TemplateResponse("login.html", {
        "request": request,
        "version": __version__,
        "error": None,
    })


@app.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(default=""),
):
    """Handle login form submission."""
    # Log failed login attempts (for security monitoring)
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")

    if verify_credentials(username, password):
        session_id, csrf_token = create_session(username)
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=settings.session_max_age,
            samesite="strict",  # Stricter than "lax" for better CSRF protection
            secure=not settings.debug,  # True in production (HTTPS only)
        )
        # Set CSRF token in a separate cookie (readable by JavaScript)
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            httponly=False,  # JavaScript needs to read this
            max_age=settings.session_max_age,
            samesite="strict",
            secure=not settings.debug,
        )
        logger.info(f"User '{username}' logged in from {client_ip}")
        return response

    # Log failed login attempt
    logger.warning(f"Failed login attempt for user '{username}' from {client_ip}")

    # Invalid credentials
    if templates is None:
        return HTMLResponse(content="Invalid credentials", status_code=401)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "version": __version__,
        "error": "Invalid username or password",
    }, status_code=401)


@app.get("/logout")
async def logout(request: Request, session_id: Optional[str] = Cookie(None, alias="session_id")):
    """Log out and clear session."""
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")

    if session_id:
        user = get_current_user(session_id)
        delete_session(session_id)
        logger.info(f"User '{user}' logged out from {client_ip}")

    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_id")
    response.delete_cookie("csrf_token")
    return response


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request, session_id: Optional[str] = Cookie(None, alias="session_id")):
    """Render the admin page (requires authentication)."""
    user = get_current_user(session_id)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if templates is None:
        return HTMLResponse(content="Templates not found")

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "version": __version__,
        "enabled_for_public": app_state["enabled_for_public"],
        "validation_count": len(validation_history),
        "username": user,
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
