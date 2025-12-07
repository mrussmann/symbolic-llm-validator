# Core Modules Documentation

This document provides detailed documentation for each core module in Logic-Guard-Layer.

## Table of Contents

- [Orchestrator](#orchestrator)
- [Semantic Parser](#semantic-parser)
- [Reasoning Module](#reasoning-module)
- [Self-Correction Loop](#self-correction-loop)
- [LLM Client](#llm-client)
- [Ontology Manager](#ontology-manager)
- [Data Models](#data-models)

---

## Orchestrator

**Location:** `src/logic_guard_layer/core/orchestrator.py`

The Orchestrator is the central component that coordinates the validation pipeline.

### Class: `Orchestrator`

```python
class Orchestrator:
    """
    Main orchestrator for the Logic-Guard-Layer pipeline.

    Pipeline stages:
    1. Parse input text → structured data
    2. Validate against ontology constraints
    3. If invalid, run self-correction loop
    4. Return final validated/corrected result
    """
```

#### Constructor

```python
def __init__(
    self,
    llm_client: Optional[OpenRouterClient] = None,
    parser: Optional[SemanticParser] = None,
    reasoner: Optional[ReasoningModule] = None,
    corrector: Optional[SelfCorrectionLoop] = None,
    auto_correct: bool = True,
):
    """
    Initialize the orchestrator.

    Args:
        llm_client: OpenRouter client (created from settings if not provided)
        parser: Semantic parser (created with llm_client if not provided)
        reasoner: Reasoning module (created with defaults if not provided)
        corrector: Self-correction loop (created if not provided)
        auto_correct: Whether to automatically correct invalid input
    """
```

#### Methods

##### `process(text: str) -> PipelineResult`

Process text through the complete pipeline.

```python
async def process(self, text: str) -> PipelineResult:
    """
    Process text through the complete pipeline.

    Args:
        text: Input text to validate and potentially correct

    Returns:
        PipelineResult with all processing details

    Example:
        orchestrator = Orchestrator()
        result = await orchestrator.process("Motor M1 hat 5000 Betriebsstunden.")
        print(f"Valid: {result.is_valid}")
    """
```

##### `validate_only(text: str) -> PipelineResult`

Validate text without correction.

```python
async def validate_only(self, text: str) -> PipelineResult:
    """
    Validate text without correction.

    Args:
        text: Input text to validate

    Returns:
        PipelineResult with validation results only (no corrections)
    """
```

##### `get_constraints_info() -> list[dict]`

Get information about all active constraints.

```python
async def get_constraints_info(self) -> list[dict]:
    """
    Get information about all active constraints.

    Returns:
        List of constraint information dictionaries with keys:
        - id: Constraint ID (e.g., "C1")
        - name: Human-readable name
        - type: Constraint type (range, relational, physical)
        - expression: Constraint expression
        - description: Detailed description
    """
```

##### `close()`

Clean up resources.

```python
async def close(self):
    """Clean up resources (close HTTP clients, etc.)."""
```

### Class: `PipelineResult`

```python
@dataclass
class PipelineResult:
    """Complete result from the Logic-Guard-Layer pipeline."""

    # Input
    original_text: str

    # Parsing stage
    parsed_data: Optional[ParsedData] = None
    parse_error: Optional[str] = None

    # Validation stage
    initial_consistency: Optional[ConsistencyResult] = None

    # Correction stage
    correction_result: Optional[CorrectionResult] = None

    # Final output
    final_text: str = ""
    final_parsed_data: Optional[ParsedData] = None
    final_violations: list[Violation] = None

    # Metrics
    total_processing_time_ms: float = 0.0

    @property
    def is_valid(self) -> bool:
        """Check if final result is valid (no violations)."""

    @property
    def was_corrected(self) -> bool:
        """Check if text was modified during processing."""
```

### Singleton Functions

```python
async def get_orchestrator() -> Orchestrator:
    """Get or create the singleton orchestrator instance."""

async def reset_orchestrator():
    """Reset the singleton orchestrator (useful for testing)."""
```

### Usage Example

```python
from logic_guard_layer.core.orchestrator import Orchestrator, get_orchestrator

# Using singleton
async def validate():
    orchestrator = await get_orchestrator()
    result = await orchestrator.process(
        "Motor M1 hat 25000 Betriebsstunden bei max 20000."
    )

    if result.is_valid:
        print("Text is valid!")
    else:
        print(f"Violations: {len(result.final_violations)}")
        if result.was_corrected:
            print(f"Corrected: {result.final_text}")

# Using custom instance
async def validate_custom():
    orchestrator = Orchestrator(auto_correct=False)
    result = await orchestrator.validate_only("Test text")
    await orchestrator.close()
```

---

## Semantic Parser

**Location:** `src/logic_guard_layer/core/parser.py`

The Semantic Parser extracts structured data from unstructured German text using LLM.

### Class: `SemanticParser`

```python
class SemanticParser:
    """
    Semantic parser that transforms unstructured text into structured data.
    Uses LLM for schema-guided parsing.
    """
```

#### Constructor

```python
def __init__(self, llm_client: OpenRouterClient):
    """
    Initialize the semantic parser.

    Args:
        llm_client: OpenRouter client for LLM calls
    """
```

#### Methods

##### `parse(text: str) -> ParsedData`

Parse unstructured text into structured data.

```python
async def parse(self, text: str) -> ParsedData:
    """
    Parse unstructured text into structured data.

    Args:
        text: The text to parse

    Returns:
        ParsedData containing extracted information

    Raises:
        ParserError: If parsing fails

    Example:
        parsed = await parser.parse(
            "Hydraulikpumpe HP-001 mit 5000 Betriebsstunden"
        )
        print(parsed.components[0].name)  # "HP-001"
    """
```

##### `extract_raw_values(parsed_data: ParsedData) -> dict`

Extract raw values for constraint checking.

```python
def extract_raw_values(self, parsed_data: ParsedData) -> dict:
    """
    Extract raw values for constraint checking.

    Args:
        parsed_data: Parsed data model

    Returns:
        Flat dictionary of values for constraint checking.
        Keys include both English and German variants:
        - operating_hours / betriebsstunden
        - max_lifespan / max_lebensdauer
        - pressure_bar / druck_bar
        - temperature_c / temperatur_c
        - rpm / drehzahl

    Example:
        values = parser.extract_raw_values(parsed_data)
        # {'name': 'HP-001', 'operating_hours': 5000, 'betriebsstunden': 5000, ...}
    """
```

### Internal Methods

##### `_convert_to_parsed_data(raw_data: dict) -> ParsedData`

Convert raw LLM output to ParsedData model.

##### `_create_component(data: dict) -> Optional[Component]`

Create a Component from extracted data.

##### `_safe_int(value: Any) -> Optional[int]`

Safely convert value to int, handling:
- None values
- String numbers
- Thousands separators (. and ,)

### Exception: `ParserError`

```python
class ParserError(Exception):
    """Exception for parser-related errors."""
    pass
```

### Usage Example

```python
from logic_guard_layer.core.parser import SemanticParser
from logic_guard_layer.llm.client import create_client_from_settings

async def parse_text():
    client = create_client_from_settings()
    parser = SemanticParser(client)

    try:
        parsed = await parser.parse("""
            Hydraulikpumpe HP-001:
            - Betriebsstunden: 5.000
            - Max. Lebensdauer: 20.000 Stunden
            - Druck: 280 bar
        """)

        for component in parsed.components:
            print(f"Component: {component.name}")
            print(f"Type: {component.type}")
            print(f"Hours: {component.operating_hours}")

        # Get raw values for constraint checking
        raw_values = parser.extract_raw_values(parsed)
        print(f"Raw values: {raw_values}")

    except ParserError as e:
        print(f"Parsing failed: {e}")

    finally:
        await client.close()
```

---

## Reasoning Module

**Location:** `src/logic_guard_layer/core/reasoner.py`

The Reasoning Module validates data against ontology constraints.

### Class: `ReasoningModule`

```python
class ReasoningModule:
    """
    Reasoning module for checking data consistency against constraints.
    Uses rule-based fast checks for common constraints.
    """
```

#### Constructor

```python
def __init__(self, constraints: Optional[list[Constraint]] = None):
    """
    Initialize the reasoning module.

    Args:
        constraints: List of constraints to check (uses defaults if not provided)
    """
```

#### Methods

##### `check_consistency(data: dict) -> ConsistencyResult`

Check if data is consistent with all constraints.

```python
def check_consistency(self, data: dict) -> ConsistencyResult:
    """
    Check if data is consistent with all constraints.

    Args:
        data: Dictionary of values to check. Supports both English
              and German keys (e.g., 'operating_hours' and 'betriebsstunden')

    Returns:
        ConsistencyResult with violations list

    Example:
        result = reasoner.check_consistency({
            'operating_hours': 25000,
            'max_lifespan': 20000
        })
        if not result.is_consistent:
            for v in result.violations:
                print(f"{v.type}: {v.message}")
    """
```

##### `check_single_constraint(constraint_id: str, data: dict) -> Optional[Violation]`

Check a single constraint by ID.

```python
def check_single_constraint(
    self, constraint_id: str, data: dict
) -> Optional[Violation]:
    """
    Check a single constraint by ID.

    Args:
        constraint_id: The constraint ID (e.g., "C1")
        data: Dictionary of values to check

    Returns:
        Violation if constraint is violated, None otherwise
    """
```

##### `get_applicable_constraints(component_type: str) -> list[Constraint]`

Get constraints applicable to a specific component type.

```python
def get_applicable_constraints(self, component_type: str) -> list[Constraint]:
    """
    Get constraints applicable to a specific component type.

    Args:
        component_type: The component type name (e.g., "Motor", "HydraulicPump")

    Returns:
        List of applicable constraints
    """
```

##### `get_constraints_summary() -> list[dict]`

Get a summary of all constraints for display.

```python
def get_constraints_summary(self) -> list[dict]:
    """
    Get a summary of all constraints for display.

    Returns:
        List of constraint summaries with keys:
        - id, name, type, expression, description
    """
```

### Class: `ConsistencyResult`

```python
class ConsistencyResult:
    """Result of a consistency check."""

    def __init__(
        self,
        is_consistent: bool,
        violations: list[Violation],
        checked_constraints: int,
        processing_time_ms: float,
    ):
        self.is_consistent = is_consistent
        self.violations = violations
        self.checked_constraints = checked_constraints
        self.processing_time_ms = processing_time_ms
```

### Usage Example

```python
from logic_guard_layer.core.reasoner import ReasoningModule

def validate_data():
    reasoner = ReasoningModule()

    # Check data with potential violations
    data = {
        'name': 'HP-001',
        'operating_hours': 25000,
        'max_lifespan': 20000,
        'pressure_bar': 400,  # Exceeds 350 bar limit
    }

    result = reasoner.check_consistency(data)

    print(f"Consistent: {result.is_consistent}")
    print(f"Checked: {result.checked_constraints} constraints")
    print(f"Time: {result.processing_time_ms:.2f}ms")

    for violation in result.violations:
        print(f"\n{violation.type.value}:")
        print(f"  Constraint: {violation.constraint}")
        print(f"  Message: {violation.message}")
        print(f"  Property: {violation.property_name}")
        print(f"  Actual: {violation.actual_value}")
        print(f"  Expected: {violation.expected_value}")
```

---

## Self-Correction Loop

**Location:** `src/logic_guard_layer/core/corrector.py`

The Self-Correction Loop iteratively repairs text with constraint violations.

### Class: `SelfCorrectionLoop`

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
```

#### Constructor

```python
def __init__(
    self,
    llm_client: OpenRouterClient,
    parser: SemanticParser,
    reasoner: ReasoningModule,
    max_iterations: int = 5,
):
    """
    Initialize the self-correction loop.

    Args:
        llm_client: OpenRouter client for LLM calls
        parser: Semantic parser for text extraction
        reasoner: Reasoning module for consistency checking
        max_iterations: Maximum correction attempts (default: 5)
    """
```

#### Methods

##### `correct(text: str) -> CorrectionResult`

Run the self-correction loop on input text.

```python
async def correct(self, text: str) -> CorrectionResult:
    """
    Run the self-correction loop on input text.

    Args:
        text: The text to validate and correct

    Returns:
        CorrectionResult with correction history and final state

    Example:
        result = await corrector.correct(
            "Motor M1 hat 25000 Betriebsstunden bei max 20000."
        )
        if result.is_consistent:
            print(f"Corrected in {result.iterations} iterations")
            print(f"New text: {result.corrected_text}")
    """
```

### Class: `CorrectionResult`

```python
@dataclass
class CorrectionResult:
    """Result of the complete correction process."""
    original_text: str
    corrected_text: str
    is_consistent: bool
    iterations: int
    max_iterations_reached: bool
    steps: list[CorrectionStep] = field(default_factory=list)
    final_violations: list[Violation] = field(default_factory=list)
    total_processing_time_ms: float = 0.0

    @property
    def was_corrected(self) -> bool:
        """Check if text was modified during correction."""
```

### Class: `CorrectionStep`

```python
@dataclass
class CorrectionStep:
    """A single step in the correction process."""
    iteration: int
    input_text: str
    output_text: str
    violations: list[Violation]
    is_consistent: bool
    processing_time_ms: float
```

### Usage Example

```python
from logic_guard_layer.core.corrector import SelfCorrectionLoop
from logic_guard_layer.core.parser import SemanticParser
from logic_guard_layer.core.reasoner import ReasoningModule
from logic_guard_layer.llm.client import create_client_from_settings

async def correct_text():
    client = create_client_from_settings()
    parser = SemanticParser(client)
    reasoner = ReasoningModule()

    corrector = SelfCorrectionLoop(
        llm_client=client,
        parser=parser,
        reasoner=reasoner,
        max_iterations=3
    )

    result = await corrector.correct(
        "Motor M1 hat 25000 Betriebsstunden bei max 20000 Stunden."
    )

    print(f"Original: {result.original_text}")
    print(f"Corrected: {result.corrected_text}")
    print(f"Consistent: {result.is_consistent}")
    print(f"Iterations: {result.iterations}")

    for step in result.steps:
        print(f"\nIteration {step.iteration}:")
        print(f"  Violations: {len(step.violations)}")
        print(f"  Time: {step.processing_time_ms:.2f}ms")

    await client.close()
```

---

## LLM Client

**Location:** `src/logic_guard_layer/llm/client.py`

The LLM Client handles communication with the OpenRouter API.

### Class: `OpenRouterClient`

```python
class OpenRouterClient:
    """Async HTTP client for OpenRouter API."""
```

#### Constructor

```python
def __init__(
    self,
    api_key: str,
    model: str = "tngtech/deepseek-r1t2-chimera:free",
    base_url: str = "https://openrouter.ai/api/v1",
    timeout: float = 60.0,
    max_retries: int = 3,
):
    """
    Initialize the OpenRouter client.

    Args:
        api_key: OpenRouter API key
        model: Model to use for completions
        base_url: API base URL
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
    """
```

#### Methods

##### `complete(prompt: str, ...) -> str`

Get a text completion from the LLM.

```python
async def complete(
    self,
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000,
    system_prompt: Optional[str] = None,
) -> str:
    """
    Get a text completion from the LLM.

    Args:
        prompt: The prompt to complete
        model: Override model (uses default if not provided)
        temperature: Sampling temperature (0.0 = deterministic)
        max_tokens: Maximum tokens to generate
        system_prompt: Optional system prompt

    Returns:
        Generated text

    Raises:
        LLMError: If the API call fails
    """
```

##### `complete_json(prompt: str, ...) -> dict`

Get a JSON completion from the LLM.

```python
async def complete_json(
    self,
    prompt: str,
    temperature: float = 0.0,
) -> dict:
    """
    Get a JSON completion from the LLM.

    Args:
        prompt: The prompt (should request JSON output)
        temperature: Sampling temperature

    Returns:
        Parsed JSON dictionary

    Raises:
        LLMError: If the API call fails or JSON parsing fails
    """
```

##### `close()`

Close the HTTP client.

```python
async def close(self):
    """Close the HTTP client."""
```

### Exception: `LLMError`

```python
class LLMError(Exception):
    """Exception for LLM-related errors."""
    pass
```

### Factory Function

```python
def create_client_from_settings() -> OpenRouterClient:
    """Create an OpenRouter client from application settings."""
```

### Usage Example

```python
from logic_guard_layer.llm.client import OpenRouterClient, create_client_from_settings

async def use_llm():
    # Using factory function
    client = create_client_from_settings()

    # Or create manually
    client = OpenRouterClient(
        api_key="sk-or-v1-xxx",
        model="anthropic/claude-3-haiku"
    )

    try:
        # Text completion
        response = await client.complete(
            prompt="Explain quantum computing in one sentence.",
            temperature=0.7
        )
        print(response)

        # JSON completion
        data = await client.complete_json(
            prompt="Extract data as JSON: Motor M1 has 5000 hours."
        )
        print(data)

    finally:
        await client.close()
```

---

## Ontology Manager

**Location:** `src/logic_guard_layer/ontology/manager.py`

The Ontology Manager handles multiple ontologies in memory.

### Class: `OntologyManager`

```python
class OntologyManager:
    """
    Manages multiple ontologies in-memory with support for uploading,
    listing, and switching between ontologies.
    """
```

#### Methods

##### `register(name: str, schema: dict, description: str) -> list[str]`

Register a new ontology.

```python
def register(self, name: str, schema: dict, description: str = "") -> list[str]:
    """
    Register a new ontology.

    Args:
        name: Unique ontology name
        schema: Ontology schema dictionary
        description: Optional description

    Returns:
        List of validation errors (empty if successful)
    """
```

##### `validate_schema(schema: dict) -> list[str]`

Validate ontology schema structure.

```python
def validate_schema(self, schema: dict) -> list[str]:
    """
    Validate that a schema has the required structure.

    Returns:
        List of error messages (empty if valid)
    """
```

##### `get(name: str) -> Optional[dict]`

Get an ontology schema by name.

##### `set_active(name: str) -> bool`

Set the active ontology.

##### `delete(name: str) -> bool`

Delete a custom ontology.

##### `list_ontologies() -> list[OntologyInfo]`

List all registered ontologies.

### Singleton Function

```python
def get_ontology_manager() -> OntologyManager:
    """Get the global OntologyManager instance."""
```

---

## Data Models

**Location:** `src/logic_guard_layer/models/`

### Entities (`models/entities.py`)

#### `ComponentType` Enum

```python
class ComponentType(str, Enum):
    MOTOR = "Motor"
    PUMP = "Pumpe"
    HYDRAULIC_PUMP = "Hydraulikpumpe"
    VALVE = "Ventil"
    SENSOR = "Sensor"
    PRESSURE_SENSOR = "Drucksensor"
    TEMPERATURE_SENSOR = "Temperatursensor"
    CONTAINER = "Behaelter"
    UNKNOWN = "Unbekannt"
```

#### `Component` Model

```python
class Component(BaseModel):
    name: str
    type: ComponentType = ComponentType.UNKNOWN
    serial_number: Optional[str] = None
    operating_hours: Optional[int] = None  # ge=0
    max_lifespan: Optional[int] = None     # gt=0
    maintenance_interval: Optional[int] = None  # gt=0
    measurements: list[Measurement] = []
```

#### `ParsedData` Model

```python
class ParsedData(BaseModel):
    components: list[Component] = []
    events: list[MaintenanceEvent] = []
    raw_values: dict[str, Any] = {}
    extraction_confidence: float = 1.0  # 0.0-1.0

    def get_component(self, name: str) -> Optional[Component]: ...
```

### Responses (`models/responses.py`)

#### `ViolationType` Enum

```python
class ViolationType(str, Enum):
    TYPE_ERROR = "TYPE_ERROR"
    RANGE_ERROR = "RANGE_ERROR"
    RELATIONAL_ERROR = "RELATIONAL_ERROR"
    TEMPORAL_ERROR = "TEMPORAL_ERROR"
    PHYSICAL_ERROR = "PHYSICAL_ERROR"
    PARSE_ERROR = "PARSE_ERROR"
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
```

#### `Violation` Model

```python
class Violation(BaseModel):
    type: ViolationType
    constraint: str
    message: str
    entity: Optional[str] = None
    property_name: Optional[str] = None
    actual_value: Optional[Any] = None
    expected_value: Optional[Any] = None
    severity: str = "error"
```

#### `ValidationRequest` Model

```python
class ValidationRequest(BaseModel):
    text: str  # min_length=1
    schema_name: str = "maintenance"
    max_iterations: Optional[int] = None  # 1-10
    auto_correct: bool = True
```

#### `ValidationResponse` Model

```python
class ValidationResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    violations: list[dict] = []
    original_violations: list[dict] = []
    iterations: int = 1
    checked_constraints: int = 0
    processing_time_ms: float = 0.0
    confidence: float = 1.0
    corrected_text: Optional[str] = None
    error: Optional[str] = None
```
