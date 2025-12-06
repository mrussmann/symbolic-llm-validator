"""Prompt templates for Logic-Guard-Layer."""

import json
from pathlib import Path
from typing import Any, Optional


def load_schema() -> dict:
    """Load the maintenance schema JSON."""
    schema_path = Path(__file__).parent.parent / "data" / "maintenance_schema.json"
    if schema_path.exists():
        with open(schema_path) as f:
            return json.load(f)
    return {}


PARSING_SYSTEM_PROMPT = """You are a precise data extraction assistant for technical maintenance documents.
Your task is to extract structured information from technical texts.
ALWAYS respond ONLY with valid JSON. No explanations, no comments.
If a value is not present in the text, use null.
Numbers with thousands separators (e.g., 15,000 or 15.000) must be extracted as integers without separators (15000)."""


def get_parsing_prompt(input_text: str, schema: Optional[dict] = None) -> str:
    """Generate a parsing prompt for extracting structured data.

    Args:
        input_text: The text to parse
        schema: Optional custom schema (uses default if not provided)

    Returns:
        The formatted prompt
    """
    if schema is None:
        schema = {
            "component": {
                "name": "string - Component identifier (e.g., 'M1', 'HP-01')",
                "type": "string - Component type (Motor, Pump, HydraulicPump, etc.)",
                "operating_hours": "integer or null - Operating hours",
                "max_lifespan": "integer or null - Maximum lifespan in hours",
                "maintenance_interval": "integer or null - Maintenance interval in hours",
                "pressure_bar": "number or null - Pressure in bar",
                "temperature_c": "number or null - Temperature in Celsius",
                "status": "string or null - Status (active, defective, maintenance)"
            },
            "maintenance": {
                "date": "string or null - Date in format YYYY-MM-DD",
                "description": "string or null - Description of maintenance"
            },
            "measurements": [
                {
                    "type": "string - Type of measurement",
                    "value": "number - Measured value",
                    "unit": "string - Unit"
                }
            ]
        }

    schema_str = json.dumps(schema, indent=2, ensure_ascii=False)

    return f"""Analyze the following technical text and extract structured information according to the schema.

SCHEMA:
{schema_str}

TEXT:
{input_text}

IMPORTANT:
- Respond ONLY with valid JSON
- Extract ALL information present in the text
- Numbers with thousands separators (e.g., 15,000 or 15.000) extract as integers without separators (15000)
- For missing information: use null
- No explanations or comments outside the JSON

JSON:"""


CORRECTION_SYSTEM_PROMPT = """You are a correction assistant for technical data.
Your task is to correct logical errors and inconsistencies in technical texts.
You must adjust the corrected values so that all constraints are satisfied.
Keep all correct information unchanged."""


def get_correction_prompt(
    original_text: str,
    violations: list[dict],
    iteration: int = 1,
) -> str:
    """Generate a correction prompt for fixing constraint violations.

    Args:
        original_text: The original text with errors
        violations: List of constraint violations
        iteration: Current iteration number (for escalating specificity)

    Returns:
        The formatted correction prompt
    """
    violations_text = "\n".join([
        f"- {v.get('type', 'ERROR')}: {v.get('message', 'Unknown error')}"
        for v in violations
    ])

    # Escalate specificity based on iteration
    if iteration <= 1:
        instruction = "Correct the text so that all mentioned problems are fixed."
    elif iteration == 2:
        instruction = """Correct the text with the following specific instructions:
- Adjust the incorrect values so they comply with the constraints
- Maintenance interval must be less than or equal to maximum lifespan
- Operating hours must be less than or equal to maximum lifespan
- Pressure must be between 0 and 350 bar"""
    else:
        # Most specific - give explicit guidance
        hints = []
        for v in violations:
            msg = v.get("message", "").lower()
            if "maintenance_interval" in msg or "wartungsintervall" in msg:
                hints.append("Set maintenance interval to a value <= maximum lifespan")
            if "operating_hours" in msg or "betriebsstunden" in msg:
                hints.append("Reduce operating hours or increase maximum lifespan")
            if "pressure" in msg or "druck" in msg:
                hints.append("Set pressure to a value between 0 and 350 bar")

        instruction = f"""Correct the text with these EXPLICIT instructions:
{chr(10).join(f'- {h}' for h in hints) if hints else '- Adjust all incorrect values accordingly'}"""

    return f"""The following technical text contains logical errors or inconsistencies:

ORIGINAL:
{original_text}

DETECTED PROBLEMS:
{violations_text}

REQUIREMENTS:
{instruction}
- Keep all correct information UNCHANGED
- Change ONLY the incorrect values/statements
- The corrected text must be in the same format as the original

CORRECTED TEXT:"""


def get_extraction_schema() -> dict:
    """Get the JSON schema for data extraction.

    Returns:
        JSON schema dictionary
    """
    return {
        "type": "object",
        "properties": {
            "component": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["Motor", "ElectricMotor", "Pump", "HydraulicPump",
                                "VacuumPump", "Valve", "Sensor", "PressureSensor",
                                "TemperatureSensor", "Container", "Unknown"]
                    },
                    "operating_hours": {"type": ["integer", "null"]},
                    "max_lifespan": {"type": ["integer", "null"]},
                    "maintenance_interval": {"type": ["integer", "null"]},
                    "pressure_bar": {"type": ["number", "null"]},
                    "temperature_c": {"type": ["number", "null"]},
                    "rpm": {"type": ["integer", "null"]},
                    "serial_number": {"type": ["string", "null"]},
                    "status": {"type": ["string", "null"]}
                },
                "required": ["name", "type"]
            },
            "maintenance": {
                "type": ["object", "null"],
                "properties": {
                    "date": {"type": ["string", "null"]},
                    "description": {"type": ["string", "null"]},
                    "technician": {"type": ["string", "null"]}
                }
            },
            "measurements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string"},
                        "value": {"type": "number"},
                        "unit": {"type": "string"}
                    },
                    "required": ["type", "value", "unit"]
                }
            }
        }
    }
