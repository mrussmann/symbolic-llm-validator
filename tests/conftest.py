"""Pytest configuration and shared fixtures."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Import models
from logic_guard_layer.models.entities import (
    Component,
    ComponentType,
    Measurement,
    ParsedData,
    MaintenanceEvent,
    EventType,
)
from logic_guard_layer.models.responses import (
    Violation,
    ViolationType,
    ValidationResult,
)
from logic_guard_layer.ontology.constraints import Constraint, ConstraintType


# === Model Fixtures ===

@pytest.fixture
def sample_measurement():
    """Create a sample measurement."""
    return Measurement(
        type="Druck",
        value=250.0,
        unit="bar"
    )


@pytest.fixture
def sample_component():
    """Create a sample valid component."""
    return Component(
        name="HP-001",
        type=ComponentType.HYDRAULIC_PUMP,
        serial_number="SN123456",
        operating_hours=5000,
        max_lifespan=20000,
        maintenance_interval=2500,
        measurements=[]
    )


@pytest.fixture
def sample_component_with_measurements(sample_measurement):
    """Create a component with measurements."""
    return Component(
        name="HP-001",
        type=ComponentType.HYDRAULIC_PUMP,
        serial_number="SN123456",
        operating_hours=5000,
        max_lifespan=20000,
        maintenance_interval=2500,
        measurements=[sample_measurement]
    )


@pytest.fixture
def invalid_component_operating_hours():
    """Create a component with invalid operating hours (exceeds lifespan)."""
    return Component(
        name="HP-002",
        type=ComponentType.HYDRAULIC_PUMP,
        serial_number="SN789",
        operating_hours=25000,
        max_lifespan=20000,
        maintenance_interval=2500,
        measurements=[]
    )


@pytest.fixture
def sample_parsed_data(sample_component):
    """Create sample parsed data."""
    return ParsedData(
        components=[sample_component],
        events=[],
        raw_values={
            "component": {
                "name": "HP-001",
                "type": "Hydraulikpumpe"
            }
        },
        extraction_confidence=0.95
    )


@pytest.fixture
def sample_maintenance_event():
    """Create a sample maintenance event."""
    return MaintenanceEvent(
        component_name="HP-001",
        event_type=EventType.MAINTENANCE,
        event_date=datetime.now().date(),
        description="Regular maintenance",
        technician="John Doe"
    )


@pytest.fixture
def sample_violation():
    """Create a sample violation."""
    return Violation(
        type=ViolationType.RANGE_ERROR,
        constraint="operating_hours >= 0",
        message="Operating hours cannot be negative: -100",
        entity="HP-001",
        property_name="operating_hours",
        actual_value=-100,
        expected_value=">= 0",
        severity="error"
    )


@pytest.fixture
def sample_validation_result_success(sample_parsed_data):
    """Create a successful validation result."""
    return ValidationResult(
        success=True,
        data={"component": sample_parsed_data.components[0].model_dump()},
        violations=[],
        iterations=1,
        checked_constraints=8,
        processing_time_ms=150.5,
        confidence=0.95,
        original_text="Hydraulikpumpe HP-001 mit 5000 Betriebsstunden",
    )


@pytest.fixture
def sample_validation_result_failure(sample_violation):
    """Create a failed validation result."""
    return ValidationResult(
        success=False,
        data={},
        violations=[sample_violation],
        iterations=3,
        checked_constraints=8,
        processing_time_ms=450.0,
        confidence=0.8,
        original_text="Test text",
        error=None
    )


# === Raw Values Fixtures ===

@pytest.fixture
def valid_raw_values():
    """Create valid raw values for constraint checking."""
    return {
        "name": "HP-001",
        "operating_hours": 5000,
        "max_lifespan": 20000,
        "maintenance_interval": 2500,
        "pressure_bar": 250,
        "temperature_c": 75,
        "rpm": 3000,
    }


@pytest.fixture
def raw_values_negative_hours():
    """Raw values with negative operating hours."""
    return {
        "name": "HP-001",
        "operating_hours": -100,
    }


@pytest.fixture
def raw_values_exceeds_lifespan():
    """Raw values where operating hours exceed lifespan."""
    return {
        "name": "HP-001",
        "operating_hours": 25000,
        "max_lifespan": 20000,
    }


@pytest.fixture
def raw_values_high_pressure():
    """Raw values with pressure exceeding limit."""
    return {
        "name": "HP-001",
        "pressure_bar": 500,
    }


@pytest.fixture
def raw_values_high_temperature():
    """Raw values with temperature exceeding limit."""
    return {
        "name": "SENSOR-001",
        "temperature_c": 200,
    }


@pytest.fixture
def raw_values_invalid_interval():
    """Raw values where maintenance interval exceeds lifespan."""
    return {
        "name": "HP-001",
        "maintenance_interval": 30000,
        "max_lifespan": 20000,
    }


# === Ontology Schema Fixtures ===

@pytest.fixture
def valid_ontology_schema():
    """Create a valid ontology schema."""
    return {
        "name": "test-ontology",
        "version": "1.0.0",
        "description": "Test ontology for unit tests",
        "definitions": {
            "concepts": {
                "Component": {
                    "description": "Base component class"
                },
                "Motor": {
                    "description": "Electric motor",
                    "parent": "Component"
                }
            },
            "properties": {
                "operating_hours": {
                    "type": "integer",
                    "description": "Operating hours"
                }
            },
            "constraints": [
                {
                    "id": "T1",
                    "name": "Test constraint",
                    "expression": "operating_hours >= 0"
                }
            ]
        }
    }


@pytest.fixture
def invalid_ontology_schema_no_definitions():
    """Create an invalid ontology schema without definitions."""
    return {
        "name": "invalid",
        "version": "1.0.0"
    }


@pytest.fixture
def invalid_ontology_schema_no_concepts():
    """Create an invalid ontology schema without concepts."""
    return {
        "name": "invalid",
        "definitions": {}
    }


# === Mock Fixtures ===

@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    client = AsyncMock()
    client.complete = AsyncMock(return_value="Corrected text")
    client.complete_json = AsyncMock(return_value={
        "component": {
            "name": "HP-001",
            "type": "Hydraulikpumpe",
            "operating_hours": 5000,
            "max_lifespan": 20000,
            "maintenance_interval": 2500,
        }
    })
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_parser(mock_llm_client, sample_parsed_data):
    """Create a mock semantic parser."""
    parser = MagicMock()
    parser.parse = AsyncMock(return_value=sample_parsed_data)
    parser.extract_raw_values = MagicMock(return_value={
        "name": "HP-001",
        "operating_hours": 5000,
        "max_lifespan": 20000,
        "maintenance_interval": 2500,
    })
    return parser


@pytest.fixture
def mock_reasoner():
    """Create a mock reasoning module."""
    from logic_guard_layer.core.reasoner import ConsistencyResult

    reasoner = MagicMock()
    reasoner.check_consistency = MagicMock(return_value=ConsistencyResult(
        is_consistent=True,
        violations=[],
        checked_constraints=8,
        processing_time_ms=10.0
    ))
    reasoner.get_constraints_summary = MagicMock(return_value=[])
    return reasoner


# === Test Data Fixtures ===

@pytest.fixture
def sample_maintenance_text_valid():
    """Sample valid maintenance text in German."""
    return """
    Wartungsbericht für Hydraulikpumpe HP-001:
    - Seriennummer: SN123456
    - Betriebsstunden: 5000
    - Maximale Lebensdauer: 20000 Stunden
    - Wartungsintervall: 2500 Stunden
    - Druck: 250 bar
    - Temperatur: 75°C
    Status: Betriebsbereit
    """


@pytest.fixture
def sample_maintenance_text_invalid():
    """Sample invalid maintenance text with violations."""
    return """
    Wartungsbericht für Hydraulikpumpe HP-002:
    - Betriebsstunden: 25000
    - Maximale Lebensdauer: 20000 Stunden
    - Druck: 500 bar
    Status: Kritisch
    """
