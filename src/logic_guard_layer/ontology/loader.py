"""Ontology loading and management for Logic-Guard-Layer."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class OWLViolation:
    """Represents a constraint violation detected by OWL reasoning."""
    violation_type: str
    constraint_name: str
    message: str
    property_name: Optional[str] = None
    actual_value: Any = None
    expected_value: Any = None


class OntologyLoader:
    """Loads and manages the OWL ontology with SWRL rules for physics-based validation."""

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
        self._swrl_rules_added = False
        self._instance_counter = 0

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
            self._add_swrl_rules()
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

    def _add_swrl_rules(self):
        """Add SWRL rules for physics-based constraint validation.

        Note: SWRL rules with swrlb: built-ins require a Java reasoner and full
        SWRL namespace. The actual physics checks are done programmatically in
        _check_carnot_limit, _check_pump_power_balance, _check_compressor_thermodynamics.
        """
        if self._ontology is None or self._swrl_rules_added:
            return

        # Mark as added - we use programmatic checks as fallback
        self._swrl_rules_added = True
        logger.debug("SWRL rules initialized (using programmatic physics checks)")

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

    def get_all_ancestor_types(self, type_name: str) -> set[str]:
        """Get all ancestor types (parents, grandparents, etc.) for a given type.

        This uses the full OWL class hierarchy for proper inheritance.
        """
        ancestors = set()

        if self._ontology is None:
            return ancestors

        cls = getattr(self._ontology, type_name, None)
        if cls is None:
            return ancestors

        # Use owlready2's ancestors() method for complete hierarchy
        try:
            for ancestor in cls.ancestors():
                if hasattr(ancestor, 'name'):
                    ancestors.add(ancestor.name)
        except Exception:
            # Fallback to manual traversal
            to_visit = [type_name]
            while to_visit:
                current = to_visit.pop()
                if current in ancestors:
                    continue
                ancestors.add(current)
                parents = self._concepts.get(current, [])
                to_visit.extend(parents)

        return ancestors

    def infer_component_type(self, data: dict) -> Optional[str]:
        """Infer the most specific component type based on properties present.

        Args:
            data: Dictionary with component properties

        Returns:
            Inferred type name or None
        """
        if self._ontology is None:
            return None

        # Check for type-specific properties to infer type
        type_indicators = {
            # Heat pump indicators
            "Waermepumpe": ["cop", "hatCOP", "quelltemperatur", "vorlauftemperatur"],
            # Pump indicators
            "Pumpe": ["npsh_available", "npsh_required", "hatNPSHverfuegbar", "hatNPSHerforderlich", "hydraulikleistung"],
            "Kreiselpumpe": ["npsh_available", "npsh_required"],
            # Compressor indicators
            "Kompressor": ["eingangsdruck", "ausgangsdruck", "eingangstemperatur", "ausgangstemperatur"],
            # Battery indicators
            "Batteriespeicher": ["ladezustand", "ladezyklen", "soc", "state_of_charge"],
            # Wind turbine indicators
            "Windturbine": ["leistungsbeiwert", "cp", "rotordurchmesser"],
        }

        data_keys = set(k.lower() for k in data.keys())

        best_match = None
        best_score = 0

        for type_name, indicators in type_indicators.items():
            score = sum(1 for ind in indicators if ind.lower() in data_keys)
            if score > best_score:
                best_score = score
                best_match = type_name

        return best_match

    def create_instance(self, class_name: str, instance_name: Optional[str] = None):
        """Create an instance of a class in the ontology.

        Args:
            class_name: Name of the class
            instance_name: Name for the new instance (auto-generated if not provided)

        Returns:
            The created instance or None
        """
        if self._ontology is None:
            return None

        cls = getattr(self._ontology, class_name, None)
        if cls is None:
            # Try to find class by looking through all classes
            for onto_cls in self._ontology.classes():
                if onto_cls.name == class_name:
                    cls = onto_cls
                    break

        if cls is None:
            logger.warning(f"Class not found in ontology: {class_name}")
            return None

        if instance_name is None:
            self._instance_counter += 1
            instance_name = f"{class_name}_instance_{self._instance_counter}"

        with self._ontology:
            instance = cls(instance_name)
        return instance

    def create_instance_from_data(self, data: dict) -> Optional[Any]:
        """Create an OWL instance from a data dictionary.

        Args:
            data: Dictionary with component data

        Returns:
            Created OWL instance or None
        """
        if self._ontology is None:
            return None

        # Determine component type
        component_type = (
            data.get("typ") or
            data.get("type") or
            self.infer_component_type(data) or
            "Komponente"
        )

        # Map common English type names to German ontology names
        type_mapping = {
            "pump": "Pumpe",
            "centrifugalpump": "Kreiselpumpe",
            "hydraulicpump": "Hydraulikpumpe",
            "motor": "Motor",
            "electricmotor": "Elektromotor",
            "compressor": "Kompressor",
            "heatpump": "Waermepumpe",
            "heatexchanger": "Waermetauscher",
            "battery": "Batteriespeicher",
            "batterystorage": "Batteriespeicher",
            "windturbine": "Windturbine",
            "gasturbine": "Gasturbine",
            "sensor": "Sensor",
            "valve": "Ventil",
            "component": "Komponente",
        }

        normalized_type = component_type.lower().replace(" ", "").replace("_", "")
        component_type = type_mapping.get(normalized_type, component_type)

        # Create instance
        instance_name = data.get("name") or data.get("seriennummer") or data.get("serial_number")
        instance = self.create_instance(component_type, instance_name)

        if instance is None:
            logger.warning(f"Could not create instance for type: {component_type}")
            return None

        # Property mapping: data key -> OWL property name
        property_mapping = {
            # Operating hours
            "operating_hours": "hatBetriebsstunden",
            "betriebsstunden": "hatBetriebsstunden",
            # Max lifespan
            "max_lifespan": "hatMaxLebensdauer",
            "max_lebensdauer": "hatMaxLebensdauer",
            # Maintenance interval
            "maintenance_interval": "hatWartungsintervall",
            "wartungsintervall": "hatWartungsintervall",
            # Pressure
            "pressure_bar": "hatDruckBar",
            "druck_bar": "hatDruckBar",
            "druck": "hatDruckBar",
            # Temperature
            "temperature_c": "hatTemperaturC",
            "temperatur_c": "hatTemperaturC",
            "temperatur": "hatTemperaturC",
            # RPM
            "rpm": "hatDrehzahl",
            "drehzahl": "hatDrehzahl",
            # Efficiency
            "efficiency": "hatWirkungsgrad",
            "wirkungsgrad": "hatWirkungsgrad",
            "eta": "hatWirkungsgrad",
            # NPSH
            "npsh_available": "hatNPSHverfuegbar",
            "npsh_verfuegbar": "hatNPSHverfuegbar",
            "npsha": "hatNPSHverfuegbar",
            "npsh_required": "hatNPSHerforderlich",
            "npsh_erforderlich": "hatNPSHerforderlich",
            "npshr": "hatNPSHerforderlich",
            # COP
            "cop": "hatCOP",
            "leistungszahl": "hatCOP",
            # Heat pump temperatures
            "t_source": "hatQuelltemperatur",
            "temperatur_quelle": "hatQuelltemperatur",
            "quelltemperatur": "hatQuelltemperatur",
            "t_sink": "hatVorlauftemperatur",
            "temperatur_vorlauf": "hatVorlauftemperatur",
            "vorlauftemperatur": "hatVorlauftemperatur",
            # Battery
            "soc": "hatLadezustand",
            "state_of_charge": "hatLadezustand",
            "ladezustand_soc": "hatLadezustand",
            "ladezustand": "hatLadezustand",
            "charge_cycles": "hatLadezyklen",
            "ladezyklen": "hatLadezyklen",
            "max_cycles": "hatMaxLadezyklen",
            "maximale_ladezyklen": "hatMaxLadezyklen",
            # Power
            "power_input": "hatLeistungsaufnahme",
            "leistungsaufnahme": "hatLeistungsaufnahme",
            "hydraulic_power": "hatHydraulikleistung",
            "hydraulikleistung": "hatHydraulikleistung",
            # Compressor
            "t_inlet": "hatEingangstemperatur",
            "temperatur_eingang": "hatEingangstemperatur",
            "t_outlet": "hatAusgangstemperatur",
            "temperatur_ausgang": "hatAusgangstemperatur",
            "p_inlet": "hatEingangsdruck",
            "druck_eingang": "hatEingangsdruck",
            "p_outlet": "hatAusgangsdruck",
            "druck_ausgang": "hatAusgangsdruck",
            # Wind turbine
            "cp": "hatLeistungsbeiwert",
            "leistungsbeiwert": "hatLeistungsbeiwert",
            # Serial number
            "serial_number": "hatSeriennummer",
            "seriennummer": "hatSeriennummer",
        }

        with self._ontology:
            for data_key, value in data.items():
                if value is None:
                    continue

                # Find the OWL property name
                owl_prop_name = property_mapping.get(data_key.lower())
                if owl_prop_name is None:
                    continue

                # Get the property from ontology
                owl_prop = getattr(self._ontology, owl_prop_name, None)
                if owl_prop is None:
                    continue

                # Set the property value
                try:
                    setattr(instance, owl_prop_name, [value])
                except Exception as e:
                    logger.debug(f"Could not set property {owl_prop_name}: {e}")

        return instance

    def run_reasoner(self, debug: bool = False) -> bool:
        """Run the reasoner on the ontology.

        Args:
            debug: Enable debug output from reasoner

        Returns:
            True if reasoning completed without errors
        """
        if self._ontology is None:
            return False

        try:
            from owlready2 import sync_reasoner_pellet

            sync_reasoner_pellet(
                self._ontology,
                infer_property_values=True,
                debug=1 if debug else 0
            )
            return True
        except Exception as e:
            # Try HermiT if Pellet fails
            try:
                from owlready2 import sync_reasoner_hermit
                sync_reasoner_hermit(self._ontology, infer_property_values=True)
                return True
            except Exception as e2:
                logger.error(f"Reasoner error (Pellet: {e}, HermiT: {e2})")
                return False

    def validate_instance(self, instance) -> list[OWLViolation]:
        """Validate an instance and return any violations detected by reasoning.

        Args:
            instance: OWL instance to validate

        Returns:
            List of OWLViolation objects
        """
        violations = []

        if instance is None or self._ontology is None:
            return violations

        # Run reasoner to infer violations
        self.run_reasoner()

        # Check if instance is classified as any violation type
        violation_classes = {
            "CavitationRisk": ("PHYSICAL_ERROR", "NPSH Cavitation",
                "Cavitation risk: NPSH available is less than NPSH required"),
            "CarnotViolation": ("PHYSICAL_ERROR", "Carnot Limit",
                "COP exceeds thermodynamic Carnot limit"),
            "EfficiencyViolation": ("PHYSICAL_ERROR", "Efficiency Limit",
                "Efficiency exceeds 100% (First Law of Thermodynamics)"),
            "LifespanExceeded": ("RANGE_ERROR", "Lifespan Exceeded",
                "Operating hours/cycles exceed maximum lifespan"),
            "NegativeValue": ("RANGE_ERROR", "Negative Value",
                "Value that must be non-negative is negative"),
        }

        try:
            instance_types = set(t.name for t in instance.is_a if hasattr(t, 'name'))

            for violation_class, (vtype, constraint, message) in violation_classes.items():
                if violation_class in instance_types:
                    violations.append(OWLViolation(
                        violation_type=vtype,
                        constraint_name=constraint,
                        message=message,
                    ))
        except Exception as e:
            logger.warning(f"Error checking instance types: {e}")

        return violations

    def validate_data(self, data: dict) -> list[OWLViolation]:
        """Validate data dictionary using OWL reasoning.

        This is the main entry point for OWL-based validation.

        Args:
            data: Dictionary with component data

        Returns:
            List of OWLViolation objects for any detected violations
        """
        violations = []

        if self._ontology is None:
            if not self.load():
                return violations

        # Create a temporary instance from data
        instance = self.create_instance_from_data(data)
        if instance is None:
            return violations

        # Validate using OWL reasoning
        violations = self.validate_instance(instance)

        # Additional programmatic checks for complex physics constraints
        # that can't be easily expressed in OWL/SWRL
        violations.extend(self._check_carnot_limit(data))
        violations.extend(self._check_pump_power_balance(data))
        violations.extend(self._check_compressor_thermodynamics(data))

        # Clean up the temporary instance
        try:
            from owlready2 import destroy_entity
            destroy_entity(instance)
        except Exception:
            pass

        return violations

    def _check_carnot_limit(self, data: dict) -> list[OWLViolation]:
        """Check heat pump COP against Carnot limit."""
        violations = []

        cop = data.get("cop") or data.get("leistungszahl")
        t_source = data.get("temperatur_quelle") or data.get("t_source") or data.get("quelltemperatur")
        t_sink = data.get("temperatur_vorlauf") or data.get("t_sink") or data.get("vorlauftemperatur")

        if cop is not None and t_source is not None and t_sink is not None:
            if t_sink > t_source:
                # Convert to Kelvin
                t_hot_k = t_sink + 273.15
                t_cold_k = t_source + 273.15

                # Carnot COP for heating
                cop_carnot = t_hot_k / (t_hot_k - t_cold_k)

                if cop > cop_carnot:
                    violations.append(OWLViolation(
                        violation_type="PHYSICAL_ERROR",
                        constraint_name="Carnot Limit (Second Law of Thermodynamics)",
                        message=f"COP ({cop}) exceeds Carnot limit ({cop_carnot:.2f}) for T_source={t_source}°C, T_sink={t_sink}°C",
                        property_name="cop",
                        actual_value=cop,
                        expected_value=f"<= {cop_carnot:.2f}",
                    ))

        return violations

    def _check_pump_power_balance(self, data: dict) -> list[OWLViolation]:
        """Check pump hydraulic power against input power."""
        violations = []

        p_in = data.get("leistungsaufnahme") or data.get("power_input")
        p_hyd = data.get("hydraulikleistung") or data.get("hydraulic_power")
        eta = data.get("wirkungsgrad") or data.get("efficiency")

        if p_in is not None and p_hyd is not None and p_in > 0:
            # Default efficiency if not given
            if eta is None:
                eta = 80
            if eta > 1:  # Convert percentage to fraction
                eta = eta / 100

            p_max = p_in * eta

            if p_hyd > p_max * 1.15:  # 15% tolerance
                violations.append(OWLViolation(
                    violation_type="PHYSICAL_ERROR",
                    constraint_name="Energy Conservation (Pump Power)",
                    message=f"Hydraulic power ({p_hyd:.1f} kW) exceeds possible output ({p_max:.1f} kW at η={eta*100:.0f}%)",
                    property_name="hydraulikleistung",
                    actual_value=p_hyd,
                    expected_value=f"<= {p_max:.1f} kW",
                ))

        return violations

    def _check_compressor_thermodynamics(self, data: dict) -> list[OWLViolation]:
        """Check compressor outlet temperature against isentropic compression."""
        violations = []

        t_in = data.get("temperatur_eingang") or data.get("t_inlet")
        t_out = data.get("temperatur_ausgang") or data.get("t_outlet")
        p_in = data.get("druck_eingang") or data.get("p_inlet")
        p_out = data.get("druck_ausgang") or data.get("p_outlet")

        if all(v is not None for v in [t_in, t_out, p_in, p_out]) and p_in > 0:
            # Convert to Kelvin
            t1_k = t_in + 273.15
            t2_k = t_out + 273.15

            # Pressure ratio
            pr = p_out / p_in

            # Isentropic temperature (γ = 1.4 for air)
            gamma = 1.4
            t2_isentropic_k = t1_k * (pr ** ((gamma - 1) / gamma))
            t2_isentropic_c = t2_isentropic_k - 273.15

            # Actual should be >= isentropic (with 5% tolerance)
            if t2_k < t2_isentropic_k * 0.95:
                violations.append(OWLViolation(
                    violation_type="PHYSICAL_ERROR",
                    constraint_name="Isentropic Compression (Second Law)",
                    message=f"Outlet temperature ({t_out}°C) is below isentropic value ({t2_isentropic_c:.1f}°C) - physically impossible",
                    property_name="temperatur_ausgang",
                    actual_value=t_out,
                    expected_value=f">= {t2_isentropic_c:.1f}°C",
                ))

        return violations

    def get_type_hierarchy_for_validation(self, type_name: str) -> list[str]:
        """Get the full type hierarchy for constraint applicability checking.

        Args:
            type_name: Component type name

        Returns:
            List of all types in hierarchy (most specific first)
        """
        if self._ontology is None:
            return [type_name]

        ancestors = self.get_all_ancestor_types(type_name)

        # Sort by specificity (type_name first, then parents, then Thing last)
        result = [type_name] if type_name in self._concepts else []

        # Add parents in order of specificity
        for ancestor in ancestors:
            if ancestor not in result and ancestor != "Thing":
                result.append(ancestor)

        return result


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


def reset_ontology_loader():
    """Reset the global ontology loader instance.

    Useful for testing or reloading the ontology.
    """
    global _loader
    _loader = None
