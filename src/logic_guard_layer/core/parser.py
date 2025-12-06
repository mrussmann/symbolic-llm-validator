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

        # Extract component data
        component_data = raw_data.get("komponente", {})
        if component_data:
            component = self._create_component(component_data)
            if component:
                components.append(component)
            raw_values["komponente"] = component_data

        # Extract measurements
        measurements = raw_data.get("messwerte", [])
        if measurements and components:
            for m in measurements:
                measurement = Measurement(
                    type=m.get("typ", "unknown"),
                    value=m.get("wert", 0),
                    unit=m.get("einheit", "")
                )
                components[0].measurements.append(measurement)
        raw_values["messwerte"] = measurements

        # Store maintenance info
        if "wartung" in raw_data:
            raw_values["wartung"] = raw_data["wartung"]

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

        # Map component type
        type_str = data.get("typ", "Unbekannt")
        try:
            component_type = ComponentType(type_str)
        except ValueError:
            # Try to match partially
            type_map = {
                "motor": ComponentType.MOTOR,
                "elektromotor": ComponentType.MOTOR,
                "pumpe": ComponentType.PUMP,
                "hydraulikpumpe": ComponentType.HYDRAULIC_PUMP,
                "hydraulik": ComponentType.HYDRAULIC_PUMP,
                "ventil": ComponentType.VALVE,
                "sensor": ComponentType.SENSOR,
                "drucksensor": ComponentType.PRESSURE_SENSOR,
                "temperatursensor": ComponentType.TEMPERATURE_SENSOR,
            }
            component_type = type_map.get(type_str.lower(), ComponentType.UNKNOWN)

        return Component(
            name=data.get("name", ""),
            type=component_type,
            serial_number=data.get("seriennummer"),
            operating_hours=self._safe_int(data.get("betriebsstunden")),
            max_lifespan=self._safe_int(data.get("max_lebensdauer")),
            maintenance_interval=self._safe_int(data.get("wartungsintervall")),
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
            if comp.max_lifespan is not None:
                values["max_lebensdauer"] = comp.max_lifespan
            if comp.maintenance_interval is not None:
                values["wartungsintervall"] = comp.maintenance_interval
            if comp.serial_number:
                values["seriennummer"] = comp.serial_number

            # Extract from measurements
            for m in comp.measurements:
                if m.type.lower() == "druck" or "druck" in m.type.lower():
                    values["druck_bar"] = m.value
                elif m.type.lower() == "temperatur" or "temp" in m.type.lower():
                    values["temperatur_c"] = m.value
                elif m.type.lower() == "drehzahl" or "rpm" in m.type.lower():
                    values["drehzahl"] = m.value

        # Also get from raw values if available
        raw_komp = parsed_data.raw_values.get("komponente", {})
        if raw_komp:
            for key in ["druck_bar", "temperatur_c", "drehzahl", "status"]:
                if key in raw_komp and raw_komp[key] is not None:
                    values[key] = raw_komp[key]

        return values
