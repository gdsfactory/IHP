#!/usr/bin/env python3
"""
SPICE to pic.yml Converter - Functional Implementation

This module converts SPICE netlists to gdsfactory pic.yml format using
a functional approach with dictionaries instead of classes.

Features:
- Component type mapping (SPICE model -> PDK function)
- Parameter translation (SPICE param -> PDK param with type conversion)
- Automatic unit conversion (e.g., "60.0u" -> 60.0)
- Layout generation with organized placements
"""

import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

# ============================================================================
# CONVERSION FUNCTIONS
# ============================================================================

# SPICE letter suffixes and their SI multipliers
_SPICE_SUFFIX_MULTIPLIERS = {
    "f": 1e-15,  # femto
    "p": 1e-12,  # pico
    "n": 1e-9,  # nano
    "u": 1e-6,  # micro
    "m": 1e-3,  # milli
    "k": 1e3,  # kilo
    "M": 1e6,  # mega
    "G": 1e9,  # giga
}


def _parse_spice_number(value: str) -> float:
    """Parse a raw SPICE number, handling broken scientific notation and SI suffixes.

    SPICE uses letter suffixes as SI multipliers:
        2.006n -> 2.006e-9
        4.5e-6 -> 4.5e-6   (standard scientific notation, no suffix)
        60.0u  -> 60.0e-6   (suffix used instead of scientific notation)

    Args:
        value: The raw SPICE number as a string.
    Returns:
        The parsed number as a float, in SI units.
    """
    value = value.strip()

    # Handle scientific notation missing 'e': 4.50-6 -> 4.50e-6
    if re.search(r"[0-9]-[0-9]", value) and "e" not in value.lower():
        value = re.sub(r"([0-9])-", r"\1e-", value)
    if re.search(r"[0-9]\+[0-9]", value) and "e" not in value.lower():
        value = re.sub(r"([0-9])\+", r"\1e+", value)

    # Check for a trailing SI suffix (single letter, not part of 'e' notation)
    match = re.match(r"^([0-9.eE+-]+)([a-zA-Z])$", value)
    if match:
        number = float(match.group(1))
        suffix = match.group(2)
        multiplier = _SPICE_SUFFIX_MULTIPLIERS.get(suffix, 1.0)
        return number * multiplier

    return float(value)


def parse_dimension(value: str) -> float:
    """Parse a dimensional value (width, length, etc.) and convert meters to micrometers.

    SPICE uses meters for dimensions, gdsfactory uses micrometers by default, so we always multiply by 1e6.
    Rounds to 4 decimal places to avoid floating point noise (e.g. 59.9999 -> 60.0).

    Args:
        value: The raw SPICE dimension as a string (e.g., "2.006n").
    Returns:
        The parsed dimension as a float in micrometers (e.g., 2.006).
    """
    return round(_parse_spice_number(value) * 1e6, 4)


def parse_float(value: str) -> float:
    """Parse a non-space SI quantity (inductance, resistance, etc.).

    Keeps the value in SI units as-is (e.g., 2.006e-9 H stays 2.006e-9).

    Args:
        value: The raw SPICE number as a string (e.g., "2.006n").
    Returns:
        The parsed number as a float in SI units (e.g., 2.006e-9).
    """
    return _parse_spice_number(value)


def parse_int(value: str) -> int:
    """Parse integer.

    Args:
        value: The raw SPICE integer as a string (e.g., "4").

    Returns:
        The parsed integer as an int (e.g., 4).
    """
    return int(float(value))


def keep_string(value: str) -> str:
    """Keep as string."""
    return value.strip()


# ============================================================================
# PARAMETER MAPPING FUNCTIONS
# ============================================================================


def create_param_mapping(
    ihp_param_name: str,
    pdk_param_name: str,
    converter: Callable | None = None,
    default: Any = None,
) -> dict[str, Any]:
    """Create a parameter mapping dictionary.

    Args:
        ihp_param_name: The parameter name used in the SPICE netlist (e.g., "w").
        pdk_param_name: The corresponding parameter name used in the PDK (e.g., "width").
        converter: A function to convert the SPICE parameter value to the PDK format (e.g., parse_dimension). If None, the value will be kept as a string.
        default: An optional default value to use if the parameter is not specified in the SPICE netlist.

    Returns:
        A dictionary containing the mapping information for this parameter.
    """
    return {
        "ihp_param_name": ihp_param_name,
        "pdk_param_name": pdk_param_name,
        "converter": converter or keep_string,
        "default": default,
    }


