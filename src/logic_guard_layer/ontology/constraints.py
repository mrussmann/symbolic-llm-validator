"""Constraint definitions for ontology validation."""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from logic_guard_layer.models.responses import Violation, ViolationType

logger = logging.getLogger(__name__)


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
    hours = data.get("operating_hours") or data.get("betriebsstunden")
    logger.debug(f"Checking operating hours: {hours}")
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
    lifespan = data.get("max_lifespan") or data.get("max_lebensdauer")
    logger.debug(f"Checking max lifespan: {lifespan}")
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
    interval = data.get("maintenance_interval") or data.get("wartungsintervall")
    logger.debug(f"Checking maintenance interval: {interval}")
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
    interval = data.get("maintenance_interval") or data.get("wartungsintervall")
    lifespan = data.get("max_lifespan") or data.get("max_lebensdauer")
    logger.debug(f"Checking interval ({interval}) vs lifespan ({lifespan})")

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
    hours = data.get("operating_hours") or data.get("betriebsstunden")
    lifespan = data.get("max_lifespan") or data.get("max_lebensdauer")
    logger.info(f"Checking operating hours ({hours}) vs lifespan ({lifespan})")

    if hours is not None and lifespan is not None and hours > lifespan:
        logger.info(f"VIOLATION: hours {hours} > lifespan {lifespan}")
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
    pressure = data.get("pressure_bar") or data.get("druck_bar") or data.get("druck")
    logger.info(f"Checking pressure: {pressure}")

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
            logger.info(f"VIOLATION: pressure {pressure} > 350")
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
    temp = data.get("temperature_c") or data.get("temperatur_c") or data.get("temperatur")
    logger.info(f"Checking temperature: {temp}")

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
            logger.info(f"VIOLATION: temperature {temp} > 150")
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


# =============================================================================
# PHYSICS-BASED CONSTRAINTS (Thermodynamics, Fluid Mechanics)
# =============================================================================


def check_efficiency_physical_limit(data: dict) -> Optional[Violation]:
    """Check that efficiency/Wirkungsgrad does not exceed 100% (1.0).

    Based on: First Law of Thermodynamics - Energy cannot be created.
    """
    # Check various efficiency field names
    efficiency = (
        data.get("wirkungsgrad") or
        data.get("efficiency") or
        data.get("isentroper_wirkungsgrad") or
        data.get("eta")
    )

    if efficiency is not None:
        # Handle both percentage (0-100) and fraction (0-1) formats
        eff_value = efficiency if efficiency <= 1 else efficiency / 100

        if eff_value < 0:
            return Violation(
                type=ViolationType.PHYSICAL_ERROR,
                constraint="0 <= η <= 1 (First Law of Thermodynamics)",
                message=f"Efficiency cannot be negative: {efficiency}",
                property_name="wirkungsgrad",
                actual_value=efficiency,
                expected_value=">= 0",
            )
        if eff_value > 1:
            return Violation(
                type=ViolationType.PHYSICAL_ERROR,
                constraint="η <= 1 (First Law of Thermodynamics)",
                message=f"Efficiency ({efficiency}%) exceeds 100% - violates energy conservation",
                property_name="wirkungsgrad",
                actual_value=efficiency,
                expected_value="<= 100%",
            )
    return None


def check_npsh_cavitation(data: dict) -> Optional[Violation]:
    """Check NPSH (Net Positive Suction Head) to prevent cavitation.

    Based on: Fluid mechanics - Cavitation occurs when local pressure drops below vapor pressure.
    NPSH_available must be greater than NPSH_required for safe pump operation.
    """
    npsh_available = (
        data.get("npsh_verfügbar") or
        data.get("npsh_verfuegbar") or
        data.get("npsh_available") or
        data.get("npsha")
    )
    npsh_required = (
        data.get("npsh_erforderlich") or
        data.get("npsh_required") or
        data.get("npshr")
    )

    if npsh_available is not None and npsh_required is not None:
        if npsh_available < npsh_required:
            margin = npsh_required - npsh_available
            return Violation(
                type=ViolationType.PHYSICAL_ERROR,
                constraint="NPSH_available > NPSH_required (Cavitation Prevention)",
                message=f"Cavitation risk: NPSH available ({npsh_available} m) < NPSH required ({npsh_required} m). Deficit: {margin:.1f} m",
                property_name="npsh_verfügbar",
                actual_value=npsh_available,
                expected_value=f"> {npsh_required} m",
            )
    return None


