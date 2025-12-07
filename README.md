# Logic-Guard-Layer

A neuro-symbolic validation system that combines LLM capabilities with ontology-based reasoning to detect logical inconsistencies in technical documents, with a focus on physics-based constraints for industrial equipment.

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

1. **Parses** unstructured natural language text into structured data using an LLM
2. **Validates** the extracted data against a formal ontology with physics-based constraints
3. **Corrects** any logical inconsistencies through an iterative self-correction loop
4. **Verifies** LLM responses against expected results using sample-based testing
5. **Returns** validated, consistent technical information

## Features

- **Semantic Parsing**: Extracts structured equipment data from natural language text (maintenance reports, emails, technician notes)
- **Physics-Based Validation**: 16 constraint rules based on thermodynamics and physical laws
- **Self-Correction Loop**: Up to 5 iterations to fix constraint violations
- **LLM Response Verification**: Sample texts with expected results to verify LLM extraction accuracy
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
lgl validate "The gas turbine GT-01 has 95,000 operating hours with a maximum lifespan of 80,000 hours."

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
  -d '{"text": "Pump P-101 has 15,000 operating hours.", "auto_correct": true}'

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
        "The centrifugal pump has 95,000 operating hours with a maximum lifespan of 80,000 hours."
    )

    print(f"Valid: {result.is_valid}")
    print(f"Violations: {len(result.final_violations)}")
    if result.was_corrected:
        print(f"Corrected: {result.final_text}")

    await orchestrator.close()

asyncio.run(main())
```

## Physics-Based Constraints

The system enforces 16 validation rules based on physical laws:

| ID | Name | Type | Physical Law |
|----|------|------|--------------|
| C1 | Operating hours positive | range | - |
| C2 | Lifespan limit | temporal | - |
| C3 | First Law of Thermodynamics | physical | Energy Conservation |
| C4 | NPSH Cavitation Protection | physical | Bernoulli Equation |
| C5 | Heat Exchanger Energy Balance | physical | First Law |
| C6 | Isentropic Compression | physical | Isentropic Process |
| C7 | Pump Power | physical | Energy Conservation |
| C8 | Battery SOC | range | 0-100% |
| C9 | Battery Cycles | temporal | Cycle limit |
| C10 | Heat Pump Carnot Limit | physical | Second Law (Carnot) |
| C11 | Wind Turbine Betz Limit | physical | Betz Law (59.3%) |
| C12 | Temperature positive (Kelvin) | physical | Third Law |
| C13 | Pressure ratio | physical | >= 1 |
| C14 | Power output | physical | Energy Conservation |
| C15 | Gas Turbine Efficiency | physical | Brayton Cycle |
| C16 | Capacity positive | range | - |

## Equipment Ontology

```
Equipment
├── RotatingMachine
│   ├── Pump
│   │   ├── CentrifugalPump
│   │   └── PositiveDisplacementPump
│   ├── Compressor
│   ├── Motor
│   └── Generator
├── HeatTransferEquipment
│   ├── HeatExchanger
│   ├── HeatPump
│   └── Cooler
├── EnergyStorage
│   ├── BatteryStorage
│   ├── ThermalStorage
│   └── HydrogenStorage
└── PowerGeneration
    ├── GasTurbine
    ├── WindTurbine
    ├── SolarPanel
    └── CHP (Combined Heat and Power)
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Input Text (Natural Language)           │
│    Maintenance reports, emails, technician notes, etc.      │
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
│     Checks constraints against physics-based ontology        │
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

## Sample Texts & LLM Verification

The system includes sample texts with expected results to verify LLM extraction accuracy:

### Structured Samples
- **Gas Turbine**: Operating hours, efficiency, pressure ratio validation
- **Wind Turbine**: Betz limit and power coefficient checks
- **Heat Pump**: Carnot COP limit validation
- **Battery Storage**: SOC and cycle limit checks
- **Centrifugal Pump**: NPSH cavitation protection

### Prose/Natural Language Samples
The system can parse unstructured natural language text:

| Sample | Description | Status |
|--------|-------------|--------|
| Maintenance Report | Formal maintenance report with equipment data | Valid |
| Technician Notes | Informal field notes about compressor status | Valid |
| Urgent Email | Email reporting critical pump issues | Violations detected |
| Inspection Log | Monthly inspection with multiple issues | Violations detected |
| Verbal Report | Transcribed voice memo about cavitation risk | Violations detected |

