"""Tests for OntologyManager."""

import pytest
from datetime import datetime

from logic_guard_layer.ontology.manager import (
    OntologyManager,
    OntologyInfo,
    get_ontology_manager,
)


@pytest.fixture
def fresh_manager():
    """Create a fresh OntologyManager instance (bypass singleton)."""
    # Reset the singleton for testing
    OntologyManager._instance = None
    manager = OntologyManager()
    yield manager
    # Cleanup after test
    OntologyManager._instance = None


class TestOntologyInfo:
    """Tests for OntologyInfo dataclass."""

    def test_create_ontology_info(self):
        """Test creating ontology info."""
        info = OntologyInfo(
            name="test",
            description="Test ontology",
            version="1.0.0",
            created_at=datetime.now(),
            concepts_count=5,
            constraints_count=3,
            is_default=False
        )
        assert info.name == "test"
        assert info.description == "Test ontology"
        assert info.version == "1.0.0"
        assert info.concepts_count == 5
        assert info.constraints_count == 3
        assert info.is_default is False

    def test_default_flag(self):
        """Test default flag."""
        info = OntologyInfo(
            name="test",
            description="Test",
            version="1.0.0",
            created_at=datetime.now(),
            concepts_count=0,
            constraints_count=0
        )
        assert info.is_default is False