def apply_param_mapping(mapping: dict[str, Any], value: str) -> Any:
    """Apply a parameter mapping to convert a value.

    Args:
        mapping: The parameter mapping dictionary created by create_param_mapping.
        value: The raw SPICE parameter value as a string.

    Returns:
        The converted parameter value, after applying the mapping's converter function.
    """
    converter = mapping["converter"]
    return converter(value)


def map_parameters(
    spice_params: dict[str, str], param_mappings: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Convert SPICE parameters to PDK parameters using mappings.

    Args:
        spice_params: A dictionary of parameters from the SPICE netlist (e.g., {"w": "2.006n", "l": "1.5u"}).
        param_mappings: A dictionary of parameter mappings created by create_param_mapping.

    Returns:
        A dictionary of converted parameters for the PDK (e.g., {"width": 2.006, "length": 1.5}).
    """
    pdk_params = {}

    for ihp_param_name, value in spice_params.items():
        if ihp_param_name in param_mappings:
            mapping = param_mappings[ihp_param_name]
            pdk_param_name = mapping["pdk_param_name"]
            pdk_params[pdk_param_name] = apply_param_mapping(mapping, value)

    # Add any missing defaults
    for _, mapping in param_mappings.items():
        pdk_param_name = mapping["pdk_param_name"]
        if pdk_param_name not in pdk_params and mapping["default"] is not None:
            pdk_params[pdk_param_name] = mapping["default"]

    return pdk_params


# ============================================================================
# COMPONENT MAPPING FUNCTIONS
# ============================================================================


def create_component_mapping(
    spice_model: str, pdk_component: str, param_mappings: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Create a component mapping dictionary.

    Args:
        spice_model: The model name used in the SPICE netlist (e.g., "sg13_lv_nmos").
        pdk_component: The corresponding component name used in the PDK (e.g., "nmos").
        param_mappings: A dictionary of parameter mappings for this component, created by create_param_mapping.

    Returns:
        A dictionary containing the mapping information for this component, including the SPICE model name, PDK component name, and parameter mappings.
    """
    return {
        "spice_model": spice_model,
        "pdk_component": pdk_component,
        "param_mappings": param_mappings,
    }


def get_default_ihp_mappings() -> dict[str, dict[str, Any]]:
    """Get default component mappings for IHP SG13G2 PDK."""

    mappings = {}

    # NMOS parameter mappings
    nmos_params = {
        "w": create_param_mapping("w", "width", parse_dimension),  # meters -> um
        "l": create_param_mapping("l", "length", parse_dimension),  # meters -> um
        "ng": create_param_mapping("ng", "nf", parse_int),
        "model": create_param_mapping(
            "model", "model", keep_string, default="sg13_lv_nmos"
        ),
    }

    # PMOS parameter mappings (same as NMOS)
    pmos_params = {
        "w": create_param_mapping("w", "width", parse_dimension),  # meters -> um
        "l": create_param_mapping("l", "length", parse_dimension),  # meters -> um
        "ng": create_param_mapping("ng", "nf", parse_int),
        "model": create_param_mapping(
            "model", "model", keep_string, default="sg13_lv_pmos"
        ),
    }

    # rppd resistor parameter mappings
    rppd_params = {
        "w": create_param_mapping(
            "w", "dx", parse_dimension
        ),  # meters -> um, width -> dx
        "l": create_param_mapping(
            "l", "dy", parse_dimension
        ),  # meters -> um, length -> dy
        "model": create_param_mapping("model", "model", keep_string, default="rppd"),
    }

    # MIM capacitor parameter mappings
    cmim_params = {
        "w": create_param_mapping("w", "width", parse_dimension),  # meters -> um
        "l": create_param_mapping("l", "length", parse_dimension),  # meters -> um
        # "model": create_param_mapping("model", "model", keep_string, default="cmim"),
    }

    # Inductor parameter mappings
    inductor_params = {
        "inductance": create_param_mapping(
            "inductance", "inductance", parse_float
        ),  # SI, keep as-is
    }

    # Register all component mappings
    mappings["sg13_lv_nmos"] = create_component_mapping(
        "sg13_lv_nmos", "nmos", nmos_params
    )
    mappings["sg13_lv_pmos"] = create_component_mapping(
        "sg13_lv_pmos", "pmos", pmos_params
    )
    mappings["sg13_hv_nmos"] = create_component_mapping(
        "sg13_hv_nmos", "nmos", nmos_params.copy()
    )
    mappings["sg13_hv_pmos"] = create_component_mapping(
        "sg13_hv_pmos", "pmos", pmos_params.copy()
    )
    mappings["rppd"] = create_component_mapping("rppd", "rppd", rppd_params)
    mappings["cap_cmim"] = create_component_mapping("cap_cmim", "cmim", cmim_params)
    mappings["inductor"] = create_component_mapping(
        "inductor", "inductor2", inductor_params
    )

    return mappings


# ============================================================================
# SPICE PARSING FUNCTIONS
# ============================================================================


def parse_instance_line(
    line: str, component_mappings: dict[str, dict[str, Any]]
) -> dict[str, Any] | None:
    """Parse a single SPICE instance line.

    Args:
        line: The raw line from the SPICE netlist representing an instance (e.g., "X1 in out vdd sg13_lv_nmos w=2.006n l=1.5u ng=4").
        component_mappings: The dictionary of component mappings to identify the model.
    Returns:
        A dictionary containing the instance information (name, nodes, model, parameters) or None if the line cannot be parsed as an instance.
    """
    parts = line.split()
    if len(parts) < 2:
        return None

    instance = {"name": parts[0], "nodes": [], "model": None, "parameters": {}}

    first_char = parts[0][0].upper()

    if first_char == "X":
        # Subcircuit instance: X<n> <nodes> <model> <params>
        model_idx = None
        for i in range(1, len(parts)):
            part = parts[i]
            if "=" not in part and any(c.isalpha() for c in part):
                if any(model in part for model in component_mappings.keys()):
                    model_idx = i
                    instance["model"] = part
                    break

        if model_idx:
            instance["nodes"] = parts[1:model_idx]
            for param_str in parts[model_idx + 1 :]:
                if "=" in param_str:
                    key, val = param_str.split("=", 1)
                    instance["parameters"][key] = val

    elif first_char == "L":
        # Inductor: L<n> <node1> <node2> <value>
        instance["model"] = "inductor"
        if len(parts) >= 3:
            instance["nodes"] = parts[1:3]
            if len(parts) > 3:
                instance["parameters"]["inductance"] = parts[3]

    elif first_char in ["R", "C"]:
        instance["model"] = "resistor" if first_char == "R" else "capacitor"
        if len(parts) >= 3:
            instance["nodes"] = parts[1:3]
            if len(parts) > 3:
                instance["parameters"]["value"] = parts[3]

    return instance


def parse_spice_netlist(
    spice_file: Path, component_mappings: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Parse SPICE netlist file.

    Args:
        spice_file: Path to the SPICE netlist file.
        component_mappings: The dictionary of component mappings to identify models and parameters.
    Returns:
        A dictionary containing the parsed netlist information (name, ports, instances, nets).
    """
    with open(spice_file) as f:
        lines = f.readlines()

    # Ignore ports for now
    # netlist = {"name": None, "ports": [], "instances": {}, "nets": set()}
    netlist = {"name": None, "instances": {}, "nets": set()}

    for line in lines:
        line = line.strip()

        if not line or line.startswith("**"):
            continue

        # Parse subcircuit definition
        if line.startswith(".subckt"):
            parts = line.split()
            netlist["name"] = parts[1] if len(parts) > 1 else "circuit"
            # netlist["ports"] = parts[2:] if len(parts) > 2 else []
            continue

        # Ignore ports for now
        # # Parse ports from commented iopin lines
        # if line.startswith("*.iopin"):
        #     parts = line.split()
        #     if len(parts) > 1:
        #         port_name = parts[1]
        #         if port_name not in netlist["ports"]:
        #             netlist["ports"].append(port_name)
        #     continue

        # End of subcircuit or other directives
        if line.startswith("."):
            continue

        # Skip comments
        if line.startswith("*"):
            continue

        # Parse instance lines
        first_char = line[0].upper()
        if first_char in ["X", "M", "R", "C", "L", "Q"]:
            instance = parse_instance_line(line, component_mappings)
            if instance:
                netlist["instances"][instance["name"]] = instance
                netlist["nets"].update(instance.get("nodes", []))

    netlist["nets"] = list(netlist["nets"])

    return netlist


# ============================================================================
# PIC.YML GENERATION FUNCTIONS
# ============================================================================


def convert_to_picyml(
    netlist: dict[str, Any],
    component_mappings: dict[str, dict[str, Any]],
    layout_spacing: float = 100.0,
    components_per_row: int = 5,
) -> dict[str, Any]:
    """Convert parsed netlist to pic.yml structure.

    Args:
        netlist: The parsed netlist dictionary containing name, ports, instances, and nets.
        component_mappings: The dictionary of component mappings to convert SPICE models and parameters to PDK components and parameters.
        layout_spacing: The spacing in micrometers between components in the generated layout.
        components_per_row: The number of components to place in each row of the layout grid

    Returns:
        A dictionary representing the pic.yml structure with instances, placements, and ports.
    """

    pic = {
        "name": netlist["name"] or "circuit",
        "instances": {},
        "placements": {},
        # "ports": {},
    }

    # Convert instances
    for inst_name, inst_data in netlist["instances"].items():
        model = inst_data["model"]

        # Check if we have a mapping for this model
        if model not in component_mappings:
            print(f"Warning: No mapping for model '{model}', skipping {inst_name}")
            continue

        mapping = component_mappings[model]

        # Add model to parameters if not already there
        spice_params = inst_data["parameters"].copy()
        if "model" not in spice_params and model:
            spice_params["model"] = model

        # Convert parameters
        pdk_params = map_parameters(spice_params, mapping["param_mappings"])

        # Create instance entry
        pic["instances"][inst_name] = {
            "component": mapping["pdk_component"],
            "settings": pdk_params,
        }

    # Generate grid layout
    x, y = 0.0, 0.0
    for i, inst_name in enumerate(pic["instances"].keys()):
        pic["placements"][inst_name] = {"x": x, "y": y}

        x += layout_spacing
        if (i + 1) % components_per_row == 0:
            x = 0.0
            y += layout_spacing

    # # Add ports
    # for port_name in netlist["ports"]:
    #     pic["ports"][port_name] = f"{port_name},e1"

    return pic


# ============================================================================
# FILE I/O FUNCTIONS
# ============================================================================


def convert_file(
    spice_file: Path,
    output_file: Path,
    component_mappings: dict[str, dict[str, Any]] | None = None,
    layout_spacing: float = 100.0,
    components_per_row: int = 5,
):
    """Convert SPICE file to pic.yml file.

    Args:
        spice_file: Path to the input SPICE netlist file.
        output_file: Path to the output pic.yml file.
        component_mappings: Optional dictionary of component mappings. If None, default IHP mappings will be used.
        layout_spacing: The spacing in micrometers between components in the generated layout (default: 100).
        components_per_row: The number of components to place in each row of the layout grid (default: 5).

    Returns:
        None. Writes the converted pic.yml to the specified output file.
    """

    # Use default mappings if none provided
    if component_mappings is None:
        component_mappings = get_default_ihp_mappings()

    print(f"Parsing SPICE netlist: {spice_file}")
    netlist = parse_spice_netlist(spice_file, component_mappings)

    print(f"Found {len(netlist['instances'])} instances")
    # print(f"Found {len(netlist['ports'])} ports")

    print("Converting to pic.yml format...")
    pic = convert_to_picyml(
        netlist, component_mappings, layout_spacing, components_per_row
    )

    print(f"Writing to {output_file}")
    with open(output_file, "w") as f:
        yaml.dump(pic, f, default_flow_style=False, sort_keys=False, indent=2)

    print("✓ Conversion complete!")
    print("\nSummary:")
    print(f"  - {len(pic['instances'])} components")
    # print(f"  - {len(pic['ports'])} ports")
    print(f"  - {len(pic['placements'])} placements")


def add_component_mapping(
    component_mappings: dict[str, dict[str, Any]],
    spice_model: str,
    pdk_component: str,
    param_mappings: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Add a custom component mapping to the mappings dictionary."""
    mapping = create_component_mapping(spice_model, pdk_component, param_mappings)
    component_mappings[spice_model] = mapping
    return component_mappings


# ============================================================================
# MAIN / CLI
# ============================================================================


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert SPICE netlists to gdsfactory pic.yml format"
    )
    parser.add_argument("input", type=Path, help="Input SPICE netlist file")
    parser.add_argument("output", type=Path, help="Output pic.yml file")
    parser.add_argument(
        "--spacing",
        type=float,
        default=100.0,
        help="Component spacing in micrometers (default: 100)",
    )
    parser.add_argument(
        "--per-row",
        type=int,
        default=5,
        help="Components per row in grid layout (default: 5)",
    )

    args = parser.parse_args()

    # Convert file with default mappings
    convert_file(
        args.input,
        args.output,
        layout_spacing=args.spacing,
        components_per_row=args.per_row,
    )


if __name__ == "__main__":
    main()