def check_heat_exchanger_energy_balance(data: dict) -> Optional[Violation]:
    """Check energy balance in heat exchangers.

    Based on: First Law of Thermodynamics - Q_hot = Q_cold (steady state, no losses)
    Q = ṁ × cp × ΔT
    """
    # Hot side
    t_hot_in = data.get("temperatur_heiss_ein") or data.get("t_hot_in")
    t_hot_out = data.get("temperatur_heiss_aus") or data.get("t_hot_out")
    m_hot = data.get("massenstrom_heiss") or data.get("m_dot_hot")
    cp_hot = data.get("cp_heiss") or data.get("cp_hot") or 4.18  # Default water

    # Cold side
    t_cold_in = data.get("temperatur_kalt_ein") or data.get("t_cold_in")
    t_cold_out = data.get("temperatur_kalt_aus") or data.get("t_cold_out")
    m_cold = data.get("massenstrom_kalt") or data.get("m_dot_cold")
    cp_cold = data.get("cp_kalt") or data.get("cp_cold") or 4.18  # Default water

    if all(v is not None for v in [t_hot_in, t_hot_out, t_cold_in, t_cold_out, m_hot, m_cold]):
        # Calculate heat transfer (kW)
        # Q = m * cp * ΔT, where m is in kg/h, cp in kJ/kgK, ΔT in K
        q_hot = abs(m_hot * cp_hot * (t_hot_in - t_hot_out)) / 3600  # Convert to kW
        q_cold = abs(m_cold * cp_cold * (t_cold_out - t_cold_in)) / 3600

        # Check temperature crossover (physically impossible)
        if t_cold_out > t_hot_in:
            return Violation(
                type=ViolationType.PHYSICAL_ERROR,
                constraint="T_cold_out <= T_hot_in (Second Law of Thermodynamics)",
                message=f"Temperature crossover: Cold outlet ({t_cold_out}°C) cannot exceed hot inlet ({t_hot_in}°C)",
                property_name="temperatur_kalt_aus",
                actual_value=t_cold_out,
                expected_value=f"<= {t_hot_in}°C",
            )

        # Check energy balance (allow 20% tolerance for losses)
        if q_hot > 0 and q_cold > 0:
            imbalance = abs(q_hot - q_cold) / max(q_hot, q_cold)
            if imbalance > 0.20:  # 20% tolerance
                return Violation(
                    type=ViolationType.PHYSICAL_ERROR,
                    constraint="Q_hot ≈ Q_cold (Energy Conservation)",
                    message=f"Energy imbalance: Q_hot={q_hot:.1f} kW, Q_cold={q_cold:.1f} kW (difference: {imbalance*100:.1f}%)",
                    property_name="wärmeleistung",
                    actual_value=f"Q_hot={q_hot:.1f}, Q_cold={q_cold:.1f}",
                    expected_value="Q_hot ≈ Q_cold (±20%)",
                )
    return None


def check_compressor_temperature_rise(data: dict) -> Optional[Violation]:
    """Check compressor outlet temperature against isentropic compression.

    Based on: Thermodynamics of isentropic compression
    T2/T1 = (P2/P1)^((γ-1)/γ) for ideal gas
    Actual temperature should be higher than isentropic (due to inefficiency).
    """
    t_in = data.get("temperatur_eingang") or data.get("t_inlet")
    t_out = data.get("temperatur_ausgang") or data.get("t_outlet")
    p_in = data.get("druck_eingang") or data.get("p_inlet")
    p_out = data.get("druck_ausgang") or data.get("p_outlet")

    if all(v is not None for v in [t_in, t_out, p_in, p_out]) and p_in > 0:
        # Convert to absolute temperature (Kelvin)
        t1_k = t_in + 273.15
        t2_k = t_out + 273.15

        # Pressure ratio
        pr = p_out / p_in

        # Isentropic temperature (assuming γ = 1.4 for air)
        gamma = 1.4
        t2_isentropic_k = t1_k * (pr ** ((gamma - 1) / gamma))
        t2_isentropic_c = t2_isentropic_k - 273.15

        # Actual temperature should be >= isentropic (efficiency < 100%)
        # If actual is less than isentropic, something is wrong
        if t2_k < t2_isentropic_k * 0.95:  # 5% tolerance
            return Violation(
                type=ViolationType.PHYSICAL_ERROR,
                constraint="T_actual >= T_isentropic (Second Law)",
                message=f"Outlet temperature ({t_out}°C) is below isentropic value ({t2_isentropic_c:.1f}°C) - physically impossible",
                property_name="temperatur_ausgang",
                actual_value=t_out,
                expected_value=f">= {t2_isentropic_c:.1f}°C",
            )

        # Check for extremely high temperature (potential safety issue)
        max_reasonable_temp = t2_isentropic_c * 1.5  # 50% above isentropic
        if t_out > max_reasonable_temp and t_out > 300:
            return Violation(
                type=ViolationType.RANGE_ERROR,
                constraint="T_outlet reasonable for compression ratio",
                message=f"Outlet temperature ({t_out}°C) unusually high for pressure ratio {pr:.1f}",
                property_name="temperatur_ausgang",
                actual_value=t_out,
                expected_value=f"~{t2_isentropic_c:.0f}-{max_reasonable_temp:.0f}°C",
            )
    return None


