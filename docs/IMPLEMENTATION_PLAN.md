# Logic-Guard-Layer: Implementation Plan

## Overview

This plan outlines the implementation of a **neuro-symbolic hybrid architecture** for validating LLM outputs. The system combines the flexibility of Large Language Models with the reliability of symbolic reasoning through ontology-based validation.

---

## Phase 1: Project Setup & Foundation

### 1.1 Project Structure
Create the following directory structure (pip-installable package):

```
logic-guard-layer/                 # Root project directory
├── pyproject.toml                 # Modern Python packaging config
├── setup.py                       # Backwards compatibility
├── README.md                      # Project documentation
├── LICENSE                        # License file
├── .env.example                   # Example environment variables
│
├── src/
│   └── logic_guard_layer/
│       ├── __init__.py            # Package init with version
│       ├── __main__.py            # CLI entry point
│       ├── main.py                # FastAPI application
│       ├── config.py              # Configuration management
│       ├── cli.py                 # Command-line interface
│       │
│       ├── core/                  # Core business logic
│       │   ├── __init__.py
│       │   ├── orchestrator.py    # Main coordination logic
│       │   ├── parser.py          # Semantic parser
│       │   ├── reasoner.py        # Reasoning module
│       │   └── corrector.py       # Self-correction loop
│       │
│       ├── ontology/              # Ontology handling
│       │   ├── __init__.py
│       │   ├── loader.py          # OWL file loading
│       │   ├── validator.py       # Schema validation
│       │   └── constraints.py     # Constraint definitions
│       │
│       ├── llm/                   # LLM integration (OpenRouter)
│       │   ├── __init__.py
│       │   ├── client.py          # OpenRouter API client
│       │   └── prompts.py         # Prompt templates
│       │
│       ├── models/                # Data models (Pydantic)
│       │   ├── __init__.py
│       │   ├── entities.py        # Domain entities
│       │   └── responses.py       # API response models
│       │
│       ├── web/                   # Frontend (Jinja2 templates)
│       │   ├── __init__.py
│       │   ├── routes.py          # Web routes for HTML pages
│       │   ├── templates/         # Jinja2 HTML templates
│       │   │   ├── base.html      # Base layout (terminal theme)
│       │   │   ├── index.html     # Dashboard page
│       │   │   ├── validate.html  # Validation form
│       │   │   ├── results.html   # Results display
│       │   │   ├── history.html   # Validation history
│       │   │   ├── ontology.html  # Ontology browser
│       │   │   └── components/    # Reusable components
│       │   │       ├── navbar.html
│       │   │       ├── footer.html
│       │   │       ├── violation_card.html
│       │   │       └── loading.html
│       │   └── static/            # Static assets
│       │       ├── css/
│       │       │   └── style.css  # Terminal theme CSS
│       │       └── js/
│       │           └── app.js     # Frontend JavaScript
│       │
│       ├── utils/                 # Utilities
│       │   ├── __init__.py
│       │   ├── logging.py
│       │   └── metrics.py
│       │
│       └── data/                  # Bundled data files
│           └── maintenance.owl    # Default ontology
│
└── tests/                         # Test suite
    ├── __init__.py
    ├── conftest.py                # Pytest fixtures
    ├── test_parser.py
    ├── test_reasoner.py
    ├── test_corrector.py
    └── test_integration.py
```

