"""
Ontology Manager for handling multiple ontologies in-memory.

Provides functionality to:
- Register/upload new ontologies
- List available ontologies
- Switch active ontology
- Validate ontology schema structure
"""

import json
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class OntologyInfo:
    """Metadata about a registered ontology."""
    name: str
    description: str
    version: str
    created_at: datetime
    concepts_count: int
    constraints_count: int
    is_default: bool = False


class OntologyManager:
    """
    Manages multiple ontologies in-memory with support for uploading,
    listing, and switching between ontologies.
    """

    _instance: Optional["OntologyManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._ontologies: dict[str, dict] = {}
        self._active: str = "maintenance"
        self._initialized = True
        logger.info("OntologyManager initialized")

    def load_default_ontology(self, schema_path: Path) -> None:
        """Load the default maintenance ontology from disk."""
        try:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema = json.load(f)

            self._ontologies["maintenance"] = {
                "schema": schema,
                "info": OntologyInfo(
                    name="maintenance",
                    description=schema.get("description", "Default maintenance ontology"),
                    version=schema.get("version", "1.0.0"),
                    created_at=datetime.now(),
                    concepts_count=len(schema.get("definitions", {}).get("concepts", {})),
                    constraints_count=len(schema.get("definitions", {}).get("constraints", [])),
                    is_default=True
                )
            }
            self._active = "maintenance"
            logger.info(f"Loaded default ontology from {schema_path}")
        except Exception as e:
            logger.error(f"Failed to load default ontology: {e}")
            raise

    def validate_schema(self, schema: dict) -> list[str]:
        """
        Validate that a schema has the required structure.
        Returns list of error messages (empty if valid).
        """
        errors = []

        # Check top-level structure
        if not isinstance(schema, dict):
            errors.append("Schema must be a JSON object")
            return errors

        # Check for definitions section
        definitions = schema.get("definitions")
        if not definitions:
            errors.append("Schema must have a 'definitions' section")
            return errors

        if not isinstance(definitions, dict):
            errors.append("'definitions' must be an object")
            return errors

        # Check for concepts
        concepts = definitions.get("concepts")
        if not concepts:
            errors.append("Schema must have 'definitions.concepts'")
        elif not isinstance(concepts, dict):
            errors.append("'definitions.concepts' must be an object")
        else:
            # Validate each concept
            for name, concept in concepts.items():
                if not isinstance(concept, dict):
                    errors.append(f"Concept '{name}' must be an object")
                    continue
                if "description" not in concept:
                    errors.append(f"Concept '{name}' missing 'description'")

        # Check for properties (optional but should be object if present)
        properties = definitions.get("properties")
        if properties is not None and not isinstance(properties, dict):
            errors.append("'definitions.properties' must be an object if present")

        # Check for constraints (optional but should be list if present)
        constraints = definitions.get("constraints")
        if constraints is not None:
            if not isinstance(constraints, list):
                errors.append("'definitions.constraints' must be an array if present")
            else:
                for i, constraint in enumerate(constraints):
                    if not isinstance(constraint, dict):
                        errors.append(f"Constraint {i} must be an object")
                        continue
                    if "id" not in constraint:
                        errors.append(f"Constraint {i} missing 'id'")
                    if "name" not in constraint:
                        errors.append(f"Constraint {i} missing 'name'")
                    if "expression" not in constraint:
                        errors.append(f"Constraint {i} missing 'expression'")

        return errors

    def register(self, name: str, schema: dict, description: str = "") -> list[str]:
        """
        Register a new ontology.
        Returns list of validation errors (empty if successful).
        """
        # Validate name
        if not name or not name.strip():
            return ["Ontology name cannot be empty"]

        name = name.strip().lower().replace(" ", "-")

        if name == "maintenance":
            return ["Cannot overwrite the default 'maintenance' ontology"]

        # Validate schema
        errors = self.validate_schema(schema)
        if errors:
            return errors

        # Get metadata from schema
        definitions = schema.get("definitions", {})
        concepts = definitions.get("concepts", {})
        constraints = definitions.get("constraints", [])

        self._ontologies[name] = {
            "schema": schema,
            "info": OntologyInfo(
                name=name,
                description=description or schema.get("description", f"Custom ontology: {name}"),
                version=schema.get("version", "1.0.0"),
                created_at=datetime.now(),
                concepts_count=len(concepts),
                constraints_count=len(constraints),
                is_default=False
            )
        }

        logger.info(f"Registered ontology '{name}' with {len(concepts)} concepts and {len(constraints)} constraints")
        return []

    def get(self, name: str) -> Optional[dict]:
        """Get an ontology schema by name."""
        entry = self._ontologies.get(name)
        return entry["schema"] if entry else None

    def get_info(self, name: str) -> Optional[OntologyInfo]:
        """Get ontology metadata by name."""
        entry = self._ontologies.get(name)
        return entry["info"] if entry else None

    def list_ontologies(self) -> list[OntologyInfo]:
        """List all registered ontologies."""
        return [entry["info"] for entry in self._ontologies.values()]

    def list_names(self) -> list[str]:
        """List names of all registered ontologies."""
        return list(self._ontologies.keys())

    def set_active(self, name: str) -> bool:
        """Set the active ontology. Returns True if successful."""
        if name not in self._ontologies:
            logger.warning(f"Attempted to activate unknown ontology: {name}")
            return False
        self._active = name
        logger.info(f"Active ontology set to: {name}")
        return True

    def get_active(self) -> tuple[str, dict]:
        """Get the currently active ontology (name, schema)."""
        schema = self._ontologies.get(self._active, {}).get("schema", {})
        return self._active, schema

    def get_active_name(self) -> str:
        """Get the name of the active ontology."""
        return self._active

    def delete(self, name: str) -> bool:
        """
        Delete an ontology. Cannot delete the default ontology.
        Returns True if successful.
        """
        if name == "maintenance":
            logger.warning("Attempted to delete default ontology")
            return False

        if name not in self._ontologies:
            return False

        del self._ontologies[name]

        # If we deleted the active ontology, switch to default
        if self._active == name:
            self._active = "maintenance"
            logger.info("Switched to default ontology after deletion")

        logger.info(f"Deleted ontology: {name}")
        return True

    def exists(self, name: str) -> bool:
        """Check if an ontology exists."""
        return name in self._ontologies


# Global singleton instance
_manager: Optional[OntologyManager] = None


def get_ontology_manager() -> OntologyManager:
    """Get the global OntologyManager instance."""
    global _manager
    if _manager is None:
        _manager = OntologyManager()
    return _manager
