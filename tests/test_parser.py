"""Tests for SemanticParser."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from logic_guard_layer.core.parser import SemanticParser, ParserError
from logic_guard_layer.models.entities import (
    Component,
    ComponentType,
    Measurement,
    ParsedData,
)
from logic_guard_layer.llm.client import LLMError


class TestSemanticParserInit:
    """Tests for SemanticParser initialization."""

    def test_init_with_client(self, mock_llm_client):
        """Test initialization with LLM client."""
        parser = SemanticParser(mock_llm_client)
        assert parser.llm_client is mock_llm_client
        assert parser.schema is not None


class TestSemanticParserParse:
    """Tests for SemanticParser.parse method."""

    @pytest.mark.asyncio
    async def test_parse_valid_text(self, mock_llm_client):
        """Test parsing valid text."""
        mock_llm_client.complete_json = AsyncMock(return_value={
            "component": {
                "name": "HP-001",
                "type": "Hydraulikpumpe",
                "operating_hours": 5000,
                "max_lifespan": 20000,
                "maintenance_interval": 2500
            }
        })

        parser = SemanticParser(mock_llm_client)
        result = await parser.parse("Test maintenance text")

        assert isinstance(result, ParsedData)
        assert len(result.components) == 1
        assert result.components[0].name == "HP-001"
        assert result.components[0].type == ComponentType.HYDRAULIC_PUMP

    @pytest.mark.asyncio
    async def test_parse_with_german_keys(self, mock_llm_client):
        """Test parsing with German keys."""
        mock_llm_client.complete_json = AsyncMock(return_value={
            "komponente": {
                "name": "HP-001",
                "typ": "Hydraulikpumpe",
                "betriebsstunden": 5000,
                "max_lebensdauer": 20000,
                "wartungsintervall": 2500
            }
        })

        parser = SemanticParser(mock_llm_client)
        result = await parser.parse("Test text")

        assert len(result.components) == 1
        assert result.components[0].operating_hours == 5000
        assert result.components[0].max_lifespan == 20000

    @pytest.mark.asyncio
    async def test_parse_with_measurements(self, mock_llm_client):
        """Test parsing with measurements."""
        mock_llm_client.complete_json = AsyncMock(return_value={
            "component": {
                "name": "HP-001",
                "type": "Hydraulikpumpe",
                "operating_hours": 5000
            },
            "measurements": [
                {"type": "Druck", "value": 250, "unit": "bar"},
                {"type": "Temperatur", "value": 75, "unit": "°C"}
            ]
        })

        parser = SemanticParser(mock_llm_client)
        result = await parser.parse("Test text")

        assert len(result.components[0].measurements) == 2
        assert result.components[0].measurements[0].type == "Druck"
        assert result.components[0].measurements[0].value == 250

    @pytest.mark.asyncio
    async def test_parse_with_german_measurements(self, mock_llm_client):
        """Test parsing with German measurement keys."""
        mock_llm_client.complete_json = AsyncMock(return_value={
            "component": {
                "name": "HP-001",
                "type": "Hydraulikpumpe"
            },
            "messwerte": [
                {"typ": "Druck", "wert": 250, "einheit": "bar"}
            ]
        })

        parser = SemanticParser(mock_llm_client)
        result = await parser.parse("Test text")

        assert len(result.components[0].measurements) == 1
        assert result.components[0].measurements[0].value == 250

    @pytest.mark.asyncio
    async def test_parse_llm_error(self, mock_llm_client):
        """Test handling LLM error."""
        mock_llm_client.complete_json = AsyncMock(side_effect=LLMError("API error"))

        parser = SemanticParser(mock_llm_client)

        with pytest.raises(ParserError) as exc_info:
            await parser.parse("Test text")

        assert "Failed to parse" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parse_unexpected_error(self, mock_llm_client):
        """Test handling unexpected error."""
        mock_llm_client.complete_json = AsyncMock(side_effect=Exception("Unexpected"))

        parser = SemanticParser(mock_llm_client)

        with pytest.raises(ParserError) as exc_info:
            await parser.parse("Test text")

        assert "Parsing failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_parse_empty_component(self, mock_llm_client):
        """Test parsing with empty component data."""
        mock_llm_client.complete_json = AsyncMock(return_value={
            "component": {}
        })

        parser = SemanticParser(mock_llm_client)
        result = await parser.parse("Test text")

        # No component should be created without a name
        assert len(result.components) == 0
        assert result.extraction_confidence == 0.5


class TestSemanticParserConvertToParsedData:
    """Tests for SemanticParser._convert_to_parsed_data method."""

    def test_convert_full_data(self, mock_llm_client):
        """Test converting full data."""
        parser = SemanticParser(mock_llm_client)
        raw_data = {
            "component": {
                "name": "HP-001",
                "type": "Hydraulikpumpe",
                "operating_hours": 5000,
                "max_lifespan": 20000
            },
            "maintenance": {
                "date": "2024-01-15",
                "technician": "John Doe"
            }
        }

        result = parser._convert_to_parsed_data(raw_data)

        assert len(result.components) == 1
        assert result.extraction_confidence == 1.0
        assert "component" in result.raw_values
        assert "maintenance" in result.raw_values

    def test_convert_no_components(self, mock_llm_client):
        """Test converting data without components."""
        parser = SemanticParser(mock_llm_client)
        raw_data = {}

        result = parser._convert_to_parsed_data(raw_data)

        assert len(result.components) == 0
        assert result.extraction_confidence == 0.5

    def test_convert_with_measurements_no_component(self, mock_llm_client):
        """Test measurements are not added without component."""
        parser = SemanticParser(mock_llm_client)
        raw_data = {
            "measurements": [
                {"type": "Druck", "value": 250, "unit": "bar"}
            ]
        }

        result = parser._convert_to_parsed_data(raw_data)

        # No component, so measurements can't be attached
        assert len(result.components) == 0


class TestSemanticParserCreateComponent:
    """Tests for SemanticParser._create_component method."""

    def test_create_component_full(self, mock_llm_client):
        """Test creating component with all fields."""
        parser = SemanticParser(mock_llm_client)
        data = {
            "name": "HP-001",
            "type": "Hydraulikpumpe",
            "serial_number": "SN123",
            "operating_hours": 5000,
            "max_lifespan": 20000,
            "maintenance_interval": 2500
        }

        component = parser._create_component(data)

        assert component.name == "HP-001"
        assert component.type == ComponentType.HYDRAULIC_PUMP
        assert component.serial_number == "SN123"
        assert component.operating_hours == 5000
        assert component.max_lifespan == 20000
        assert component.maintenance_interval == 2500

    def test_create_component_no_name(self, mock_llm_client):
        """Test creating component without name returns None."""
        parser = SemanticParser(mock_llm_client)
        data = {"type": "Motor"}

        component = parser._create_component(data)

        assert component is None

    def test_create_component_type_mapping(self, mock_llm_client):
        """Test component type mapping for various types."""
        parser = SemanticParser(mock_llm_client)

        test_cases = [
            ("Motor", ComponentType.MOTOR),
            ("Elektromotor", ComponentType.MOTOR),
            ("Pumpe", ComponentType.PUMP),
            ("Hydraulikpumpe", ComponentType.HYDRAULIC_PUMP),
            ("Hydraulik", ComponentType.HYDRAULIC_PUMP),
            ("Ventil", ComponentType.VALVE),
            ("Sensor", ComponentType.SENSOR),
            ("Drucksensor", ComponentType.PRESSURE_SENSOR),
            ("Temperatursensor", ComponentType.TEMPERATURE_SENSOR),
            ("UnknownType", ComponentType.UNKNOWN),
        ]

        for type_str, expected_type in test_cases:
            data = {"name": "TEST", "type": type_str}
            component = parser._create_component(data)
            assert component.type == expected_type, f"Failed for {type_str}"

    def test_create_component_german_keys(self, mock_llm_client):
        """Test creating component with German keys."""
        parser = SemanticParser(mock_llm_client)
        data = {
            "name": "HP-001",
            "typ": "Hydraulikpumpe",
            "seriennummer": "SN123",
            "betriebsstunden": 5000,
            "max_lebensdauer": 20000,
            "wartungsintervall": 2500
        }

        component = parser._create_component(data)

        assert component.operating_hours == 5000
        assert component.max_lifespan == 20000
        assert component.maintenance_interval == 2500
        assert component.serial_number == "SN123"


class TestSemanticParserSafeInt:
    """Tests for SemanticParser._safe_int method."""

    def test_safe_int_valid(self, mock_llm_client):
        """Test safe_int with valid integer."""
        parser = SemanticParser(mock_llm_client)
        assert parser._safe_int(5000) == 5000

    def test_safe_int_string(self, mock_llm_client):
        """Test safe_int with string number."""
        parser = SemanticParser(mock_llm_client)
        assert parser._safe_int("5000") == 5000

    def test_safe_int_with_thousands_separator_dot(self, mock_llm_client):
        """Test safe_int with dot thousands separator."""
        parser = SemanticParser(mock_llm_client)
        assert parser._safe_int("5.000") == 5000

    def test_safe_int_with_thousands_separator_comma(self, mock_llm_client):
        """Test safe_int with comma thousands separator."""
        parser = SemanticParser(mock_llm_client)
        assert parser._safe_int("5,000") == 5000

    def test_safe_int_none(self, mock_llm_client):
        """Test safe_int with None."""
        parser = SemanticParser(mock_llm_client)
        assert parser._safe_int(None) is None

    def test_safe_int_invalid(self, mock_llm_client):
        """Test safe_int with invalid value."""
        parser = SemanticParser(mock_llm_client)
        assert parser._safe_int("not a number") is None

    def test_safe_int_float(self, mock_llm_client):
        """Test safe_int with float."""
        parser = SemanticParser(mock_llm_client)
        assert parser._safe_int(5000.0) == 5000


class TestSemanticParserExtractRawValues:
    """Tests for SemanticParser.extract_raw_values method."""

    def test_extract_from_component(self, mock_llm_client, sample_component):
        """Test extracting values from component."""
        parser = SemanticParser(mock_llm_client)
        parsed_data = ParsedData(
            components=[sample_component],
            raw_values={}
        )

        values = parser.extract_raw_values(parsed_data)

        assert values["name"] == "HP-001"
        assert values["operating_hours"] == 5000
        assert values["betriebsstunden"] == 5000
        assert values["max_lifespan"] == 20000
        assert values["max_lebensdauer"] == 20000
        assert values["maintenance_interval"] == 2500
        assert values["wartungsintervall"] == 2500

    def test_extract_from_measurements(self, mock_llm_client):
        """Test extracting values from measurements."""
        parser = SemanticParser(mock_llm_client)

        component = Component(
            name="HP-001",
            type=ComponentType.HYDRAULIC_PUMP,
            measurements=[
                Measurement(type="Druck", value=250.0, unit="bar"),
                Measurement(type="Temperatur", value=75.0, unit="°C"),
                Measurement(type="Drehzahl", value=3000.0, unit="rpm"),
            ]
        )
        parsed_data = ParsedData(components=[component], raw_values={})

        values = parser.extract_raw_values(parsed_data)

        assert values["druck_bar"] == 250.0
        assert values["pressure_bar"] == 250.0
        assert values["temperatur_c"] == 75.0
        assert values["temperature_c"] == 75.0
        assert values["drehzahl"] == 3000.0
        assert values["rpm"] == 3000.0

    def test_extract_from_raw_values(self, mock_llm_client):
        """Test extracting from raw_values dict."""
        parser = SemanticParser(mock_llm_client)

        parsed_data = ParsedData(
            components=[Component(name="HP-001")],
            raw_values={
                "component": {
                    "pressure_bar": 300,
                    "temperature_c": 80,
                    "rpm": 4000,
                    "status": "active"
                }
            }
        )

        values = parser.extract_raw_values(parsed_data)

        assert values["pressure_bar"] == 300
        assert values["temperature_c"] == 80
        assert values["rpm"] == 4000
        assert values["status"] == "active"

    def test_extract_from_german_raw_values(self, mock_llm_client):
        """Test extracting from German raw_values dict."""
        parser = SemanticParser(mock_llm_client)

        parsed_data = ParsedData(
            components=[Component(name="HP-001")],
            raw_values={
                "komponente": {
                    "druck_bar": 300,
                    "temperatur_c": 80,
                    "drehzahl": 4000,
                }
            }
        )

        values = parser.extract_raw_values(parsed_data)

        assert values["druck_bar"] == 300
        assert values["temperatur_c"] == 80
        assert values["drehzahl"] == 4000

    def test_extract_empty_parsed_data(self, mock_llm_client):
        """Test extracting from empty parsed data."""
        parser = SemanticParser(mock_llm_client)
        parsed_data = ParsedData()

        values = parser.extract_raw_values(parsed_data)

        assert values == {}

    def test_extract_measurements_with_english_type(self, mock_llm_client):
        """Test extracting measurements with English type names."""
        parser = SemanticParser(mock_llm_client)

        component = Component(
            name="HP-001",
            measurements=[
                Measurement(type="pressure", value=250.0, unit="bar"),
                Measurement(type="temp", value=75.0, unit="°C"),
            ]
        )
        parsed_data = ParsedData(components=[component], raw_values={})

        values = parser.extract_raw_values(parsed_data)

        assert values["pressure_bar"] == 250.0
        assert values["temperature_c"] == 75.0
