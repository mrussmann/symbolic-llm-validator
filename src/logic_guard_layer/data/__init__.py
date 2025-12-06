"""Data files for Logic-Guard-Layer."""

from pathlib import Path

DATA_DIR = Path(__file__).parent
ONTOLOGY_PATH = DATA_DIR / "maintenance.owl"
SCHEMA_PATH = DATA_DIR / "maintenance_schema.json"

__all__ = ["DATA_DIR", "ONTOLOGY_PATH", "SCHEMA_PATH"]