class TestOntologyManager:
    """Tests for OntologyManager class."""

    def test_singleton_pattern(self):
        """Test OntologyManager is a singleton."""
        OntologyManager._instance = None
        manager1 = OntologyManager()
        manager2 = OntologyManager()
        assert manager1 is manager2
        OntologyManager._instance = None

    def test_initial_state(self, fresh_manager):
        """Test initial state after creation."""
        assert fresh_manager._active == "maintenance"
        assert len(fresh_manager._ontologies) == 0

    def test_validate_schema_valid(self, fresh_manager, valid_ontology_schema):
        """Test validating a valid schema."""
        errors = fresh_manager.validate_schema(valid_ontology_schema)
        assert len(errors) == 0

    def test_validate_schema_not_dict(self, fresh_manager):
        """Test validating non-dict schema."""
        errors = fresh_manager.validate_schema("not a dict")
        assert len(errors) == 1
        assert "JSON object" in errors[0]

    def test_validate_schema_no_definitions(self, fresh_manager, invalid_ontology_schema_no_definitions):
        """Test validating schema without definitions."""
        errors = fresh_manager.validate_schema(invalid_ontology_schema_no_definitions)
        assert len(errors) == 1
        assert "definitions" in errors[0]

    def test_validate_schema_no_concepts(self, fresh_manager):
        """Test validating schema without concepts."""
        # Schema with definitions but no concepts
        schema = {
            "definitions": {
                "properties": {"test": "value"}
            }
        }
        errors = fresh_manager.validate_schema(schema)
        assert len(errors) == 1
        assert "concepts" in errors[0]

    def test_validate_schema_invalid_definitions(self, fresh_manager):
        """Test validating schema with invalid definitions type."""
        schema = {
            "definitions": "not a dict"
        }
        errors = fresh_manager.validate_schema(schema)
        assert len(errors) == 1
        assert "object" in errors[0]

    def test_validate_schema_concept_missing_description(self, fresh_manager):
        """Test validating schema with concept missing description."""
        schema = {
            "definitions": {
                "concepts": {
                    "Component": {}  # Missing description
                }
            }
        }
        errors = fresh_manager.validate_schema(schema)
        assert len(errors) == 1
        assert "description" in errors[0]

    def test_validate_schema_invalid_constraints(self, fresh_manager):
        """Test validating schema with invalid constraints."""
        schema = {
            "definitions": {
                "concepts": {
                    "Component": {"description": "Test"}
                },
                "constraints": [
                    {"id": "C1"}  # Missing name and expression
                ]
            }
        }
        errors = fresh_manager.validate_schema(schema)
        assert len(errors) == 2  # Missing name and expression

    def test_register_valid_ontology(self, fresh_manager, valid_ontology_schema):
        """Test registering a valid ontology."""
        errors = fresh_manager.register("custom-ontology", valid_ontology_schema, "Custom description")
        assert len(errors) == 0
        assert fresh_manager.exists("custom-ontology")

    def test_register_empty_name(self, fresh_manager, valid_ontology_schema):
        """Test registering with empty name."""
        errors = fresh_manager.register("", valid_ontology_schema)
        assert len(errors) == 1
        assert "empty" in errors[0].lower()

    def test_register_whitespace_name(self, fresh_manager, valid_ontology_schema):
        """Test registering with whitespace-only name."""
        errors = fresh_manager.register("   ", valid_ontology_schema)
        assert len(errors) == 1
        assert "empty" in errors[0].lower()

    def test_register_cannot_overwrite_maintenance(self, fresh_manager, valid_ontology_schema):
        """Test cannot overwrite the default maintenance ontology."""
        errors = fresh_manager.register("maintenance", valid_ontology_schema)
        assert len(errors) == 1
        assert "maintenance" in errors[0].lower()

    def test_register_name_normalization(self, fresh_manager, valid_ontology_schema):
        """Test name is normalized (lowercase, hyphenated)."""
        errors = fresh_manager.register("My Custom Ontology", valid_ontology_schema)
        assert len(errors) == 0
        assert fresh_manager.exists("my-custom-ontology")

    def test_register_invalid_schema(self, fresh_manager, invalid_ontology_schema_no_definitions):
        """Test registering with invalid schema."""
        errors = fresh_manager.register("invalid", invalid_ontology_schema_no_definitions)
        assert len(errors) > 0

    def test_get_existing_ontology(self, fresh_manager, valid_ontology_schema):
        """Test getting an existing ontology."""
        fresh_manager.register("test-ontology", valid_ontology_schema)
        schema = fresh_manager.get("test-ontology")
        assert schema is not None
        assert schema == valid_ontology_schema

    def test_get_nonexistent_ontology(self, fresh_manager):
        """Test getting a non-existent ontology."""
        schema = fresh_manager.get("nonexistent")
        assert schema is None

    def test_get_info_existing(self, fresh_manager, valid_ontology_schema):
        """Test getting info for existing ontology."""
        fresh_manager.register("test-ontology", valid_ontology_schema, "Test description")
        info = fresh_manager.get_info("test-ontology")
        assert info is not None
        assert info.name == "test-ontology"
        assert info.description == "Test description"
        assert info.is_default is False

    def test_get_info_nonexistent(self, fresh_manager):
        """Test getting info for non-existent ontology."""
        info = fresh_manager.get_info("nonexistent")
        assert info is None

    def test_list_ontologies(self, fresh_manager, valid_ontology_schema):
        """Test listing all ontologies."""
        fresh_manager.register("ontology1", valid_ontology_schema)
        fresh_manager.register("ontology2", valid_ontology_schema)
        ontologies = fresh_manager.list_ontologies()
        assert len(ontologies) == 2

    def test_list_names(self, fresh_manager, valid_ontology_schema):
        """Test listing ontology names."""
        fresh_manager.register("ontology1", valid_ontology_schema)
        fresh_manager.register("ontology2", valid_ontology_schema)
        names = fresh_manager.list_names()
        assert "ontology1" in names
        assert "ontology2" in names

    def test_set_active_existing(self, fresh_manager, valid_ontology_schema):
        """Test setting active to existing ontology."""
        fresh_manager.register("test-ontology", valid_ontology_schema)
        result = fresh_manager.set_active("test-ontology")
        assert result is True
        assert fresh_manager.get_active_name() == "test-ontology"

    def test_set_active_nonexistent(self, fresh_manager):
        """Test setting active to non-existent ontology."""
        result = fresh_manager.set_active("nonexistent")
        assert result is False

    def test_get_active(self, fresh_manager, valid_ontology_schema):
        """Test getting active ontology."""
        fresh_manager.register("test-ontology", valid_ontology_schema)
        fresh_manager.set_active("test-ontology")
        name, schema = fresh_manager.get_active()
        assert name == "test-ontology"
        assert schema == valid_ontology_schema

    def test_get_active_name(self, fresh_manager, valid_ontology_schema):
        """Test getting active ontology name."""
        fresh_manager.register("test-ontology", valid_ontology_schema)
        fresh_manager.set_active("test-ontology")
        assert fresh_manager.get_active_name() == "test-ontology"

    def test_delete_existing_custom(self, fresh_manager, valid_ontology_schema):
        """Test deleting an existing custom ontology."""
        fresh_manager.register("test-ontology", valid_ontology_schema)
        assert fresh_manager.exists("test-ontology")
        result = fresh_manager.delete("test-ontology")
        assert result is True
        assert not fresh_manager.exists("test-ontology")

    def test_delete_nonexistent(self, fresh_manager):
        """Test deleting a non-existent ontology."""
        result = fresh_manager.delete("nonexistent")
        assert result is False

    def test_delete_default_ontology(self, fresh_manager):
        """Test cannot delete the default maintenance ontology."""
        result = fresh_manager.delete("maintenance")
        assert result is False

    def test_delete_active_switches_to_default(self, fresh_manager, valid_ontology_schema):
        """Test deleting active ontology switches to default."""
        fresh_manager.register("test-ontology", valid_ontology_schema)
        fresh_manager.set_active("test-ontology")
        fresh_manager.delete("test-ontology")
        assert fresh_manager.get_active_name() == "maintenance"

    def test_exists(self, fresh_manager, valid_ontology_schema):
        """Test exists method."""
        assert not fresh_manager.exists("test-ontology")
        fresh_manager.register("test-ontology", valid_ontology_schema)
        assert fresh_manager.exists("test-ontology")