def check_pump_power_balance(data: dict) -> Optional[Violation]:
    """Check pump hydraulic power against input power.

    Based on: P_hydraulic = ρ × g × Q × H
    P_hydraulic must be <= P_input × η
    """
    # Get values with German/English key names
    rho = data.get("dichte_medium") or data.get("density") or 1000  # Default water kg/m³
    q = data.get("volumenstrom") or data.get("flow_rate")  # m³/h
    h = data.get("förderhöhe") or data.get("foerderhoehe") or data.get("head")  # m
    p_in = data.get("leistungsaufnahme") or data.get("power_input")  # kW
    eta = data.get("wirkungsgrad") or data.get("efficiency")  # fraction or %

    if all(v is not None for v in [q, h, p_in]) and p_in > 0:
        # Convert flow rate to m³/s
        q_si = q / 3600
        g = 9.81

        # Hydraulic power in kW
        p_hyd = (rho * g * q_si * h) / 1000

        # If efficiency not given, assume 80%
        if eta is None:
            eta = 0.80
        elif eta > 1:  # If given as percentage
            eta = eta / 100

        # Maximum possible hydraulic power
        p_max = p_in * eta

        # Allow 15% tolerance for measurement uncertainty
        if p_hyd > p_max * 1.15:
            return Violation(
                type=ViolationType.PHYSICAL_ERROR,
                constraint="P_hydraulic <= P_input × η (Energy Conservation)",
                message=f"Hydraulic power ({p_hyd:.1f} kW) exceeds possible output ({p_max:.1f} kW at η={eta*100:.0f}%)",
                property_name="leistungsaufnahme",
                actual_value=f"P_hyd={p_hyd:.1f} kW",
                expected_value=f"<= {p_max:.1f} kW",
            )
    return None


def check_battery_soc_range(data: dict) -> Optional[Violation]:
    """Check battery State of Charge is within valid range.

    SOC must be between 0% and 100%.
    """
    soc = data.get("ladezustand_soc") or data.get("soc") or data.get("state_of_charge")

    if soc is not None:
        if soc < 0:
            return Violation(
                type=ViolationType.PHYSICAL_ERROR,
                constraint="0% <= SOC <= 100%",
                message=f"State of Charge cannot be negative: {soc}%",
                property_name="ladezustand_soc",
                actual_value=soc,
                expected_value=">= 0%",
            )
        if soc > 100:
            return Violation(
                type=ViolationType.PHYSICAL_ERROR,
                constraint="0% <= SOC <= 100%",
                message=f"State of Charge cannot exceed 100%: {soc}%",
                property_name="ladezustand_soc",
                actual_value=soc,
                expected_value="<= 100%",
            )
    return None


def check_battery_cycles_vs_max(data: dict) -> Optional[Violation]:
    """Check battery charge cycles against maximum rated cycles."""
    cycles = data.get("ladezyklen") or data.get("charge_cycles")
    max_cycles = data.get("maximale_ladezyklen") or data.get("max_cycles")

    if cycles is not None and max_cycles is not None:
        if cycles > max_cycles:
            pct_over = ((cycles - max_cycles) / max_cycles) * 100
            return Violation(
                type=ViolationType.RELATIONAL_ERROR,
                constraint="charge_cycles <= max_cycles",
                message=f"Battery cycles ({cycles}) exceed maximum rated cycles ({max_cycles}) by {pct_over:.1f}%",
                property_name="ladezyklen",
                actual_value=cycles,
                expected_value=f"<= {max_cycles}",
            )
    return None


