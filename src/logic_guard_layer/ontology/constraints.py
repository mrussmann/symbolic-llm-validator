"""Constraint definitions for ontology validation."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from logic_guard_layer.models.responses import Violation, ViolationType


class ConstraintType(str, Enum):
    """Types of constraints."""
    RANGE = "range"
    RELATIONAL = "relational"
    TYPE = "type"
    TEMPORAL = "temporal"
    PHYSICAL = "physical"


@dataclass
class Constraint:
    """Definition of a validation constraint."""
    id: str
    name: str
    type: ConstraintType
    description: str
    expression: str
    check_fn: Callable[[dict], Optional[Violation]]
    applicable_types: list[str]


def check_operating_hours_non_negative(data: dict) -> Optional[Violation]:
    """Check that operating hours are non-negative."""
    hours = data.get("betriebsstunden") or data.get("operating_hours")
    if hours is not None and hours < 0:
        return Violation(
            type=ViolationType.RANGE_ERROR,
            constraint="operating_hours >= 0",
            message=f"Operating hours cannot be negative: {hours}",
            property_name="operating_hours",
            actual_value=hours,
            expected_value=">= 0",
        )
    return None


def check_max_lifespan_positive(data: dict) -> Optional[Violation]:
    """Check that max lifespan is positive."""
    lifespan = data.get("max_lebensdauer") or data.get("max_lifespan")
    if lifespan is not None and lifespan <= 0:
        return Violation(
            type=ViolationType.RANGE_ERROR,
            constraint="max_lifespan > 0",
            message=f"Maximum lifespan must be positive: {lifespan}",
            property_name="max_lifespan",
            actual_value=lifespan,
            expected_value="> 0",
        )
    return None


def check_maintenance_interval_positive(data: dict) -> Optional[Violation]:
    """Check that maintenance interval is positive."""
    interval = data.get("wartungsintervall") or data.get("maintenance_interval")
    if interval is not None and interval <= 0:
        return Violation(
            type=ViolationType.RANGE_ERROR,
            constraint="maintenance_interval > 0",
            message=f"Maintenance interval must be positive: {interval}",
            property_name="maintenance_interval",
            actual_value=interval,
            expected_value="> 0",
        )
    return None


def check_maintenance_interval_vs_lifespan(data: dict) -> Optional[Violation]:
    """Check that maintenance interval does not exceed max lifespan."""
    interval = data.get("wartungsintervall") or data.get("maintenance_interval")
    lifespan = data.get("max_lebensdauer") or data.get("max_lifespan")

    if interval is not None and lifespan is not None and interval > lifespan:
        return Violation(
            type=ViolationType.RELATIONAL_ERROR,
            constraint="maintenance_interval <= max_lifespan",
            message=f"Maintenance interval ({interval}) exceeds maximum lifespan ({lifespan})",
            property_name="maintenance_interval",
            actual_value=interval,
            expected_value=f"<= {lifespan}",
        )
    return None


def check_operating_hours_vs_lifespan(data: dict) -> Optional[Violation]:
    """Check that operating hours do not exceed max lifespan."""
    hours = data.get("betriebsstunden") or data.get("operating_hours")
    lifespan = data.get("max_lebensdauer") or data.get("max_lifespan")

    if hours is not None and lifespan is not None and hours > lifespan:
        return Violation(
            type=ViolationType.RELATIONAL_ERROR,
            constraint="operating_hours <= max_lifespan",
            message=f"Operating hours ({hours}) exceed maximum lifespan ({lifespan})",
            property_name="operating_hours",
            actual_value=hours,
            expected_value=f"<= {lifespan}",
        )
    return None


def check_pressure_range(data: dict) -> Optional[Violation]:
    """Check that pressure is within valid range for hydraulics (0-350 bar)."""
    pressure = data.get("druck_bar") or data.get("pressure_bar") or data.get("druck")

    if pressure is not None:
        if pressure < 0:
            return Violation(
                type=ViolationType.PHYSICAL_ERROR,
                constraint="0 <= pressure_bar <= 350",
                message=f"Pressure cannot be negative: {pressure} bar",
                property_name="pressure_bar",
                actual_value=pressure,
                expected_value=">= 0 bar",
            )
        if pressure > 350:
            return Violation(
                type=ViolationType.RANGE_ERROR,
                constraint="0 <= pressure_bar <= 350",
                message=f"Pressure ({pressure} bar) exceeds maximum for standard hydraulics (350 bar)",
                property_name="pressure_bar",
                actual_value=pressure,
                expected_value="<= 350 bar",
            )
    return None


def check_temperature_range(data: dict) -> Optional[Violation]:
    """Check that temperature is within valid range (-40 to 150°C)."""
    temp = data.get("temperatur_c") or data.get("temperature_c") or data.get("temperatur")

    if temp is not None:
        if temp < -40:
            return Violation(
                type=ViolationType.RANGE_ERROR,
                constraint="-40 <= temperature_c <= 150",
                message=f"Temperature ({temp}°C) below minimum (-40°C)",
                property_name="temperature_c",
                actual_value=temp,
                expected_value=">= -40°C",
            )
        if temp > 150:
            return Violation(
                type=ViolationType.RANGE_ERROR,
                constraint="-40 <= temperature_c <= 150",
                message=f"Temperature ({temp}°C) above maximum (150°C)",
                property_name="temperature_c",
                actual_value=temp,
                expected_value="<= 150°C",
            )
    return None


def check_rpm_range(data: dict) -> Optional[Violation]:
    """Check that RPM is within valid range (0-10000)."""
    rpm = data.get("drehzahl") or data.get("rpm")

    if rpm is not None:
        if rpm < 0:
            return Violation(
                type=ViolationType.PHYSICAL_ERROR,
                constraint="0 <= rpm <= 10000",
                message=f"RPM cannot be negative: {rpm}",
                property_name="rpm",
                actual_value=rpm,
                expected_value=">= 0",
            )
        if rpm > 10000:
            return Violation(
                type=ViolationType.RANGE_ERROR,
                constraint="0 <= rpm <= 10000",
                message=f"RPM ({rpm}) exceeds maximum (10000)",
                property_name="rpm",
                actual_value=rpm,
                expected_value="<= 10000",
            )
    return None


# Define all constraints
MAINTENANCE_CONSTRAINTS: list[Constraint] = [
    Constraint(
        id="C1",
        name="Operating hours non-negative",
        type=ConstraintType.RANGE,
        description="Operating hours must be >= 0",
        expression="operating_hours >= 0",
        check_fn=check_operating_hours_non_negative,
        applicable_types=["Component", "Motor", "Pump", "HydraulicPump"],
    ),
    Constraint(
        id="C2",
        name="Maximum lifespan positive",
        type=ConstraintType.RANGE,
        description="Maximum lifespan must be > 0",
        expression="max_lifespan > 0",
        check_fn=check_max_lifespan_positive,
        applicable_types=["Component", "Motor", "Pump", "HydraulicPump"],
    ),
    Constraint(
        id="C3",
        name="Maintenance interval positive",
        type=ConstraintType.RANGE,
        description="Maintenance interval must be > 0",
        expression="maintenance_interval > 0",
        check_fn=check_maintenance_interval_positive,
        applicable_types=["Component", "Motor", "Pump", "HydraulicPump"],
    ),
    Constraint(
        id="C4",
        name="Maintenance interval <= lifespan",
        type=ConstraintType.RELATIONAL,
        description="Maintenance interval cannot exceed maximum lifespan",
        expression="maintenance_interval <= max_lifespan",
        check_fn=check_maintenance_interval_vs_lifespan,
        applicable_types=["Component", "Motor", "Pump", "HydraulicPump"],
    ),
    Constraint(
        id="C5",
        name="Operating hours <= lifespan",
        type=ConstraintType.RELATIONAL,
        description="Operating hours cannot exceed maximum lifespan",
        expression="operating_hours <= max_lifespan",
        check_fn=check_operating_hours_vs_lifespan,
        applicable_types=["Component", "Motor", "Pump", "HydraulicPump"],
    ),
    Constraint(
        id="C6",
        name="Hydraulic pressure range",
        type=ConstraintType.PHYSICAL,
        description="Pressure must be within valid range for standard hydraulics (0-350 bar)",
        expression="0 <= pressure_bar <= 350",
        check_fn=check_pressure_range,
        applicable_types=["HydraulicPump", "Pump", "Component"],
    ),
    Constraint(
        id="C7",
        name="Temperature range",
        type=ConstraintType.PHYSICAL,
        description="Temperature must be within valid range (-40 to 150°C)",
        expression="-40 <= temperature_c <= 150",
        check_fn=check_temperature_range,
        applicable_types=["Component", "Motor", "Sensor"],
    ),
    Constraint(
        id="C8",
        name="RPM range",
        type=ConstraintType.PHYSICAL,
        description="RPM must be within valid range (0-10000)",
        expression="0 <= rpm <= 10000",
        check_fn=check_rpm_range,
        applicable_types=["Motor", "Pump", "RotatingComponent"],
    ),
]


def get_all_constraints() -> list[Constraint]:
    """Get all defined constraints."""
    return MAINTENANCE_CONSTRAINTS.copy()


def get_constraints_for_type(type_name: str) -> list[Constraint]:
    """Get constraints applicable to a specific type.

    Args:
        type_name: The type/class name

    Returns:
        List of applicable constraints
    """
    return [
        c for c in MAINTENANCE_CONSTRAINTS
        if type_name in c.applicable_types or "Component" in c.applicable_types
    ]


def get_constraint_by_id(constraint_id: str) -> Optional[Constraint]:
    """Get a constraint by its ID.

    Args:
        constraint_id: The constraint ID (e.g., "C1")

    Returns:
        The constraint or None
    """
    for c in MAINTENANCE_CONSTRAINTS:
        if c.id == constraint_id:
            return c
    return None
