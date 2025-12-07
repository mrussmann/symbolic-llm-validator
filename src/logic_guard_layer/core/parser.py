"""Semantic parser for extracting structured data from text."""

import logging
from typing import Any, Optional

from logic_guard_layer.llm.client import OpenRouterClient, LLMError
from logic_guard_layer.llm.prompts import (
    get_parsing_prompt,
    get_extraction_schema,
    PARSING_SYSTEM_PROMPT,
)
from logic_guard_layer.models.entities import ParsedData, Component, ComponentType, Measurement

logger = logging.getLogger(__name__)


class ParserError(Exception):
    """Exception for parser-related errors."""
    pass


class SemanticParser:
    """
    Semantic parser that transforms unstructured text into structured data.
    Uses LLM for schema-guided parsing.
    """

    def __init__(self, llm_client: OpenRouterClient):
        """Initialize the semantic parser.

        Args:
            llm_client: OpenRouter client for LLM calls
        """
        self.llm_client = llm_client
        self.schema = get_extraction_schema()

    async def parse(self, text: str) -> ParsedData:
        """Parse unstructured text into structured data.

        Args:
            text: The text to parse

        Returns:
            ParsedData containing extracted information

        Raises:
            ParserError: If parsing fails
        """
        try:
            # Generate parsing prompt
            prompt = get_parsing_prompt(text)

            # Call LLM to extract structured data
            logger.debug("Calling LLM for text parsing")
            raw_data = await self.llm_client.complete_json(
                prompt=prompt,
                temperature=0.0,  # Deterministic for parsing
            )

            # Convert to ParsedData model
            parsed = self._convert_to_parsed_data(raw_data)
            logger.debug(f"Parsed {len(parsed.components)} components")
            return parsed

        except LLMError as e:
            logger.error(f"LLM error during parsing: {e}")
            raise ParserError(f"Failed to parse text: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during parsing: {e}")
            raise ParserError(f"Parsing failed: {e}") from e

    def _convert_to_parsed_data(self, raw_data: dict) -> ParsedData:
        """Convert raw LLM output to ParsedData model.

        Args:
            raw_data: Raw dictionary from LLM

        Returns:
            ParsedData model
        """
        components = []
        raw_values = {}

        logger.info(f"Converting raw LLM data: {raw_data}")

        # Extract component data (support both English and German keys)
        component_data = raw_data.get("component") or raw_data.get("komponente", {})
        if component_data:
            logger.info(f"Found component data: {component_data}")
            component = self._create_component(component_data)
            if component:
                components.append(component)
            raw_values["component"] = component_data

        # Extract measurements (support both English and German keys)
        measurements = raw_data.get("measurements") or raw_data.get("messwerte", [])
        if measurements and components:
            for m in measurements:
                measurement = Measurement(
                    type=m.get("type") or m.get("typ", "unknown"),
                    value=m.get("value") or m.get("wert", 0),
                    unit=m.get("unit") or m.get("einheit", "")
                )
                components[0].measurements.append(measurement)
        raw_values["measurements"] = measurements

        # Store maintenance info (support both English and German keys)
        maintenance_data = raw_data.get("maintenance") or raw_data.get("wartung")
        if maintenance_data:
            raw_values["maintenance"] = maintenance_data

        return ParsedData(
            components=components,
            events=[],
            raw_values=raw_values,
            extraction_confidence=1.0 if components else 0.5,
        )

    def _create_component(self, data: dict) -> Optional[Component]:
        """Create a Component from extracted data.

        Args:
            data: Component data dictionary

        Returns:
            Component instance or None
        """
        if not data.get("name"):
            return None

        # Map component type (support both English and German keys)
        type_str = data.get("type") or data.get("typ", "Unknown")
        try:
            component_type = ComponentType(type_str)
        except ValueError:
            # Try to match partially
            type_map = {
                "motor": ComponentType.MOTOR,
                "electricmotor": ComponentType.MOTOR,
                "elektromotor": ComponentType.MOTOR,
                "pump": ComponentType.PUMP,
                "pumpe": ComponentType.PUMP,
                "hydraulicpump": ComponentType.HYDRAULIC_PUMP,
                "hydraulikpumpe": ComponentType.HYDRAULIC_PUMP,
                "hydraulik": ComponentType.HYDRAULIC_PUMP,
                "valve": ComponentType.VALVE,
                "ventil": ComponentType.VALVE,
                "sensor": ComponentType.SENSOR,
                "pressuresensor": ComponentType.PRESSURE_SENSOR,
                "drucksensor": ComponentType.PRESSURE_SENSOR,
                "temperaturesensor": ComponentType.TEMPERATURE_SENSOR,
                "temperatursensor": ComponentType.TEMPERATURE_SENSOR,
            }
            component_type = type_map.get(type_str.lower().replace(" ", ""), ComponentType.UNKNOWN)

        # Get operating hours (English or German key)
        operating_hours = self._safe_int(
            data.get("operating_hours") or data.get("betriebsstunden")
        )
        # Get max lifespan (English or German key)
        max_lifespan = self._safe_int(
            data.get("max_lifespan") or data.get("max_lebensdauer")
        )
        # Get maintenance interval (English or German key)
        maintenance_interval = self._safe_int(
            data.get("maintenance_interval") or data.get("wartungsintervall")
        )
        # Get serial number (English or German key)
        serial_number = data.get("serial_number") or data.get("seriennummer")

        logger.info(f"Created component: name={data.get('name')}, type={component_type}, "
                   f"hours={operating_hours}, lifespan={max_lifespan}")

        return Component(
            name=data.get("name", ""),
            type=component_type,
            serial_number=serial_number,
            operating_hours=operating_hours,
            max_lifespan=max_lifespan,
            maintenance_interval=maintenance_interval,
            measurements=[],
        )

    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int.

        Args:
            value: Value to convert

        Returns:
            Integer or None
        """
        if value is None:
            return None
        try:
            # Handle string numbers with thousands separator
            if isinstance(value, str):
                value = value.replace(".", "").replace(",", "")
            return int(value)
        except (ValueError, TypeError):
            return None

    def extract_raw_values(self, parsed_data: ParsedData) -> dict:
        """Extract raw values for constraint checking.

        Args:
            parsed_data: Parsed data model

        Returns:
            Flat dictionary of values for constraint checking
        """
        values = {}

        # Extract from components
        for comp in parsed_data.components:
            values["name"] = comp.name
            values["typ"] = comp.type.value

            if comp.operating_hours is not None:
                values["betriebsstunden"] = comp.operating_hours
                values["operating_hours"] = comp.operating_hours
            if comp.max_lifespan is not None:
                values["max_lebensdauer"] = comp.max_lifespan
                values["max_lifespan"] = comp.max_lifespan
            if comp.maintenance_interval is not None:
                values["wartungsintervall"] = comp.maintenance_interval
                values["maintenance_interval"] = comp.maintenance_interval
            if comp.serial_number:
                values["seriennummer"] = comp.serial_number

            # Extract from measurements
            for m in comp.measurements:
                m_type = m.type.lower()
                if "druck" in m_type or "pressure" in m_type:
                    values["druck_bar"] = m.value
                    values["pressure_bar"] = m.value
                elif "temperatur" in m_type or "temp" in m_type:
                    values["temperatur_c"] = m.value
                    values["temperature_c"] = m.value
                elif "drehzahl" in m_type or "rpm" in m_type:
                    values["drehzahl"] = m.value
                    values["rpm"] = m.value

        # Also get from raw values if available (support both English and German)
        raw_comp = parsed_data.raw_values.get("component") or parsed_data.raw_values.get("komponente", {})
        if raw_comp:
            # Pressure
            pressure = raw_comp.get("pressure_bar") or raw_comp.get("druck_bar")
            if pressure is not None:
                values["druck_bar"] = pressure
                values["pressure_bar"] = pressure
            # Temperature
            temp = raw_comp.get("temperature_c") or raw_comp.get("temperatur_c")
            if temp is not None:
                values["temperatur_c"] = temp
                values["temperature_c"] = temp
            # RPM
            rpm = raw_comp.get("rpm") or raw_comp.get("drehzahl")
            if rpm is not None:
                values["drehzahl"] = rpm
                values["rpm"] = rpm
            # Status
            status = raw_comp.get("status")
            if status is not None:
                values["status"] = status

        logger.info(f"Extracted raw values for constraint checking: {values}")
        return values