class TestGetOntologyManager:
    """Tests for get_ontology_manager function."""

    def test_returns_singleton(self):
        """Test get_ontology_manager returns same instance."""
        # Reset singleton
        OntologyManager._instance = None

        manager1 = get_ontology_manager()
        manager2 = get_ontology_manager()
        assert manager1 is manager2

        # Cleanup
        OntologyManager._instance = None

    def test_creates_manager_on_first_call(self):
        """Test manager is created on first call."""
        OntologyManager._instance = None

        import logic_guard_layer.ontology.manager as manager_module
        manager_module._manager = None

        manager = get_ontology_manager()
        assert manager is not None

        # Cleanup
        OntologyManager._instance = None
        manager_module._manager = None


class TestOntologyManagerIntegration:
    """Integration tests for OntologyManager."""

    def test_full_workflow(self, fresh_manager, valid_ontology_schema):
        """Test full registration, activation, deletion workflow."""
        # Register
        errors = fresh_manager.register("workflow-test", valid_ontology_schema, "Workflow test")
        assert len(errors) == 0

        # Verify exists
        assert fresh_manager.exists("workflow-test")

        # Get info
        info = fresh_manager.get_info("workflow-test")
        assert info.name == "workflow-test"

        # Activate
        result = fresh_manager.set_active("workflow-test")
        assert result is True
        assert fresh_manager.get_active_name() == "workflow-test"

        # Get active schema
        name, schema = fresh_manager.get_active()
        assert name == "workflow-test"
        assert schema == valid_ontology_schema

        # List
        names = fresh_manager.list_names()
        assert "workflow-test" in names

        # Delete
        result = fresh_manager.delete("workflow-test")
        assert result is True
        assert not fresh_manager.exists("workflow-test")

        # Active should switch to default
        assert fresh_manager.get_active_name() == "maintenance"

    def test_multiple_ontologies(self, fresh_manager, valid_ontology_schema):
        """Test managing multiple ontologies."""
        # Register multiple
        for i in range(5):
            errors = fresh_manager.register(f"ontology-{i}", valid_ontology_schema)
            assert len(errors) == 0

        # List should have all
        names = fresh_manager.list_names()
        assert len(names) == 5

        # Activate different ones
        for i in range(5):
            result = fresh_manager.set_active(f"ontology-{i}")
            assert result is True
            assert fresh_manager.get_active_name() == f"ontology-{i}"

        # Delete some
        fresh_manager.delete("ontology-1")
        fresh_manager.delete("ontology-3")

        names = fresh_manager.list_names()
        assert len(names) == 3
        assert "ontology-0" in names
        assert "ontology-2" in names
        assert "ontology-4" in names

    def test_schema_with_all_sections(self, fresh_manager):
        """Test schema with all optional sections."""
        full_schema = {
            "name": "full-test",
            "version": "2.0.0",
            "description": "Complete test ontology",
            "definitions": {
                "concepts": {
                    "Component": {"description": "Base component"},
                    "Motor": {"description": "Electric motor", "parent": "Component"},
                    "Pump": {"description": "Fluid pump", "parent": "Component"},
                },
                "properties": {
                    "operating_hours": {"type": "integer", "min": 0},
                    "max_lifespan": {"type": "integer", "min": 1},
                },
                "constraints": [
                    {"id": "C1", "name": "Hours non-negative", "expression": "operating_hours >= 0"},
                    {"id": "C2", "name": "Lifespan positive", "expression": "max_lifespan > 0"},
                ]
            }
        }

        errors = fresh_manager.validate_schema(full_schema)
        assert len(errors) == 0

        errors = fresh_manager.register("full-test", full_schema)
        assert len(errors) == 0

        info = fresh_manager.get_info("full-test")
        assert info.concepts_count == 3
        assert info.constraints_count == 2
