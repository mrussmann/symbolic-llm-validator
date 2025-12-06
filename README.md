# Logic-Guard-Layer

A neuro-symbolic validation system that combines LLM capabilities with ontology-based reasoning to detect and correct logical inconsistencies in technical maintenance documents.

```
  _    ___   ___ ___ ___    ___ _   _   _   ___ ___
 | |  / _ \ / __|_ _/ __|  / __| | | | /_\ | _ \   \
 | |_| (_) | (_ || | (__  | (_ | |_| |/ _ \|   / |) |
 |____\___/ \___|___\___|  \___|\___//_/ \_\_|_\___/

  _      ___   _____ ___
 | |    /_\ \ / / __| _ \
 | |__ / _ \ V /| _||   /
 |____/_/ \_\_| |___|_|_\
```

## Overview

Logic-Guard-Layer addresses the challenge of LLM hallucinations in technical domains by implementing a hybrid architecture that:

1. **Parses** unstructured German technical text into structured data using an LLM
2. **Validates** the extracted data against a formal OWL 2 ontology with domain constraints
3. **Corrects** any logical inconsistencies through an iterative self-correction loop
4. **Returns** validated, consistent technical information

## Features

- **Semantic Parsing**: Extracts structured component data from German maintenance text
- **Ontology-Based Validation**: 8 constraint rules covering range, relational, and physical limits
- **Self-Correction Loop**: Up to 5 iterations to fix constraint violations
- **REST API**: FastAPI-based endpoints for validation
- **Web Interface**: Retro terminal-themed UI with green phosphor CRT aesthetic
- **CLI Tool**: Command-line interface for scripting and automation
- **OpenRouter Integration**: Uses `tngtech/deepseek-r1t2-chimera:free` by default

## Installation

```bash
# Install from PyPI (when published)
pip install logic-guard-layer

# Or install from source
git clone <repository-url>
cd logic-guard-layer
pip install .

# Or install in development mode
pip install -e .
```

After installation, the `lgl` and `logic-guard` commands will be available globally.

## Quick Start

### Option 1: Run without installation (Development)

```bash
# 1. Clone and enter directory
git clone <repository-url>
cd logic-guard-layer

# 2. Install dependencies from requirements.txt
pip install -r requirements.txt

# 3. Set your OpenRouter API key
export OPENROUTER_API_KEY=sk-or-v1-xxxxx

# 4. Run directly with auto-reload
python run.py --reload

# 5. Open http://localhost:8000 in your browser
```

### Option 2: Install as package

```bash
# 1. Install the package
pip install logic-guard-layer

# 2. Set your OpenRouter API key
export OPENROUTER_API_KEY=sk-or-v1-xxxxx

# 3. Start the web server
lgl serve

# 4. Open http://localhost:8000 in your browser
```

## Configuration

Create a `.env` file in the project root:

```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=tngtech/deepseek-r1t2-chimera:free
MAX_CORRECTION_ITERATIONS=5
DEBUG=false
```

Or set environment variables directly:

```bash
export OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

## Usage

### CLI Commands

```bash
# Show system information
lgl info

# List all validation constraints
lgl constraints

# Validate text directly
lgl validate "Motor M1 hat 15.000 Betriebsstunden bei einer maximalen Lebensdauer von 20.000 Stunden."

# Validate from file
lgl validate -f input.txt -o output.txt

# Validate without auto-correction
lgl validate --no-correct "Text to check"

# Start the web server
lgl serve --port 8000

# Start in development mode with auto-reload
lgl serve --reload
```

### API Endpoints

```bash
# Health check
curl http://localhost:8000/api/health

# Validate text
curl -X POST http://localhost:8000/api/validate \
  -H "Content-Type: application/json" \
  -d '{"text": "Motor M1 hat 15.000 Betriebsstunden.", "auto_correct": true}'

# Get constraints
curl http://localhost:8000/api/constraints

# Get validation history
curl http://localhost:8000/api/history

# Get ontology schema
curl http://localhost:8000/api/ontology
```

### Python API

```python
import asyncio
from logic_guard_layer import Orchestrator

async def main():
    orchestrator = Orchestrator()

    result = await orchestrator.process(
        "Motor M1 hat 25.000 Betriebsstunden bei einer maximalen Lebensdauer von 20.000 Stunden."
    )

    print(f"Valid: {result.is_valid}")
    print(f"Violations: {len(result.final_violations)}")
    if result.was_corrected:
        print(f"Corrected: {result.final_text}")

    await orchestrator.close()

