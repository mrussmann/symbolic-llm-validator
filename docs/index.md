# Logic-Guard-Layer Developer Documentation

Welcome to the Logic-Guard-Layer developer documentation. This guide provides comprehensive information for developers who want to understand, extend, or contribute to the project.

## Table of Contents

1. [Architecture Overview](architecture.md)
2. [Core Modules](core-modules.md)
3. [API Reference](api-reference.md)
4. [Configuration](configuration.md)
5. [Testing Guide](testing.md)
6. [Contributing](contributing.md)

## Quick Links

- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Key Concepts](#key-concepts)

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- pip package manager
- OpenRouter API key

### Development Installation

```bash
# Clone the repository
git clone <repository-url>
cd logic-guard-layer

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### Running the Development Server

```bash
# Using the run script (recommended for development)
python run.py --reload

# Or using the CLI
lgl serve --reload

# Or using uvicorn directly
uvicorn logic_guard_layer.main:app --reload
```

---

## Project Structure

```
logic-guard-layer/
├── src/
│   └── logic_guard_layer/
│       ├── __init__.py           # Package exports
│       ├── __main__.py           # python -m support
│       ├── cli.py                # Click CLI commands
│       ├── config.py             # Pydantic settings
│       ├── main.py               # FastAPI application
│       ├── core/                 # Core pipeline modules
│       │   ├── __init__.py
│       │   ├── orchestrator.py   # Pipeline orchestration
│       │   ├── parser.py         # Semantic text parser
│       │   ├── reasoner.py       # Constraint validation
│       │   └── corrector.py      # Self-correction loop
│       ├── llm/                  # LLM integration
│       │   ├── __init__.py
│       │   ├── client.py         # OpenRouter API client
│       │   └── prompts.py        # Prompt templates
│       ├── models/               # Data models
│       │   ├── __init__.py
│       │   ├── entities.py       # Domain entities
│       │   └── responses.py      # API response models
│       ├── ontology/             # Ontology management
│       │   ├── __init__.py
│       │   ├── loader.py         # OWL ontology loader
│       │   ├── manager.py        # Ontology manager
│       │   └── constraints.py    # Constraint definitions
│       ├── data/                 # Data files
│       │   ├── maintenance.owl   # OWL 2 ontology
│       │   ├── maintenance_schema.json
│       │   └── sample_ontology.json
│       └── web/                  # Web interface
│           ├── __init__.py
│           ├── templates/        # Jinja2 HTML templates
│           └── static/           # CSS/JS assets
├── tests/                        # Test suite
│   ├── conftest.py              # Shared fixtures
│   ├── test_models.py
│   ├── test_constraints.py
│   ├── test_ontology_manager.py
│   ├── test_parser.py
│   ├── test_reasoner.py
│   ├── test_corrector.py
│   ├── test_orchestrator.py
│   └── test_api.py
├── docs/                         # Documentation
├── pyproject.toml               # Project configuration
├── requirements.txt             # Dependencies
├── run.py                       # Development runner
└── README.md
```

---

## Key Concepts

### Neuro-Symbolic Architecture

Logic-Guard-Layer implements a **neuro-symbolic hybrid architecture** that combines:

1. **Neural Component (LLM)**: Uses large language models for semantic understanding and text generation
2. **Symbolic Component (Ontology)**: Uses formal OWL 2 ontology and rule-based constraints for logical validation

This hybrid approach addresses the hallucination problem in LLMs by grounding their outputs in formal logic.

### Pipeline Stages

The validation pipeline consists of three main stages:

```
Input Text → [Parse] → [Validate] → [Correct] → Output
```

1. **Parse**: Extract structured data from unstructured German text using LLM
2. **Validate**: Check extracted data against ontology constraints
3. **Correct**: If violations found, iteratively repair the text (up to 5 iterations)

### Domain Model

The system is designed for **industrial maintenance domain** with:

- **Components**: Motors, pumps, valves, sensors, etc.
- **Properties**: Operating hours, lifespan, pressure, temperature, RPM
- **Constraints**: Range limits, relational rules, physical laws

### Constraint Types

| Type | Description | Example |
|------|-------------|---------|
| **Range** | Value bounds | `operating_hours >= 0` |
| **Relational** | Value relationships | `operating_hours <= max_lifespan` |
| **Physical** | Physical limits | `0 <= pressure <= 350 bar` |
| **Temporal** | Time-based rules | (Future extension) |
| **Type** | Type validation | Component type must exist in ontology |

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| **Language** | Python 3.11+ |
| **Web Framework** | FastAPI |
| **ASGI Server** | Uvicorn |
| **Data Validation** | Pydantic v2 |
| **HTTP Client** | httpx (async) |
| **Ontology** | OWL 2 / Owlready2 |
| **Templates** | Jinja2 |
| **CLI** | Click |
| **Testing** | pytest, pytest-asyncio |
| **LLM Provider** | OpenRouter |

---

## Next Steps

- Read the [Architecture Overview](architecture.md) for detailed system design
- Explore the [Core Modules](core-modules.md) for implementation details
- Check the [API Reference](api-reference.md) for endpoint documentation
- See the [Testing Guide](testing.md) for writing and running tests
- Review [Contributing](contributing.md) to contribute to the project
