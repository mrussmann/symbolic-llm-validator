"""Ontology loading and management for Logic-Guard-Layer."""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class OntologyLoader:
    """Loads and manages the OWL ontology."""

    _instance: Optional["OntologyLoader"] = None
    _ontology = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern for ontology loader."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, ontology_path: Optional[Path] = None):
        """Initialize the ontology loader.

        Args:
            ontology_path: Path to the OWL ontology file
        """
        if hasattr(self, "_initialized") and self._initialized:
            return

        self._initialized = True
        self._ontology_path = ontology_path
        self._ontology = None
        self._concepts: dict[str, list[str]] = {}
        self._properties: dict[str, dict] = {}

    def load(self, path: Optional[Path] = None) -> bool:
        """Load the ontology from file.

        Args:
            path: Optional path override

        Returns:
            True if loaded successfully
        """
        try:
            from owlready2 import get_ontology

            ontology_path = path or self._ontology_path
            if ontology_path is None:
                # Use default path
                package_dir = Path(__file__).parent.parent
                ontology_path = package_dir / "data" / "maintenance.owl"

            if not ontology_path.exists():
                logger.error(f"Ontology file not found: {ontology_path}")
                return False

            logger.info(f"Loading ontology from: {ontology_path}")
            self._ontology = get_ontology(f"file://{ontology_path}").load()
            self._extract_concepts()
            self._extract_properties()
            logger.info(f"Ontology loaded: {len(self._concepts)} concepts, {len(self._properties)} properties")
            return True

        except Exception as e:
            logger.error(f"Failed to load ontology: {e}")
            return False

    def _extract_concepts(self):
        """Extract concept hierarchy from ontology."""
        if self._ontology is None:
            return

        self._concepts = {}
        for cls in self._ontology.classes():
            name = cls.name
            parent_names = [p.name for p in cls.is_a if hasattr(p, "name")]
            self._concepts[name] = parent_names

    def _extract_properties(self):
        """Extract properties from ontology."""
        if self._ontology is None:
            return

        self._properties = {}

        # Data properties
        for prop in self._ontology.data_properties():
            self._properties[prop.name] = {
                "type": "datatype",
                "domain": [d.name for d in prop.domain] if prop.domain else [],
                "range": str(prop.range[0]) if prop.range else "unknown",
            }

        # Object properties
        for prop in self._ontology.object_properties():
            self._properties[prop.name] = {
                "type": "object",
                "domain": [d.name for d in prop.domain] if prop.domain else [],
                "range": [r.name for r in prop.range] if prop.range else [],
            }

    @property
    def ontology(self):
        """Get the loaded ontology."""
        return self._ontology

    @property
    def is_loaded(self) -> bool:
        """Check if ontology is loaded."""
        return self._ontology is not None

    def get_concepts(self) -> dict[str, list[str]]:
        """Get all concepts with their parent classes."""
        return self._concepts.copy()

    def get_concept_hierarchy(self) -> list[dict]:
        """Get concepts as a hierarchical structure for display."""
        if not self._concepts:
            return []

        # Find root concepts (those with only 'Thing' as parent or no parent)
        roots = []
        for name, parents in self._concepts.items():
            if not parents or all(p == "Thing" for p in parents):
                roots.append(name)

        def build_tree(concept_name: str) -> dict:
            children = [
                name for name, parents in self._concepts.items()
                if concept_name in parents
            ]
            return {
                "name": concept_name,
                "children": [build_tree(c) for c in sorted(children)]
            }

        return [build_tree(root) for root in sorted(roots)]

    def get_properties(self) -> dict[str, dict]:
        """Get all properties."""
        return self._properties.copy()

    def is_valid_type(self, type_name: str) -> bool:
        """Check if a type name is valid in the ontology."""
        return type_name in self._concepts

    def get_parent_types(self, type_name: str) -> list[str]:
        """Get parent types for a given type."""
        return self._concepts.get(type_name, [])

    def create_instance(self, class_name: str, instance_name: str):
        """Create an instance of a class in the ontology.

        Args:
            class_name: Name of the class
            instance_name: Name for the new instance

        Returns:
            The created instance or None
        """
        if self._ontology is None:
            return None

        cls = getattr(self._ontology, class_name, None)
        if cls is None:
            return None

        with self._ontology:
            instance = cls(instance_name)
        return instance

    def run_reasoner(self) -> bool:
        """Run the reasoner on the ontology.

        Returns:
            True if reasoning completed without errors
        """
        if self._ontology is None:
            return False

        try:
            from owlready2 import sync_reasoner_hermit
            sync_reasoner_hermit(self._ontology, infer_property_values=True)
            return True
        except Exception as e:
            logger.error(f"Reasoner error: {e}")
            return False


# Global loader instance
_loader: Optional[OntologyLoader] = None


def get_ontology_loader(path: Optional[Path] = None) -> OntologyLoader:
    """Get the global ontology loader instance.

    Args:
        path: Optional path to ontology file

    Returns:
        OntologyLoader instance
    """
    global _loader
    if _loader is None:
        _loader = OntologyLoader(path)
    return _loader


def load_ontology(path: Optional[Path] = None) -> OntologyLoader:
    """Load the ontology and return the loader.

    Args:
        path: Optional path to ontology file

    Returns:
        OntologyLoader instance with loaded ontology
    """
    loader = get_ontology_loader(path)
    if not loader.is_loaded:
        loader.load(path)
    return loader