asyncio.run(main())
```

## Constraints

The system enforces these validation rules:

| ID | Name | Type | Expression |
|----|------|------|------------|
| C1 | Operating hours non-negative | range | `betriebsstunden >= 0` |
| C2 | Max lifespan positive | range | `max_lebensdauer > 0` |
| C3 | Maintenance interval positive | range | `wartungsintervall > 0` |
| C4 | Maintenance interval <= lifespan | relational | `wartungsintervall <= max_lebensdauer` |
| C5 | Operating hours <= lifespan | relational | `betriebsstunden <= max_lebensdauer` |
| C6 | Hydraulic pressure range | physical | `0 <= druck_bar <= 350` |
| C7 | Temperature range | physical | `-40 <= temperatur_c <= 150` |
| C8 | RPM range | physical | `0 <= drehzahl <= 10000` |

## Component Hierarchy

```
Komponente (Component)
├── RotierendeKomponente (Rotating)
│   ├── Motor
│   │   └── Elektromotor
│   └── Pumpe
│       ├── Hydraulikpumpe
│       └── Vakuumpumpe
├── StatischeKomponente (Static)
│   ├── Ventil
│   │   ├── Regelventil
│   │   └── Absperrventil
│   └── Behaelter
└── Sensor
    ├── Drucksensor
    └── Temperatursensor
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Input Text (German)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Semantic Parser (LLM)                     │
│              Extracts structured data via OpenRouter         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Reasoning Module                          │
│         Checks constraints against OWL 2 ontology           │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
              Consistent?          Violations?
                    │                   │
                    ▼                   ▼
              ┌─────────┐    ┌─────────────────────┐
              │ Return  │    │  Self-Correction    │
              │ Valid   │    │  Loop (max 5 iter)  │
              └─────────┘    └─────────────────────┘
                                       │
                                       ▼
                              ┌─────────────────┐
                              │ Corrected Text  │
                              └─────────────────┘
```

## Project Structure

```
src/logic_guard_layer/
├── __init__.py           # Package exports
├── __main__.py           # python -m support
├── cli.py                # Click CLI
├── config.py             # Pydantic settings
├── main.py               # FastAPI application
├── core/
│   ├── parser.py         # Semantic parser
│   ├── reasoner.py       # Constraint checking
│   ├── corrector.py      # Self-correction loop
│   └── orchestrator.py   # Pipeline orchestration
├── llm/
│   ├── client.py         # OpenRouter API client
│   └── prompts.py        # Prompt templates
├── models/
│   ├── entities.py       # Domain entities
│   └── responses.py      # API responses
├── ontology/
│   ├── loader.py         # OWL ontology loader
│   └── constraints.py    # Constraint definitions
├── data/
│   ├── maintenance.owl   # OWL 2 ontology
│   └── maintenance_schema.json
└── web/
    ├── templates/        # Jinja2 templates
    └── static/           # CSS/JS assets
```

## Web Interface

The web interface features a retro terminal aesthetic with:

- Green phosphor text on black background
- CRT scanline overlay effect
- Screen flicker animation
- VT323 monospace font

Access the interface at `http://localhost:8000` after starting the server.

## Example

**Input:**
```
Der Elektromotor M1 in Halle 3 hat aktuell 25.000 Betriebsstunden
bei einer maximalen Lebensdauer von 20.000 Stunden. Der aktuelle
Systemdruck beträgt 280 bar.
```

**Validation Result:**
```
[ERROR] Found 1 constraint violation(s)
  - RELATIONAL: Betriebsstunden (25000) überschreiten maximale Lebensdauer (20000)

[CORRECTED TEXT]
Der Elektromotor M1 in Halle 3 hat aktuell 18.000 Betriebsstunden
bei einer maximalen Lebensdauer von 20.000 Stunden. Der aktuelle
Systemdruck beträgt 280 bar.
```

## Development

### Running without pip install

```bash
# Run with auto-reload (watches src/ for changes)
python run.py --reload

# Custom port
python run.py --port 3000 --reload

# Debug mode
python run.py --reload --debug

# Show all options
python run.py --help
```

### Full development setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with auto-reload via CLI
lgl serve --reload

# Check code style
ruff check src/
```

## License

MIT License

## References

- [OpenRouter API](https://openrouter.ai/)
- [OWL 2 Web Ontology Language](https://www.w3.org/TR/owl2-overview/)
- [Owlready2 Documentation](https://owlready2.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
