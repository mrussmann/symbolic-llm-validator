# Architecture Overview

This document describes the architecture of Logic-Guard-Layer, a neuro-symbolic validation system for technical maintenance documents.

## Table of Contents

- [System Overview](#system-overview)
- [Component Architecture](#component-architecture)
- [Data Flow](#data-flow)
- [Design Patterns](#design-patterns)
- [Concurrency Model](#concurrency-model)
- [Extension Points](#extension-points)

---

## System Overview

Logic-Guard-Layer implements a **three-stage pipeline** architecture for validating and correcting LLM outputs:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Logic-Guard-Layer                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Input     │───▶│   Parser    │───▶│  Reasoner   │───▶│  Corrector  │  │
│  │   Text      │    │   (LLM)     │    │ (Ontology)  │    │   (LLM)     │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                            │                  │                  │          │
│                            ▼                  ▼                  ▼          │
│                     ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│                     │  Parsed     │    │ Violations  │    │  Corrected  │  │
│                     │  Data       │    │   List      │    │    Text     │  │
│                     └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Architectural Principles

1. **Separation of Concerns**: Each stage has a single responsibility
2. **Async-First**: All I/O operations are asynchronous
3. **Dependency Injection**: Components are loosely coupled via constructor injection
4. **Fail-Safe**: Errors are caught and handled gracefully
5. **Observable**: Extensive logging at each stage

---

## Component Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Presentation Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │
│  │  FastAPI     │  │    CLI       │  │   Python     │                       │
│  │  REST API    │  │  Interface   │  │    SDK       │                       │
│  └──────────────┘  └──────────────┘  └──────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Orchestration Layer                                │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         Orchestrator                                  │   │
│  │  - Manages pipeline execution                                         │   │
│  │  - Coordinates between stages                                         │   │
│  │  - Handles errors and retries                                         │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Core Layer                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │
│  │   Semantic   │  │  Reasoning   │  │    Self-     │                       │
│  │   Parser     │  │   Module     │  │  Correction  │                       │
│  └──────────────┘  └──────────────┘  └──────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Infrastructure Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │
│  │  OpenRouter  │  │   Ontology   │  │   Config     │                       │
│  │   Client     │  │   Manager    │  │   Manager    │                       │
│  └──────────────┘  └──────────────┘  └──────────────┘                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Component Descriptions

#### Orchestrator (`core/orchestrator.py`)

The central coordinator that manages the validation pipeline.

```python
class Orchestrator:
    """
    Main orchestrator for the Logic-Guard-Layer pipeline.

    Responsibilities:
    - Initialize and manage component lifecycle
    - Execute the three-stage pipeline
    - Handle errors and produce results
    """

    def __init__(
        self,
        llm_client: Optional[OpenRouterClient] = None,
        parser: Optional[SemanticParser] = None,
        reasoner: Optional[ReasoningModule] = None,
        corrector: Optional[SelfCorrectionLoop] = None,
        auto_correct: bool = True,
    ): ...

    async def process(self, text: str) -> PipelineResult: ...
    async def validate_only(self, text: str) -> PipelineResult: ...
```

#### Semantic Parser (`core/parser.py`)

Extracts structured data from unstructured German text using LLM.

```python
class SemanticParser:
    """
    Semantic parser that transforms unstructured text into structured data.

    Responsibilities:
    - Generate parsing prompts
    - Call LLM for extraction
    - Convert LLM output to domain models
    """

    async def parse(self, text: str) -> ParsedData: ...
    def extract_raw_values(self, parsed_data: ParsedData) -> dict: ...
```

#### Reasoning Module (`core/reasoner.py`)

Validates extracted data against ontology constraints.

```python
class ReasoningModule:
    """
    Reasoning module for checking data consistency against constraints.

    Responsibilities:
    - Load and manage constraints
    - Check data against all constraints
    - Report violations with details
    """

    def check_consistency(self, data: dict) -> ConsistencyResult: ...
    def check_single_constraint(self, constraint_id: str, data: dict) -> Optional[Violation]: ...
```

#### Self-Correction Loop (`core/corrector.py`)

Iteratively repairs text with constraint violations.

```python
class SelfCorrectionLoop:
    """
    Self-correction loop that iteratively repairs inconsistent text.

    Algorithm:
    1. Parse input text
    2. Check consistency against constraints
    3. If consistent → return success
    4. If not consistent:
       a. Check for cycle (seen this output before?)
       b. Generate correction prompt with violations
       c. Call LLM for corrected text
       d. Increment iteration counter
       e. If max_iterations reached → return best result
       f. Go to step 1 with corrected text
    """

    async def correct(self, text: str) -> CorrectionResult: ...
```

---

## Data Flow

### Request Processing Flow

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ Client  │────▶│ FastAPI │────▶│  Orch.  │────▶│ Parser  │────▶│   LLM   │
└─────────┘     └─────────┘     └─────────┘     └─────────┘     └─────────┘
                                      │               │               │
                                      │               │◀──────────────┘
                                      │               │
                                      │         ParsedData
                                      │               │
                                      ▼               ▼
                                ┌─────────┐     ┌─────────┐
                                │Reasoner │◀────│Raw Values│
                                └─────────┘     └─────────┘
                                      │
                              ┌───────┴───────┐
                              │               │
                         Consistent      Violations
                              │               │
                              ▼               ▼
                        ┌─────────┐     ┌─────────┐
                        │ Return  │     │Corrector│
                        │ Success │     └─────────┘
                        └─────────┘           │
                                              ▼
                                        ┌─────────┐
                                        │   LLM   │
                                        └─────────┘
                                              │
                                              ▼
                                        (Loop back to Parser)
```

### Data Models Flow

```
Input Text (str)
      │
      ▼
┌─────────────────┐
│   ParsedData    │
├─────────────────┤
│ - components[]  │
│ - events[]      │
│ - raw_values{}  │
│ - confidence    │
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ ConsistencyResult│
├─────────────────┤
│ - is_consistent │
│ - violations[]  │
│ - checked_count │
│ - time_ms       │
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ CorrectionResult│
├─────────────────┤
│ - original_text │
│ - corrected_text│
│ - is_consistent │
│ - iterations    │
│ - steps[]       │
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ PipelineResult  │
├─────────────────┤
│ - original_text │
│ - final_text    │
│ - violations[]  │
│ - is_valid      │
│ - was_corrected │
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ValidationResponse│
├─────────────────┤
│ - success       │
│ - data          │
│ - violations[]  │
│ - iterations    │
└─────────────────┘
```

---

## Design Patterns

### Singleton Pattern

Used for shared resources that should have only one instance:

```python
# Orchestrator singleton
_orchestrator: Optional[Orchestrator] = None

async def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator

async def reset_orchestrator():
    global _orchestrator
    if _orchestrator is not None:
        await _orchestrator.close()
        _orchestrator = None
```

```python
# OntologyManager singleton (class-level)
class OntologyManager:
    _instance: Optional["OntologyManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
```

### Dependency Injection

Components accept dependencies via constructor:

```python
class Orchestrator:
    def __init__(
        self,
        llm_client: Optional[OpenRouterClient] = None,  # Injected
        parser: Optional[SemanticParser] = None,        # Injected
        reasoner: Optional[ReasoningModule] = None,     # Injected
        corrector: Optional[SelfCorrectionLoop] = None, # Injected
    ):
        self.llm_client = llm_client
        self.parser = parser
        self.reasoner = reasoner or ReasoningModule()  # Default if not provided
        self.corrector = corrector
```

### Strategy Pattern

Constraints use the strategy pattern for flexible validation:

```python
@dataclass
class Constraint:
    id: str
    name: str
    type: ConstraintType
    description: str
    expression: str
    check_fn: Callable[[dict], Optional[Violation]]  # Strategy
    applicable_types: list[str]

# Each constraint has its own check function (strategy)
def check_operating_hours_non_negative(data: dict) -> Optional[Violation]:
    hours = data.get("operating_hours")
    if hours is not None and hours < 0:
        return Violation(...)
    return None
```

### Factory Pattern

Used for creating clients from configuration:

```python
def create_client_from_settings() -> OpenRouterClient:
    """Factory function to create LLM client from settings."""
    from logic_guard_layer.config import settings

    return OpenRouterClient(
        api_key=settings.openrouter_api_key,
        model=settings.openrouter_model,
    )
```

---

## Concurrency Model

### Async/Await Architecture

All I/O-bound operations are asynchronous:

```python
class SemanticParser:
    async def parse(self, text: str) -> ParsedData:
        # Async LLM call
        raw_data = await self.llm_client.complete_json(
            prompt=prompt,
            temperature=0.0,
        )
        return self._convert_to_parsed_data(raw_data)
```

### Event Loop Integration

FastAPI handles the event loop:

```python
@app.post("/api/validate")
async def validate_text(request: ValidationRequest):
    orchestrator = await get_orchestrator()
    result = await orchestrator.process(request.text)
    return ValidationResponse.from_result(result)
```

### Resource Cleanup

Proper cleanup of async resources:

```python
class Orchestrator:
    async def close(self):
        """Clean up resources."""
        if self.llm_client is not None:
            await self.llm_client.close()

class OpenRouterClient:
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
```

---

## Extension Points

### Adding New Constraints

1. Define the check function in `ontology/constraints.py`:

```python
def check_new_constraint(data: dict) -> Optional[Violation]:
    value = data.get("property_name")
    if value is not None and not is_valid(value):
        return Violation(
            type=ViolationType.RANGE_ERROR,
            constraint="property_name constraint",
            message=f"Invalid value: {value}",
            property_name="property_name",
            actual_value=value,
            expected_value="expected range",
        )
    return None
```

2. Add to `MAINTENANCE_CONSTRAINTS` list:

```python
MAINTENANCE_CONSTRAINTS.append(
    Constraint(
        id="C9",
        name="New constraint name",
        type=ConstraintType.RANGE,
        description="Description",
        expression="expression",
        check_fn=check_new_constraint,
        applicable_types=["Component"],
    )
)
```

### Adding New Component Types

1. Add to `ComponentType` enum in `models/entities.py`:

```python
class ComponentType(str, Enum):
    # ... existing types
    NEW_TYPE = "NewTypeName"
```

2. Update type mapping in `core/parser.py`:

```python
type_map = {
    # ... existing mappings
    "newtypename": ComponentType.NEW_TYPE,
}
```

### Adding New API Endpoints

1. Add endpoint in `main.py`:

```python
@app.post("/api/new-endpoint")
async def new_endpoint(request: NewRequest) -> NewResponse:
    # Implementation
    return NewResponse(...)
```

2. Add request/response models in `models/responses.py`:

```python
class NewRequest(BaseModel):
    field: str

class NewResponse(BaseModel):
    result: str
```

### Custom Ontology Support

1. Create ontology schema JSON:

```json
{
    "name": "custom-ontology",
    "version": "1.0.0",
    "definitions": {
        "concepts": {
            "MyConcept": {"description": "..."}
        },
        "constraints": [
            {"id": "C1", "name": "...", "expression": "..."}
        ]
    }
}
```

2. Register via API:

```python
POST /api/ontology/upload
{
    "name": "custom-ontology",
    "schema": { ... }
}
```

---

## Security Considerations

### Authentication

- Session-based authentication for admin endpoints
- Hardcoded credentials (development only - change for production!)

```python
# main.py - CHANGE THESE FOR PRODUCTION
ADMIN_USERNAME = "myjoe"
ADMIN_PASSWORD = "design41."
```

### API Security

- CORS configured for development (allow all origins)
- Rate limiting via OpenRouter

### Input Validation

- Pydantic models validate all input
- Field constraints (min/max length, value ranges)

```python
class ValidationRequest(BaseModel):
    text: str = Field(..., min_length=1)
    max_iterations: Optional[int] = Field(None, ge=1, le=10)
```

---

## Performance Considerations

### LLM Call Optimization

- Temperature 0.0 for parsing (deterministic)
- Temperature 0.3 for correction (slight variation)
- Retry logic with exponential backoff

### Caching Opportunities

- Ontology loaded once at startup
- Constraints list cached
- Consider adding response caching for repeated queries

### Monitoring Points

- Processing time tracked at each stage
- Iteration count for corrections
- Violation counts and types
