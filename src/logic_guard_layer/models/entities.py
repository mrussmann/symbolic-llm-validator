"""Domain entity models for Logic-Guard-Layer."""

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ComponentType(str, Enum):
    """Types of components in the maintenance domain."""
    MOTOR = "Motor"
    PUMP = "Pumpe"
    HYDRAULIC_PUMP = "Hydraulikpumpe"
    VALVE = "Ventil"
    SENSOR = "Sensor"
    PRESSURE_SENSOR = "Drucksensor"
    TEMPERATURE_SENSOR = "Temperatursensor"
    CONTAINER = "Behaelter"
    UNKNOWN = "Unbekannt"


class EventType(str, Enum):
    """Types of events in the maintenance domain."""
    MAINTENANCE = "Wartung"
    FAILURE = "Ausfall"
    MEASUREMENT = "Messung"


class Measurement(BaseModel):
    """A measurement value with unit."""
    type: str = Field(..., description="Type of measurement (e.g., 'Druck', 'Temperatur')")
    value: float = Field(..., description="Measured value")
    unit: str = Field(..., description="Unit of measurement (e.g., 'bar', '°C')")


class Component(BaseModel):
    """Base model for a technical component."""
    name: str = Field(..., description="Component identifier/name")
    type: ComponentType = Field(default=ComponentType.UNKNOWN, description="Component type")
    serial_number: Optional[str] = Field(None, alias="seriennummer", description="Serial number")
    operating_hours: Optional[int] = Field(None, alias="betriebsstunden", ge=0, description="Operating hours")
    max_lifespan: Optional[int] = Field(None, alias="max_lebensdauer", gt=0, description="Maximum lifespan in hours")
    maintenance_interval: Optional[int] = Field(None, alias="wartungsintervall", gt=0, description="Maintenance interval in hours")
    measurements: list[Measurement] = Field(default_factory=list, description="Associated measurements")

    model_config = {
        "populate_by_name": True,
    }


class MaintenanceEvent(BaseModel):
    """A maintenance event record."""
    component_name: str = Field(..., description="Name of the maintained component")
    event_type: EventType = Field(default=EventType.MAINTENANCE, description="Type of event")
    event_date: Optional[date] = Field(None, alias="datum", description="Date of the event")
    description: Optional[str] = Field(None, description="Description of the maintenance")
    technician: Optional[str] = Field(None, alias="techniker", description="Technician who performed the work")

    model_config = {
        "populate_by_name": True,
    }


class ParsedData(BaseModel):
    """Structured data extracted from text by the parser."""
    components: list[Component] = Field(default_factory=list, description="Extracted components")
    events: list[MaintenanceEvent] = Field(default_factory=list, description="Extracted events")
    raw_values: dict[str, Any] = Field(default_factory=dict, description="Raw extracted values")
    extraction_confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")

    def get_component(self, name: str) -> Optional[Component]:
        """Get a component by name."""
        for comp in self.components:
            if comp.name == name:
                return comp
        return None