### 1.2 Package Configuration (`pyproject.toml`)

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "logic-guard-layer"
version = "1.0.0"
description = "Neuro-symbolic hybrid architecture for validating LLM outputs"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.11"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
keywords = ["llm", "validation", "ontology", "neuro-symbolic", "ai"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

dependencies = [
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.23.0",
    "owlready2>=0.40",
    "httpx>=0.24.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-multipart>=0.0.6",
    "jinja2>=3.1.0",
    "aiofiles>=23.0.0",
    "python-dotenv>=1.0.0",
    "click>=8.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[project.scripts]
logic-guard = "logic_guard_layer.cli:main"
lgl = "logic_guard_layer.cli:main"

[project.urls]
Homepage = "https://github.com/yourname/logic-guard-layer"
Documentation = "https://github.com/yourname/logic-guard-layer#readme"
Repository = "https://github.com/yourname/logic-guard-layer"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
logic_guard_layer = [
    "data/*.owl",
    "web/templates/**/*.html",
    "web/static/**/*",
]

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.ruff]
line-length = 88
select = ["E", "F", "I", "N", "W"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
```

### 1.3 CLI Module (`cli.py`)

**Command-Line Interface:**
```python
import click
import uvicorn
from logic_guard_layer.config import settings

@click.group()
@click.version_option(version="1.0.0", prog_name="logic-guard-layer")
def main():
    """Logic-Guard-Layer: Neuro-symbolic LLM output validation."""
    pass


@main.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    """Start the Logic-Guard-Layer web server."""
    click.echo(f"Starting Logic-Guard-Layer server at http://{host}:{port}")
    click.echo(f"Using model: {settings.openrouter_model}")
    uvicorn.run(
        "logic_guard_layer.main:app",
        host=host,
        port=port,
        reload=reload
    )


@main.command()
@click.argument("text", required=False)
@click.option("--file", "-f", type=click.Path(exists=True), help="Input file")
@click.option("--output", "-o", type=click.Choice(["json", "text"]), default="text")
def validate(text: str, file: str, output: str):
    """Validate text against the ontology (CLI mode)."""
    import asyncio
    from logic_guard_layer.core.orchestrator import LogicGuardLayer

    if file:
        with open(file) as f:
            text = f.read()
    elif not text:
        text = click.get_text_stream("stdin").read()

    async def run_validation():
        lgl = LogicGuardLayer()
        try:
            result = await lgl.validate(text)
            return result
        finally:
            await lgl.close()

    result = asyncio.run(run_validation())

    if output == "json":
        import json
        click.echo(json.dumps(result.dict(), indent=2))
    else:
        if result.success:
            click.secho("[SUCCESS] Validation passed!", fg="green")
        else:
            click.secho(f"[ERROR] {len(result.violations)} violation(s) found:", fg="red")
            for v in result.violations:
                click.echo(f"  - {v.type}: {v.message}")


@main.command()
def info():
    """Display configuration information."""
    click.echo("Logic-Guard-Layer Configuration:")
    click.echo(f"  Model: {settings.openrouter_model}")
    click.echo(f"  Ontology: {settings.ontology_path}")
    click.echo(f"  Max Iterations: {settings.max_correction_iterations}")


if __name__ == "__main__":
    main()
```

### 1.4 Package Entry Point (`__main__.py`)

```python
"""Allow running as: python -m logic_guard_layer"""
from logic_guard_layer.cli import main

if __name__ == "__main__":
    main()
```

### 1.5 Package Init (`__init__.py`)

```python
"""Logic-Guard-Layer: Neuro-symbolic LLM output validation."""

__version__ = "1.0.0"
__author__ = "Your Name"

from logic_guard_layer.core.orchestrator import LogicGuardLayer
from logic_guard_layer.models.responses import ValidationResult, Violation

__all__ = ["LogicGuardLayer", "ValidationResult", "Violation", "__version__"]
```

### 1.6 Installation Methods

**Install from PyPI (when published):**
```bash
pip install logic-guard-layer
```

**Install from source:**
```bash
git clone https://github.com/yourname/logic-guard-layer.git
cd logic-guard-layer
pip install -e .
```

**Install with development dependencies:**
```bash
pip install -e ".[dev]"
```

**Run as standalone application:**
```bash
# Start web server
logic-guard serve --host 0.0.0.0 --port 8000

# Or using the short alias
lgl serve

# Validate text from command line
lgl validate "Der Motor M1 hat 15.000 Betriebsstunden..."

# Validate from file
lgl validate -f report.txt -o json

# Validate from stdin
cat report.txt | lgl validate

# Show configuration
lgl info
```

**Run as Python module:**
```bash
python -m logic_guard_layer serve
python -m logic_guard_layer validate "text to validate"
```

**Use as library:**
```python
from logic_guard_layer import LogicGuardLayer

async def main():
    lgl = LogicGuardLayer()
    result = await lgl.validate("Der Motor M1 hat 15.000 Betriebsstunden...")

    if result.success:
        print("Validation passed!")
    else:
        for violation in result.violations:
            print(f"Error: {violation.message}")

    await lgl.close()
```

---

## Phase 2: Data Models & Configuration

### 2.1 Configuration (`config.py`)

**Configuration with Pydantic Settings:**
```python
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    # OpenRouter LLM Configuration
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        env="OPENROUTER_BASE_URL"
    )
    openrouter_model: str = Field(
        default="tngtech/deepseek-r1t2-chimera:free",
        env="OPENROUTER_MODEL"
    )
    llm_timeout: float = Field(default=60.0, env="LLM_TIMEOUT")
    llm_max_retries: int = Field(default=3, env="LLM_MAX_RETRIES")

    # Ontology Configuration
    ontology_path: str = Field(
        default="data/maintenance.owl",
        env="ONTOLOGY_PATH"
    )

    # Self-Correction Loop Settings
    max_correction_iterations: int = Field(default=5, env="MAX_ITERATIONS")
    llm_temperature: float = Field(default=0.0, env="LLM_TEMPERATURE")

    # Application Settings
    app_name: str = "Logic-Guard-Layer"
    debug: bool = Field(default=False, env="DEBUG")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

**Example `.env` file:**
```
# OpenRouter Configuration
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=tngtech/deepseek-r1t2-chimera:free

# Optional: Override defaults
# LLM_TIMEOUT=60.0
# LLM_MAX_RETRIES=3
# MAX_ITERATIONS=5
# LLM_TEMPERATURE=0.0

# Application
DEBUG=false
```

### 2.2 Pydantic Models (`models/`)

**entities.py:**
- `Component` - Base component model
- `Motor`, `Pump`, `Valve`, `Sensor` - Specific component types
- `MaintenanceEvent` - Maintenance record
- `Measurement` - Sensor measurements

**responses.py:**
- `ValidationRequest` - Input request model
- `ValidationResponse` - Output response model
- `Violation` - Constraint violation details
- `ConsistencyResult` - Reasoning result

---

## Phase 3: Ontology Module

### 3.1 Ontology File (`data/maintenance.owl`)
Create OWL 2 ontology for maintenance domain:

**Concepts (Classes):**
```
Komponente (Component)
├── RotierendeKomponente (Rotating)
│   ├── Motor
│   └── Pumpe (Pump)
├── StatischeKomponente (Static)
│   ├── Ventil (Valve)
│   └── Behaelter (Container)
└── Sensor
    ├── Drucksensor (Pressure)
    └── Temperatursensor (Temperature)

Ereignis (Event)
├── Wartungsereignis (Maintenance)
├── Ausfallereignis (Failure)
└── Messereignis (Measurement)
```

**Datatype Properties:**
- `hatBetriebsstunden` (hasOperatingHours): Component → integer
- `hatMaxLebensdauer` (hasMaxLifespan): Component → integer
- `hatWartungsintervall` (hasMaintenanceInterval): Component → integer
- `hatSeriennummer` (hasSerialNumber): Component → string
- `hatDatum` (hasDate): Event → date
- `hatDruckBar` (hasPressureBar): Measurement → float
- `hatTemperaturC` (hasTemperatureC): Measurement → float

**Axioms/Constraints:**
1. `hatBetriebsstunden >= 0`
2. `hatMaxLebensdauer > 0`
3. `hatWartungsintervall > 0`
4. `hatWartungsintervall <= hatMaxLebensdauer`
5. `hatBetriebsstunden <= hatMaxLebensdauer`
6. `hatDruckBar` range: 0-350 bar (standard hydraulics)
7. `hatTemperaturC` range: -40 to +150°C

### 3.2 Ontology Loader (`ontology/loader.py`)
- Load OWL file using Owlready2
- Initialize reasoner (HermiT)
- Singleton pattern for ontology instance
- Lazy loading support

### 3.3 Constraint Definitions (`ontology/constraints.py`)
- Define constraint types: Type, Range, Relational, Temporal, Physical
- Rule-based fast checks in Python
- Integration with OWL reasoning for complex cases

---

## Phase 4: LLM Integration (OpenRouter)

### 4.1 LLM Client (`llm/client.py`)

**Provider:** OpenRouter API (https://openrouter.ai)
**Default Model:** `tngtech/deepseek-r1t2-chimera:free`

**OpenRouter Configuration:**
```python
from dataclasses import dataclass
from typing import Optional
import httpx

@dataclass
class OpenRouterConfig:
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "tngtech/deepseek-r1t2-chimera:free"
    timeout: float = 60.0
    max_retries: int = 3
```

**Client Implementation:**
```python
class OpenRouterClient:
    """
    LLM client for OpenRouter API.
    Default model: tngtech/deepseek-r1t2-chimera:free
    """

    def __init__(self, config: OpenRouterConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            base_url=config.base_url,
            timeout=config.timeout,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "HTTP-Referer": "https://logic-guard-layer.app",
                "X-Title": "Logic-Guard-Layer",
                "Content-Type": "application/json"
            }
        )

    async def complete(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 4096
    ) -> str:
        """
        Generate completion using OpenRouter API.

        Args:
            prompt: The input prompt
            model: Model to use (defaults to tngtech/deepseek-r1t2-chimera:free)
            temperature: Sampling temperature (0 for deterministic)
            max_tokens: Maximum tokens in response

        Returns:
            Generated text response
        """
        payload = {
            "model": model or self.config.default_model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.post(
                    "/chat/completions",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise LLMError(f"OpenRouter API error: {e}")

            except httpx.RequestError as e:
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                raise LLMError(f"Request failed: {e}")

        raise LLMError("Max retries exceeded")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


class LLMError(Exception):
    """Exception for LLM-related errors."""
    pass
```

**Environment Variables (`.env`):**
```
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=tngtech/deepseek-r1t2-chimera:free
```

**Features:**
- Async HTTP client using httpx
- Retry logic with exponential backoff for rate limits
- Configurable model (defaults to `tngtech/deepseek-r1t2-chimera:free`)
- Temperature=0 for deterministic parsing
- Proper error handling and custom exceptions

### 4.2 Prompt Templates (`llm/prompts.py`)

**Parsing Prompt:**
```
Analysiere den folgenden technischen Text und extrahiere
strukturierte Informationen gemäß dem Schema:

SCHEMA:
{schema_json}

TEXT:
{input_text}

Antworte ausschließlich mit validem JSON. Keine Erklärungen.
```

**Correction Prompt:**
```
Der folgende Text enthält logische Fehler oder Inkonsistenzen:

ORIGINAL:
{original_text}

ERKANNTE PROBLEME:
{violations_list}

ANFORDERUNGEN:
- Korrigiere den Text, sodass alle genannten Probleme behoben sind
- Behalte alle korrekten Informationen unverändert bei
- Ändere nur die fehlerhaften Werte/Aussagen

KORRIGIERTER TEXT:
```

---

## Phase 5: Core Components

### 5.1 Semantic Parser (`core/parser.py`)

**Pipeline:**
1. Generate parsing prompt from schema + input text
2. Call LLM with temperature=0
3. Parse JSON response
4. Validate against schema
5. Map to ontology instances

**Error Handling:**
- Invalid JSON → retry with explicit JSON instruction
- Missing fields → targeted follow-up query
- Type errors → attempt coercion or report error

### 5.2 Reasoning Module (`core/reasoner.py`)

**Two-Strategy Approach:**

1. **Fast Rule-Based Checks:**
   - Numeric range validation
   - Relational constraint checks
   - Type validation
   - Implemented in pure Python for speed

2. **OWL Reasoning (HermiT):**
   - Complex logical inference
   - Full ontology consistency check
   - Used for edge cases

**Output Format:**
```python
@dataclass
class ConsistencyResult:
    is_consistent: bool
    violations: list[Violation]
    checked_constraints: int
    processing_time_ms: float
```

### 5.3 Self-Correction Loop (`core/corrector.py`)

**Algorithm:**
```
1. Parse input text
2. Check consistency
3. If consistent → return success
4. If not consistent:
   a. Check for cycle (seen this output before?)
   b. Generate correction prompt with violations
   c. Call LLM for corrected text
   d. Increment iteration counter
   e. If max_iterations reached → return best result
   f. Go to step 1 with corrected text
```

**Safeguards:**
- Maximum iterations (default: 5)
- Cycle detection via output hashing
- Escalating prompt specificity
- Track best result (fewest violations)
- Graceful degradation with confidence score

### 5.4 Orchestrator (`core/orchestrator.py`)

**Main Class:**
```python
from config import settings
from llm.client import OpenRouterClient, OpenRouterConfig

class LogicGuardLayer:
    """
    Main orchestrator for the Logic-Guard-Layer system.
    Uses OpenRouter API with tngtech/deepseek-r1t2-chimera:free model.
    """

    def __init__(
        self,
        ontology_path: str = None,
        max_iterations: int = None
    ):
        # Load configuration
        ontology_path = ontology_path or settings.ontology_path
        max_iterations = max_iterations or settings.max_correction_iterations

        # Initialize OpenRouter LLM client
        llm_config = OpenRouterConfig(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            default_model=settings.openrouter_model,
            timeout=settings.llm_timeout,
            max_retries=settings.llm_max_retries
        )
        self.llm_client = OpenRouterClient(llm_config)

        # Initialize components
        self.ontology = load_ontology(ontology_path)
        self.parser = SemanticParser(self.llm_client, self.ontology.schema)
        self.reasoner = ReasoningModule(self.ontology)
        self.corrector = SelfCorrectionLoop(
            self.llm_client,
            max_iterations,
            temperature=settings.llm_temperature
        )

    async def validate(self, text: str) -> ValidationResult:
        """Validate text against the ontology."""
        return await self.corrector.run(text, self.parser, self.reasoner)

    async def close(self):
        """Cleanup resources."""
        await self.llm_client.close()
```

---

## Phase 6: API Layer

### 6.1 FastAPI Application (`main.py`)

**Endpoints:**
- `POST /validate` - Main validation endpoint
- `GET /health` - Health check
- `GET /ontology/concepts` - List ontology concepts
- `GET /ontology/constraints` - List active constraints

**Request/Response:**
```python
@app.post("/validate", response_model=ValidationResponse)
async def validate(request: ValidationRequest):
    result = await logic_guard.validate(
        text=request.text,
        schema=request.schema_name
    )
    return ValidationResponse(
        success=result.success,
        data=result.data,
        violations=[v.dict() for v in result.violations],
        iterations=result.iterations,
        confidence=result.confidence
    )
```

---

## Phase 7: Frontend (Jinja2 Templates)

### 7.1 Template Setup (`main.py` additions)

**Configure Jinja2 with FastAPI:**
```python
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Logic-Guard-Layer")

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="web/templates")
```

### 7.2 Web Routes (`web/routes.py`)

**HTML Page Endpoints:**
```python
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Dashboard/home page."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Logic-Guard-Layer"
    })

@router.get("/validate", response_class=HTMLResponse)
async def validate_form(request: Request):
    """Validation input form."""
    return templates.TemplateResponse("validate.html", {
        "request": request,
        "title": "Validate Text"
    })

@router.post("/validate", response_class=HTMLResponse)
async def validate_submit(request: Request, text: str = Form(...)):
    """Process validation and show results."""
    result = await logic_guard.validate(text)
    return templates.TemplateResponse("results.html", {
        "request": request,
        "title": "Validation Results",
        "result": result,
        "original_text": text
    })

@router.get("/history", response_class=HTMLResponse)
async def history(request: Request):
    """Validation history page."""
    return templates.TemplateResponse("history.html", {
        "request": request,
        "title": "Validation History",
        "validations": validation_history
    })

@router.get("/ontology", response_class=HTMLResponse)
async def ontology_browser(request: Request):
    """Ontology browser/explorer."""
    return templates.TemplateResponse("ontology.html", {
        "request": request,
        "title": "Ontology Browser",
        "concepts": ontology.get_concepts(),
        "constraints": ontology.get_constraints()
    })
```

### 7.3 Base Template (`templates/base.html`)

**Retro Terminal Layout:**
```html
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} | Logic-Guard-Layer</title>
    <!-- Google Font: VT323 for authentic terminal look -->
    <link href="https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap" rel="stylesheet">
    <link href="{{ url_for('static', path='css/style.css') }}" rel="stylesheet">
</head>
<body class="terminal-body">
    <!-- Scanline overlay effect -->
    <div class="scanlines"></div>

    {% include "components/navbar.html" %}

    <main class="terminal-container">
        <div class="terminal-header">
            <span class="terminal-title">> {{ title }}</span>
            <span class="terminal-cursor">_</span>
        </div>
        <div class="terminal-content">
            {% block content %}{% endblock %}
        </div>
    </main>

    {% include "components/footer.html" %}

    <script src="{{ url_for('static', path='js/app.js') }}"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

### 7.4 Home/Dashboard Page (`templates/index.html`)

**Dashboard Features:**
- System status overview
- Quick validation form
- Recent validations summary
- Statistics (total validations, success rate, avg iterations)

```html
{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h1>Logic-Guard-Layer Dashboard</h1>
        <p class="lead">Neuro-symbolische Validierung von KI-Outputs</p>
    </div>
</div>

<!-- Stats Cards -->
<div class="row mb-4">
    <div class="col-md-3">
        <div class="card bg-primary text-white">
            <div class="card-body">
                <h5 class="card-title">Total Validations</h5>
                <h2>{{ stats.total }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-success text-white">
            <div class="card-body">
                <h5 class="card-title">Success Rate</h5>
                <h2>{{ stats.success_rate }}%</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-info text-white">
            <div class="card-body">
                <h5 class="card-title">Avg. Iterations</h5>
                <h2>{{ stats.avg_iterations }}</h2>
            </div>
        </div>
    </div>
    <div class="col-md-3">
        <div class="card bg-warning">
            <div class="card-body">
                <h5 class="card-title">Constraints Active</h5>
                <h2>{{ stats.constraints_count }}</h2>
            </div>
        </div>
    </div>
</div>

<!-- Quick Validation -->
<div class="card mb-4">
    <div class="card-header">
        <h5>Quick Validation</h5>
    </div>
    <div class="card-body">
        <form action="/validate" method="post">
            <div class="mb-3">
                <textarea class="form-control" name="text" rows="4"
                    placeholder="Paste technical text to validate..."></textarea>
            </div>
            <button type="submit" class="btn btn-primary">Validate</button>
        </form>
    </div>
</div>

<!-- Recent Validations -->
<div class="card">
    <div class="card-header">
        <h5>Recent Validations</h5>
    </div>
    <div class="card-body">
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Status</th>
                    <th>Violations</th>
                    <th>Iterations</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
                {% for v in recent_validations %}
                <tr>
                    <td>{{ v.timestamp }}</td>
                    <td>
                        {% if v.success %}
                        <span class="badge bg-success">Valid</span>
                        {% else %}
                        <span class="badge bg-danger">Invalid</span>
                        {% endif %}
                    </td>
                    <td>{{ v.violations|length }}</td>
                    <td>{{ v.iterations }}</td>
                    <td><a href="/results/{{ v.id }}">View</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
```

### 7.5 Validation Form Page (`templates/validate.html`)

**Features:**
- Large text input area
- Schema/domain selector dropdown
- Example text buttons
- Real-time character count
- Submit with loading indicator

```html
{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-lg-8 mx-auto">
        <h1>Text Validierung</h1>
        <p>Geben Sie technischen Text ein, der gegen die Ontologie validiert werden soll.</p>

        <form action="/validate" method="post" id="validation-form">
            <div class="mb-3">
                <label for="schema" class="form-label">Domäne/Schema</label>
                <select class="form-select" name="schema" id="schema">
                    <option value="maintenance" selected>Technische Wartung</option>
                    <option value="quality">Qualitätssicherung</option>
                </select>
            </div>

            <div class="mb-3">
                <label for="text" class="form-label">Eingabetext</label>
                <textarea class="form-control" name="text" id="text" rows="10"
                    placeholder="Technischen Text hier eingeben..." required></textarea>
                <div class="form-text">
                    <span id="char-count">0</span> Zeichen
                </div>
            </div>

            <div class="mb-3">
                <label class="form-label">Beispiele laden:</label>
                <div class="btn-group">
                    <button type="button" class="btn btn-outline-secondary btn-sm"
                        onclick="loadExample('motor')">Motor-Wartung</button>
                    <button type="button" class="btn btn-outline-secondary btn-sm"
                        onclick="loadExample('pump')">Hydraulikpumpe</button>
                    <button type="button" class="btn btn-outline-secondary btn-sm"
                        onclick="loadExample('error')">Mit Fehlern</button>
                </div>
            </div>

            <button type="submit" class="btn btn-primary btn-lg" id="submit-btn">
                <span class="spinner-border spinner-border-sm d-none" id="loading"></span>
                Validieren
            </button>
        </form>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
const examples = {
    motor: `Der Motor M1 hat 15.000 Betriebsstunden bei einer maximalen
Lebensdauer von 50.000 Stunden. Das Wartungsintervall beträgt
5.000 Stunden. Die letzte Wartung wurde am 12.03.2024 durchgeführt.`,
    pump: `Die Hydraulikpumpe HP-01 zeigt einen Betriebsdruck von 280 bar
bei 8.000 Betriebsstunden. Die maximale Lebensdauer beträgt
20.000 Stunden.`,
    error: `Die Hydraulikpumpe HP-01 zeigt einen Betriebsdruck von 420 bar
bei 12.000 Betriebsstunden. Die maximale Lebensdauer beträgt
10.000 Stunden. Das nächste Wartungsintervall ist auf 15.000 Stunden eingestellt.`
};

function loadExample(key) {
    document.getElementById('text').value = examples[key];
    updateCharCount();
}

function updateCharCount() {
    const count = document.getElementById('text').value.length;
    document.getElementById('char-count').textContent = count;
}

document.getElementById('text').addEventListener('input', updateCharCount);

document.getElementById('validation-form').addEventListener('submit', function() {
    document.getElementById('loading').classList.remove('d-none');
    document.getElementById('submit-btn').disabled = true;
});
</script>
{% endblock %}
```

### 7.6 Results Page (`templates/results.html`)

**Features:**
- Success/failure status banner
- Original text display
- Extracted structured data (JSON viewer)
- Violations list with severity indicators
- Correction iterations timeline
- Corrected text (if applicable)
- Actions: retry, copy, download report

```html
{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-12">
        <!-- Status Banner -->
        {% if result.success %}
        <div class="alert alert-success">
            <h4><i class="bi bi-check-circle"></i> Validierung erfolgreich</h4>
            <p>Der Text ist konsistent mit der Ontologie.</p>
        </div>
        {% else %}
        <div class="alert alert-danger">
            <h4><i class="bi bi-x-circle"></i> Validierung fehlgeschlagen</h4>
            <p>{{ result.violations|length }} Constraint-Verletzung(en) gefunden.</p>
        </div>
        {% endif %}

        <!-- Summary Stats -->
        <div class="row mb-4">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <h6>Iterationen</h6>
                        <h3>{{ result.iterations }}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <h6>Geprüfte Constraints</h6>
                        <h3>{{ result.checked_constraints }}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <h6>Verarbeitungszeit</h6>
                        <h3>{{ result.processing_time_ms }}ms</h3>
                    </div>
                </div>
            </div>
        </div>

        <!-- Original Text -->
        <div class="card mb-4">
            <div class="card-header">
                <h5>Originaltext</h5>
            </div>
            <div class="card-body">
                <pre class="bg-light p-3">{{ original_text }}</pre>
            </div>
        </div>

        <!-- Extracted Data -->
        <div class="card mb-4">
            <div class="card-header">
                <h5>Extrahierte Daten</h5>
            </div>
            <div class="card-body">
                <pre class="bg-dark text-light p-3"><code>{{ result.data | tojson(indent=2) }}</code></pre>
            </div>
        </div>

        <!-- Violations -->
        {% if result.violations %}
        <div class="card mb-4">
            <div class="card-header bg-danger text-white">
                <h5>Constraint-Verletzungen</h5>
            </div>
            <div class="card-body">
                {% for v in result.violations %}
                <div class="card mb-2 border-danger">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <h6 class="text-danger">{{ v.type }}</h6>
                            <span class="badge bg-secondary">{{ v.constraint }}</span>
                        </div>
                        <p class="mb-1">{{ v.message }}</p>
                        {% if v.entity %}
                        <small class="text-muted">Entität: {{ v.entity }}</small>
                        {% endif %}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        <!-- Iteration Timeline -->
        {% if result.iterations > 1 %}
        <div class="card mb-4">
            <div class="card-header">
                <h5>Korrektur-Verlauf</h5>
            </div>
            <div class="card-body">
                <ul class="timeline">
                    {% for iter in result.iteration_history %}
                    <li class="timeline-item">
                        <span class="badge bg-primary">Iteration {{ iter.number }}</span>
                        <p>{{ iter.violations_count }} Verletzungen</p>
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        {% endif %}

        <!-- Actions -->
        <div class="d-flex gap-2">
            <a href="/validate" class="btn btn-primary">Neue Validierung</a>
            <button class="btn btn-outline-secondary" onclick="copyResults()">
                Ergebnis kopieren
            </button>
            <a href="/api/results/{{ result.id }}/download" class="btn btn-outline-secondary">
                Report herunterladen
            </a>
        </div>
    </div>
</div>
{% endblock %}
```

### 7.7 Ontology Browser Page (`templates/ontology.html`)

**Features:**
- Hierarchical concept tree view
- Concept details panel
- Properties list per concept
- Active constraints table
- Search/filter functionality

```html
{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-12">
        <h1>Ontologie Browser</h1>
        <p>Erkunden Sie die Domänenontologie und aktive Constraints.</p>
    </div>
</div>

<div class="row">
    <!-- Concept Tree -->
    <div class="col-md-4">
        <div class="card">
            <div class="card-header">
                <h5>Konzepte</h5>
                <input type="text" class="form-control form-control-sm"
                    placeholder="Suchen..." id="concept-search">
            </div>
            <div class="card-body">
                <ul class="concept-tree" id="concept-tree">
                    {% for concept in concepts %}
                    <li class="concept-item" data-concept="{{ concept.name }}">
                        <span class="concept-name">{{ concept.name }}</span>
                        {% if concept.children %}
                        <ul>
                            {% for child in concept.children %}
                            <li class="concept-item" data-concept="{{ child.name }}">
                                <span class="concept-name">{{ child.name }}</span>
                            </li>
                            {% endfor %}
                        </ul>
                        {% endif %}
                    </li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </div>

    <!-- Concept Details -->
    <div class="col-md-8">
        <div class="card mb-4" id="concept-details">
            <div class="card-header">
                <h5>Konzept Details</h5>
            </div>
            <div class="card-body">
                <p class="text-muted">Wählen Sie ein Konzept aus der Liste.</p>
            </div>
        </div>

        <!-- Constraints Table -->
        <div class="card">
            <div class="card-header">
                <h5>Aktive Constraints</h5>
            </div>
            <div class="card-body">
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Typ</th>
                            <th>Regel</th>
                            <th>Beschreibung</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for c in constraints %}
                        <tr>
                            <td>{{ c.id }}</td>
                            <td><span class="badge bg-info">{{ c.type }}</span></td>
                            <td><code>{{ c.expression }}</code></td>
                            <td>{{ c.description }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### 7.8 Reusable Components

**`components/navbar.html`:**
```html
<nav class="terminal-nav">
    <a href="/" class="brand">LOGIC-GUARD-LAYER</a>
    <a href="/">Dashboard</a>
    <a href="/validate">Validieren</a>
    <a href="/history">Verlauf</a>
    <a href="/ontology">Ontologie</a>
    <a href="/api/docs" style="float: right;">API</a>
</nav>
```

**`components/footer.html`:**
```html
<footer class="terminal-footer">
    LOGIC-GUARD-LAYER v1.0.0 | Neuro-Symbolic AI Validation System |
    Model: {{ config.openrouter_model }}
</footer>
```

**`components/violation_card.html`:**
```html
<div class="violation-item">
    <div class="violation-type">{{ violation.type }}</div>
    <div>Constraint: {{ violation.constraint }}</div>
    <div>{{ violation.message }}</div>
    {% if violation.entity %}
    <div style="color: var(--terminal-green-dim);">Entity: {{ violation.entity }}</div>
    {% endif %}
</div>
```

**`components/loading.html`:**
```html
<div class="terminal-loading">
    Processing<span class="loading-dots"></span>
</div>
```

### 7.9 Static Assets

**`static/css/style.css`:**
```css
/* ============================================
   LOGIC-GUARD-LAYER - RETRO TERMINAL THEME
   Green phosphor CRT monitor aesthetic
   ============================================ */

:root {
    /* Terminal Colors */
    --terminal-bg: #0a0a0a;
    --terminal-green: #00ff41;
    --terminal-green-dim: #00cc33;
    --terminal-green-bright: #33ff66;
    --terminal-green-glow: rgba(0, 255, 65, 0.4);
    --terminal-amber: #ffb000;
    --terminal-red: #ff3333;
    --terminal-cyan: #00ffff;

    /* Fonts */
    --font-terminal: 'VT323', 'Share Tech Mono', 'Courier New', monospace;
    --font-size-base: 18px;
    --font-size-lg: 24px;
    --font-size-xl: 32px;
}

/* ============================================
   BASE STYLES
   ============================================ */

* {
    box-sizing: border-box;
}

html, body {
    margin: 0;
    padding: 0;
    height: 100%;
}

.terminal-body {
    background-color: var(--terminal-bg);
    color: var(--terminal-green);
    font-family: var(--font-terminal);
    font-size: var(--font-size-base);
    line-height: 1.4;
    min-height: 100vh;
    position: relative;
    overflow-x: hidden;
}

/* CRT Scanline Effect */
.scanlines {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 1000;
    background: repeating-linear-gradient(
        0deg,
        rgba(0, 0, 0, 0.15),
        rgba(0, 0, 0, 0.15) 1px,
        transparent 1px,
        transparent 2px
    );
}

/* Screen flicker animation */
@keyframes flicker {
    0% { opacity: 0.97; }
    50% { opacity: 1; }
    100% { opacity: 0.98; }
}

.terminal-body::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(
        ellipse at center,
        transparent 0%,
        rgba(0, 0, 0, 0.3) 100%
    );
    pointer-events: none;
    z-index: 999;
}

/* ============================================
   TERMINAL CONTAINER
   ============================================ */

.terminal-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    position: relative;
    z-index: 1;
}

.terminal-header {
    border-bottom: 2px solid var(--terminal-green);
    padding-bottom: 10px;
    margin-bottom: 20px;
}

.terminal-title {
    font-size: var(--font-size-xl);
    text-shadow: 0 0 10px var(--terminal-green-glow);
}

/* Blinking cursor */
.terminal-cursor {
    animation: blink 1s step-end infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}

.terminal-content {
    animation: flicker 0.15s infinite;
}

/* ============================================
   NAVIGATION BAR
   ============================================ */

.terminal-nav {
    background: var(--terminal-bg);
    border-bottom: 1px solid var(--terminal-green-dim);
    padding: 10px 20px;
    position: sticky;
    top: 0;
    z-index: 100;
}

.terminal-nav a {
    color: var(--terminal-green);
    text-decoration: none;
    margin-right: 30px;
    font-size: var(--font-size-base);
    transition: all 0.2s ease;
}

.terminal-nav a:hover {
    color: var(--terminal-green-bright);
    text-shadow: 0 0 10px var(--terminal-green-glow);
}

.terminal-nav a::before {
    content: '> ';
}

.terminal-nav .brand {
    font-size: var(--font-size-lg);
    font-weight: bold;
}

.terminal-nav .brand::before {
    content: '[';
}

.terminal-nav .brand::after {
    content: ']';
}

/* ============================================
   TERMINAL CARDS / PANELS
   ============================================ */

.terminal-card {
    background: rgba(0, 20, 0, 0.5);
    border: 1px solid var(--terminal-green-dim);
    padding: 15px;
    margin-bottom: 20px;
}

.terminal-card-header {
    border-bottom: 1px dashed var(--terminal-green-dim);
    padding-bottom: 10px;
    margin-bottom: 10px;
    font-size: var(--font-size-lg);
}

.terminal-card-header::before {
    content: '### ';
}

/* ============================================
   STATS DISPLAY
   ============================================ */

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
    margin-bottom: 20px;
}

.stat-box {
    border: 1px solid var(--terminal-green-dim);
    padding: 15px;
    text-align: center;
}

.stat-box .stat-value {
    font-size: 48px;
    text-shadow: 0 0 20px var(--terminal-green-glow);
}

.stat-box .stat-label {
    color: var(--terminal-green-dim);
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 2px;
}

/* ============================================
   FORMS
   ============================================ */

.terminal-input,
.terminal-textarea,
.terminal-select {
    background: var(--terminal-bg);
    border: 1px solid var(--terminal-green-dim);
    color: var(--terminal-green);
    font-family: var(--font-terminal);
    font-size: var(--font-size-base);
    padding: 10px;
    width: 100%;
    outline: none;
}

.terminal-input:focus,
.terminal-textarea:focus,
.terminal-select:focus {
    border-color: var(--terminal-green);
    box-shadow: 0 0 10px var(--terminal-green-glow);
}

.terminal-textarea {
    min-height: 200px;
    resize: vertical;
}

.terminal-select option {
    background: var(--terminal-bg);
    color: var(--terminal-green);
}

/* ============================================
   BUTTONS
   ============================================ */

.terminal-btn {
    background: transparent;
    border: 2px solid var(--terminal-green);
    color: var(--terminal-green);
    font-family: var(--font-terminal);
    font-size: var(--font-size-base);
    padding: 10px 25px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-transform: uppercase;
    letter-spacing: 2px;
}

.terminal-btn:hover {
    background: var(--terminal-green);
    color: var(--terminal-bg);
    box-shadow: 0 0 20px var(--terminal-green-glow);
}

.terminal-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.terminal-btn::before {
    content: '[ ';
}

.terminal-btn::after {
    content: ' ]';
}

.terminal-btn-small {
    padding: 5px 15px;
    font-size: 14px;
}

/* ============================================
   TABLES
   ============================================ */

.terminal-table {
    width: 100%;
    border-collapse: collapse;
}

.terminal-table th,
.terminal-table td {
    border: 1px solid var(--terminal-green-dim);
    padding: 10px;
    text-align: left;
}

.terminal-table th {
    background: rgba(0, 255, 65, 0.1);
    text-transform: uppercase;
    letter-spacing: 1px;
}

.terminal-table tr:hover {
    background: rgba(0, 255, 65, 0.05);
}

/* ============================================
   STATUS BADGES
   ============================================ */

.terminal-badge {
    display: inline-block;
    padding: 2px 8px;
    font-size: 14px;
    border: 1px solid;
}

.terminal-badge-success {
    color: var(--terminal-green);
    border-color: var(--terminal-green);
}

.terminal-badge-error {
    color: var(--terminal-red);
    border-color: var(--terminal-red);
}

.terminal-badge-warning {
    color: var(--terminal-amber);
    border-color: var(--terminal-amber);
}

.terminal-badge-info {
    color: var(--terminal-cyan);
    border-color: var(--terminal-cyan);
}

/* ============================================
   ALERTS / STATUS BANNERS
   ============================================ */

.terminal-alert {
    padding: 15px;
    margin-bottom: 20px;
    border: 2px solid;
}

.terminal-alert-success {
    border-color: var(--terminal-green);
    background: rgba(0, 255, 65, 0.1);
}

.terminal-alert-success::before {
    content: '[SUCCESS] ';
}

.terminal-alert-error {
    border-color: var(--terminal-red);
    color: var(--terminal-red);
    background: rgba(255, 51, 51, 0.1);
}

.terminal-alert-error::before {
    content: '[ERROR] ';
}

.terminal-alert-warning {
    border-color: var(--terminal-amber);
    color: var(--terminal-amber);
    background: rgba(255, 176, 0, 0.1);
}

.terminal-alert-warning::before {
    content: '[WARNING] ';
}

/* ============================================
   CODE / JSON DISPLAY
   ============================================ */

.terminal-code {
    background: rgba(0, 0, 0, 0.5);
    border: 1px solid var(--terminal-green-dim);
    padding: 15px;
    overflow-x: auto;
    white-space: pre-wrap;
    font-size: 16px;
}

/* ============================================
   VIOLATIONS LIST
   ============================================ */

.violation-item {
    border: 1px solid var(--terminal-red);
    padding: 10px;
    margin-bottom: 10px;
    background: rgba(255, 51, 51, 0.05);
}

.violation-item .violation-type {
    color: var(--terminal-red);
    font-weight: bold;
}

.violation-item .violation-type::before {
    content: '!!! ';
}

/* ============================================
   CONCEPT TREE (Ontology Browser)
   ============================================ */

.concept-tree {
    list-style: none;
    padding-left: 0;
}

.concept-tree ul {
    list-style: none;
    padding-left: 20px;
    border-left: 1px dashed var(--terminal-green-dim);
    margin-left: 10px;
}

.concept-item {
    padding: 5px 0;
    cursor: pointer;
}

.concept-item::before {
    content: '├── ';
    color: var(--terminal-green-dim);
}

.concept-item:last-child::before {
    content: '└── ';
}

.concept-item:hover .concept-name {
    color: var(--terminal-green-bright);
    text-shadow: 0 0 5px var(--terminal-green-glow);
}

.concept-item.selected .concept-name {
    color: var(--terminal-green-bright);
    text-decoration: underline;
}

/* ============================================
   TIMELINE (Correction iterations)
   ============================================ */

.terminal-timeline {
    list-style: none;
    padding-left: 0;
    border-left: 2px solid var(--terminal-green-dim);
    margin-left: 10px;
}

.terminal-timeline li {
    padding: 10px 0 10px 20px;
    position: relative;
}

.terminal-timeline li::before {
    content: '●';
    position: absolute;
    left: -7px;
    color: var(--terminal-green);
}

/* ============================================
   LOADING ANIMATION
   ============================================ */

.terminal-loading {
    display: inline-block;
}

.terminal-loading::after {
    content: '';
    animation: loading-dots 1.5s infinite;
}

@keyframes loading-dots {
    0% { content: '.'; }
    33% { content: '..'; }
    66% { content: '...'; }
    100% { content: ''; }
}

/* ============================================
   FOOTER
   ============================================ */

.terminal-footer {
    border-top: 1px solid var(--terminal-green-dim);
    padding: 20px;
    text-align: center;
    color: var(--terminal-green-dim);
    font-size: 14px;
    margin-top: 40px;
}

.terminal-footer::before {
    content: '--- ';
}

.terminal-footer::after {
    content: ' ---';
}

/* ============================================
   RESPONSIVE ADJUSTMENTS
   ============================================ */

@media (max-width: 768px) {
    :root {
        --font-size-base: 16px;
        --font-size-lg: 20px;
        --font-size-xl: 26px;
    }

    .terminal-nav a {
        display: block;
        margin: 10px 0;
    }

    .stats-grid {
        grid-template-columns: 1fr 1fr;
    }
}

/* ============================================
   ASCII ART SUPPORT
   ============================================ */

.ascii-art {
    font-size: 12px;
    line-height: 1.2;
    white-space: pre;
    color: var(--terminal-green-dim);
}
```

**`static/js/app.js`:**
```javascript
// Logic-Guard-Layer Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(t => new bootstrap.Tooltip(t));

    // Concept tree click handler
    document.querySelectorAll('.concept-item').forEach(item => {
        item.addEventListener('click', function(e) {
            e.stopPropagation();
            const conceptName = this.dataset.concept;
            loadConceptDetails(conceptName);

            // Update selection
            document.querySelectorAll('.concept-item').forEach(i =>
                i.classList.remove('selected'));
            this.classList.add('selected');
        });
    });

    // Concept search
    const searchInput = document.getElementById('concept-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            document.querySelectorAll('.concept-item').forEach(item => {
                const name = item.dataset.concept.toLowerCase();
                item.style.display = name.includes(query) ? '' : 'none';
            });
        });
    }
});

async function loadConceptDetails(conceptName) {
    const detailsPanel = document.getElementById('concept-details');
    try {
        const response = await fetch(`/api/ontology/concepts/${conceptName}`);
        const data = await response.json();

        detailsPanel.innerHTML = `
            <div class="card-header">
                <h5>${data.name}</h5>
            </div>
            <div class="card-body">
                <p><strong>Überklasse:</strong> ${data.parent || 'Keine'}</p>
                <h6>Properties:</h6>
                <ul>
                    ${data.properties.map(p => `
                        <li><code>${p.name}</code>: ${p.range}</li>
                    `).join('')}
                </ul>
                <h6>Zugehörige Constraints:</h6>
                <ul>
                    ${data.constraints.map(c => `
                        <li>${c.expression}</li>
                    `).join('')}
                </ul>
            </div>
        `;
    } catch (error) {
        console.error('Error loading concept details:', error);
    }
}

function copyResults() {
    const resultsText = document.querySelector('.card-body pre')?.textContent;
    if (resultsText) {
        navigator.clipboard.writeText(resultsText);
        alert('Ergebnis in Zwischenablage kopiert!');
    }
}
```

---

## Phase 8: Testing

### 8.1 Unit Tests
- `test_parser.py` - Parser functionality
- `test_reasoner.py` - Constraint checking
- `test_corrector.py` - Self-correction loop

### 8.2 Integration Tests
- End-to-end validation flow
- Error scenarios
- Edge cases from documentation exercises

### 8.3 Test Cases from Documentation

**Test 1: Hydraulic Pump Validation**
```python
input_text = """
Die Hydraulikpumpe HP-01 zeigt einen Betriebsdruck von 420 bar bei
12.000 Betriebsstunden. Die maximale Lebensdauer beträgt 10.000 Stunden.
Das nächste Wartungsintervall ist auf 15.000 Stunden eingestellt.
"""
# Expected violations:
# - Pressure 420 > 350 bar max
# - Operating hours 12000 > max lifespan 10000
# - Maintenance interval 15000 > max lifespan 10000
```

**Test 2: Temporal Inconsistency**
```python
input_text = """
Die Pumpe wurde am 15.03.2024 ausgetauscht, nachdem sie am 20.03.2024
ausgefallen war.
"""
# Expected violation: Repair before failure (temporal constraint)
```

---

## Phase 8: Performance Optimization

### 8.1 Caching Strategy
- Layer 1: In-memory ontology cache (TBox)
- Layer 2: Reasoning cache for frequent checks
- Layer 3: LLM response cache for identical prompts

### 8.2 Parallelization
- Check independent constraints in parallel
- Async LLM calls

### 8.3 Incremental Reasoning
- Only check constraints affected by new assertions
- Skip unrelated axioms

---

## Implementation Order

| Step | Component | Priority | Estimated Effort |
|------|-----------|----------|------------------|
| 1 | Project structure (src layout) | High | Small |
| 2 | pyproject.toml & packaging config | High | Small |
| 3 | Configuration (Pydantic settings) | High | Small |
| 4 | Pydantic data models | High | Small |
| 5 | Ontology file (maintenance.owl) | High | Medium |
| 6 | Ontology loader (Owlready2) | High | Small |
| 7 | OpenRouter LLM client | High | Medium |
| 8 | Prompt templates | High | Small |
| 9 | Semantic parser | High | Medium |
| 10 | Constraint definitions | High | Medium |
| 11 | Reasoning module | High | Medium |
| 12 | Self-correction loop | High | Medium |
| 13 | Orchestrator | High | Small |
| 14 | CLI module (click) | High | Small |
| 15 | FastAPI API endpoints | High | Small |
| 16 | Frontend: Base template (terminal theme) | High | Small |
| 17 | Frontend: Dashboard page | High | Medium |
| 18 | Frontend: Validation form page | High | Medium |
| 19 | Frontend: Results page | High | Medium |
| 20 | Frontend: Ontology browser page | Medium | Medium |
| 21 | Frontend: History page | Medium | Small |
| 22 | Frontend: Terminal CSS styling | Medium | Medium |
| 23 | Unit tests | Medium | Medium |
| 24 | Integration tests | Medium | Medium |
| 25 | Performance optimization | Low | Medium |

---

## Risk Mitigation

Based on the four core risks identified in the documentation:

### Semantic Loss
- Implement confidence scoring for extractions
- Flag uncertain values for manual review
- Iterative ontology improvement based on feedback

### Feedback Loop Stability
- Hard limit of 5 iterations
- Cycle detection via hashing
- Escalating prompt specificity
- Return best result on non-convergence

### Latency
- Rule-based fast checks before OWL reasoning
- Async operations throughout
- Caching at multiple layers

### Ontology Completeness
- Explicit documentation of what IS and IS NOT validated
- Feedback mechanism for false positives
- Regular ontology reviews with domain experts

---

## Success Criteria

1. **Functional:** System correctly validates maintenance reports against defined constraints
2. **Performance:** < 2 seconds for typical validation (single iteration)
3. **Reliability:** Self-correction loop converges in > 90% of cases within 5 iterations
4. **Testable:** > 80% test coverage on core components
5. **Extensible:** New domains can be added by swapping ontology file

---

## Next Steps

1. Create project structure with `src/` layout for pip packaging
2. Configure `pyproject.toml` with dependencies and CLI entry points
3. Set up configuration with Pydantic Settings and `.env` support
4. Define Pydantic models for entities and responses
5. Create maintenance ontology OWL file
6. Implement ontology loader with Owlready2
7. Build OpenRouter LLM client (default model: `tngtech/deepseek-r1t2-chimera:free`)
8. Create prompt templates for parsing and correction
9. Implement semantic parser
10. Build reasoning module with constraint checking
11. Create self-correction loop with convergence safeguards
12. Wire up orchestrator to coordinate all components
13. Implement CLI with Click (serve, validate, info commands)
14. Add FastAPI API endpoints
15. Create retro terminal theme base template
16. Build all frontend pages with terminal styling
17. Write unit and integration tests
18. Test pip installation (`pip install -e .`)

**Quick Start After Implementation:**
```bash
# Install
pip install -e .

# Configure
export OPENROUTER_API_KEY=your-key-here

# Run web server
lgl serve

# Or validate from CLI
lgl validate "Der Motor M1 hat 15.000 Betriebsstunden..."
```