**Example Prose Input:**
```
MAINTENANCE REPORT - Q4 2024
Subject: Cooling Pump Inspection

The cooling water pump (Model: KSB Etanorm 50-200) in cooling circuit 3
was inspected today. The pump has been in continuous operation for
approximately 22,000 hours since initial commissioning. The maximum
expected service life according to manufacturer specifications is
60,000 operating hours.

Current measured values:
- NPSH available: 6.5 meters water column
- NPSH required: 4.2 meters (according to pump curve)
- Hydraulic efficiency: 78%
- Motor power consumption: 15 kW
```

The LLM extracts structured data which is then validated against physics constraints.

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
│   ├── loader.py         # Ontology loader
│   ├── manager.py        # Ontology management
│   └── constraints.py    # Constraint definitions
├── data/
│   ├── physics_ontology.json  # Physics-based ontology
│   └── sample_ontology.json   # Sample ontology
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
- Interactive ontology visualization
- Sample text verification with expected vs actual comparison

Access the interface at `http://localhost:8000` after starting the server.

## Example

**Input:**
```
The gas turbine GT-01 in power plant section A has accumulated 95,000
operating hours with a maximum rated lifespan of 80,000 hours. Current
system pressure is 385 bar.
```

**Validation Result:**
```
[ERROR] Found 2 constraint violation(s)
  - RELATIONAL: Operating hours (95,000) exceed maximum lifespan (80,000)
  - RANGE: Pressure (385 bar) exceeds maximum allowed (350 bar)

[CORRECTED TEXT]
The gas turbine GT-01 in power plant section A has accumulated 75,000
operating hours with a maximum rated lifespan of 80,000 hours. Current
system pressure is 320 bar.
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

# Run with auto-reload via CLI
lgl serve --reload

# Check code style
ruff check src/
```

## Testing

The project includes a comprehensive pytest test suite with 340+ tests covering all major modules.

### Running Tests

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=logic_guard_layer --cov-report=html

# Run specific test file
pytest tests/test_sample_verification.py

# Run specific test class
pytest tests/test_constraints.py::TestCheckPressureRange

# Run tests matching a pattern
pytest -k "parser"
```

### Test Structure

| File | Tests | Coverage |
|------|-------|----------|
| `tests/conftest.py` | Shared fixtures | All modules |
| `tests/test_models.py` | 62 tests | entities.py, responses.py |
| `tests/test_constraints.py` | 53 tests | constraints.py |
| `tests/test_ontology_manager.py` | 38 tests | manager.py |
| `tests/test_parser.py` | 28 tests | parser.py |
| `tests/test_reasoner.py` | 33 tests | reasoner.py |
| `tests/test_corrector.py` | 23 tests | corrector.py |
| `tests/test_orchestrator.py` | 26 tests | orchestrator.py |
| `tests/test_api.py` | 30 tests | main.py (FastAPI) |
| `tests/test_sample_verification.py` | 46 tests | Sample verification |

### Test Categories

- **Unit Tests**: Individual function and class testing
- **Integration Tests**: Component interaction testing
- **API Tests**: FastAPI endpoint testing with TestClient
- **Async Tests**: Tests for async functions using pytest-asyncio
- **Sample Verification Tests**: LLM response verification with expected results

### Writing Tests

Tests use pytest fixtures defined in `tests/conftest.py`:

```python
import pytest

def test_valid_equipment(sample_equipment):
    """Test using a fixture from conftest.py"""
    assert sample_equipment.name == "GT-01"
    assert sample_equipment.operating_hours == 45000

@pytest.mark.asyncio
async def test_parser(mock_llm_client):
    """Test async parser with mocked LLM client"""
    from logic_guard_layer.core.parser import SemanticParser
    parser = SemanticParser(mock_llm_client)
    result = await parser.parse("Test text")
    assert result is not None
```

## License

MIT License

## References

- [OpenRouter API](https://openrouter.ai/)
- [OWL 2 Web Ontology Language](https://www.w3.org/TR/owl2-overview/)
- [Owlready2 Documentation](https://owlready2.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