def check_cop_physical_limit(data: dict) -> Optional[Violation]:
    """Check heat pump COP against Carnot limit.

    Based on: COP_Carnot = T_hot / (T_hot - T_cold) for heating
    Actual COP must be less than Carnot COP.
    """
    cop = data.get("cop") or data.get("leistungszahl")
    t_source = data.get("temperatur_quelle") or data.get("t_source")  # Cold side (e.g., ground, air)
    t_sink = data.get("temperatur_vorlauf") or data.get("t_sink")  # Hot side (heating water)

    if cop is not None:
        # Basic sanity check
        if cop <= 0:
            return Violation(
                type=ViolationType.PHYSICAL_ERROR,
                constraint="COP > 0",
                message=f"COP must be positive: {cop}",
                property_name="cop",
                actual_value=cop,
                expected_value="> 0",
            )

        # If we have temperatures, check against Carnot limit
        if t_source is not None and t_sink is not None and t_sink > t_source:
            # Convert to Kelvin
            t_hot_k = t_sink + 273.15
            t_cold_k = t_source + 273.15

            # Carnot COP for heating
            cop_carnot = t_hot_k / (t_hot_k - t_cold_k)

            if cop > cop_carnot:
                return Violation(
                    type=ViolationType.PHYSICAL_ERROR,
                    constraint="COP <= COP_Carnot (Second Law of Thermodynamics)",
                    message=f"COP ({cop}) exceeds Carnot limit ({cop_carnot:.2f}) for T_source={t_source}°C, T_sink={t_sink}°C",
                    property_name="cop",
                    actual_value=cop,
                    expected_value=f"<= {cop_carnot:.2f}",
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
    # === PHYSICS-BASED CONSTRAINTS ===
    Constraint(
        id="C9",
        name="Efficiency physical limit",
        type=ConstraintType.PHYSICAL,
        description="Efficiency cannot exceed 100% (First Law of Thermodynamics)",
        expression="0 <= η <= 1",
        check_fn=check_efficiency_physical_limit,
        applicable_types=["Component", "Motor", "Pump", "Compressor", "Turbine", "HeatExchanger"],
    ),
    Constraint(
        id="C10",
        name="NPSH cavitation prevention",
        type=ConstraintType.PHYSICAL,
        description="NPSH available must exceed NPSH required to prevent cavitation",
        expression="NPSH_available > NPSH_required",
        check_fn=check_npsh_cavitation,
        applicable_types=["Pump", "Kreiselpumpe", "CentrifugalPump"],
    ),
    Constraint(
        id="C11",
        name="Heat exchanger energy balance",
        type=ConstraintType.PHYSICAL,
        description="Heat transfer must satisfy energy conservation (Q_hot ≈ Q_cold)",
        expression="Q_hot = Q_cold ± tolerance",
        check_fn=check_heat_exchanger_energy_balance,
        applicable_types=["HeatExchanger", "Wärmetauscher", "Kondensator", "Verdampfer"],
    ),
    Constraint(
        id="C12",
        name="Compressor isentropic temperature",
        type=ConstraintType.PHYSICAL,
        description="Compressor outlet temperature must be consistent with thermodynamics",
        expression="T_out >= T_isentropic",
        check_fn=check_compressor_temperature_rise,
        applicable_types=["Compressor", "Kompressor", "Verdichter"],
    ),
    Constraint(
        id="C13",
        name="Pump power balance",
        type=ConstraintType.PHYSICAL,
        description="Hydraulic power cannot exceed input power times efficiency",
        expression="P_hydraulic <= P_input × η",
        check_fn=check_pump_power_balance,
        applicable_types=["Pump", "Kreiselpumpe", "HydraulicPump"],
    ),
    Constraint(
        id="C14",
        name="Battery SOC range",
        type=ConstraintType.PHYSICAL,
        description="Battery State of Charge must be between 0% and 100%",
        expression="0% <= SOC <= 100%",
        check_fn=check_battery_soc_range,
        applicable_types=["Battery", "Batteriespeicher", "Akkumulator"],
    ),
    Constraint(
        id="C15",
        name="Battery cycle limit",
        type=ConstraintType.RELATIONAL,
        description="Battery charge cycles cannot exceed maximum rated cycles",
        expression="charge_cycles <= max_cycles",
        check_fn=check_battery_cycles_vs_max,
        applicable_types=["Battery", "Batteriespeicher", "Akkumulator"],
    ),
    Constraint(
        id="C16",
        name="Heat pump COP Carnot limit",
        type=ConstraintType.PHYSICAL,
        description="Heat pump COP cannot exceed Carnot limit (Second Law of Thermodynamics)",
        expression="COP <= COP_Carnot = T_hot/(T_hot-T_cold)",
        check_fn=check_cop_physical_limit,
        applicable_types=["HeatPump", "Wärmepumpe"],
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
