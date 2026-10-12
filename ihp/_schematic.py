"""Schematic model references, independent of optional simulator runtimes."""

from typing import Any

BONDPAD_SHAPES = {"octagon": 0, "square": 1, "circle": 2}

# Native NgSpice wrapper nodes retain their declared case. These aliases differ
# from the converted VACASK wrappers, whose nodes are lowercase.
_NATIVE_UPPERCASE_PORTS = {
    "cmim": {"PLUS", "MINUS"},
    "rfcmim": {"PLUS", "MINUS"},
    "svaricap": {"G1", "W", "G2"},
    "esd_nmos": {"VDD", "VSS"},
    "bondpad": {"PAD"},
}


def native_port_map(qualname: str, port_order: list[str]) -> dict[str, str]:
    """Map schematic symbols to the actual native NgSpice terminals.

    @tags circulax-simulation
    """
    uppercase = _NATIVE_UPPERCASE_PORTS.get(qualname, set())
    return {
        port: port
        if port in uppercase
        else port[1:]
        if port in ("P1", "P2")
        else port.lower()
        for port in port_order
    }


def circulax_model(
    name: str,
    module: str,
    port_order: list[str],
    qualname: str | None = None,
    params: dict[str, str] | None = None,
    port_map: dict[str, str] | None = None,
    defaults: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Reference a shared Circulax object using the Intel PDK contract.

    @tags circulax-simulation
    """
    entry: dict[str, Any] = {
        "language": "circulax",
        "implementation": "Circulax",
        "name": name,
        "module": module,
        "qualname": qualname or name,
        "port_order": list(port_order),
        "params": dict(params or {}),
    }
    if port_map is not None:
        entry["port_map"] = dict(port_map)
    if defaults is not None:
        entry["defaults"] = dict(defaults)
    return entry


def with_circulax_models(
    models: list[dict[str, Any]], *, qualname: str
) -> list[dict[str, Any]]:
    """Keep native registrations and add a shared parameterized library model.

    Parameter expressions and corner cards belong to the referenced LibraryModel,
    so GF+ forwards schematic settings without evaluating native library equations.
    Its public ports match the symbol; native terminal aliases stay inside it.
    @tags circulax-simulation
    """
    result = list(models)
    for model in models:
        if model.get("implementation") == "VACASK":
            result.append(
                circulax_model(
                    model["name"],
                    "ihp.models.circulax",
                    model["port_order"],
                    qualname=qualname,
                )
            )
    return result
