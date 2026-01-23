import vlsir
import vlsir.circuit_pb2 as vckt

# Mapping from string names to proto enum values
_SPICE_TYPE_MAP: dict[str, int] = {
    "SUBCKT": vckt.SpiceType.SUBCKT,
    "RESISTOR": vckt.SpiceType.RESISTOR,
    "CAPACITOR": vckt.SpiceType.CAPACITOR,
    "INDUCTOR": vckt.SpiceType.INDUCTOR,
    "MOS": vckt.SpiceType.MOS,
    "DIODE": vckt.SpiceType.DIODE,
    "BIPOLAR": vckt.SpiceType.BIPOLAR,
    "VSOURCE": vckt.SpiceType.VSOURCE,
    "ISOURCE": vckt.SpiceType.ISOURCE,
    "VCVS": vckt.SpiceType.VCVS,
    "VCCS": vckt.SpiceType.VCCS,
    "CCCS": vckt.SpiceType.CCCS,
    "CCVS": vckt.SpiceType.CCVS,
    "TLINE": vckt.SpiceType.TLINE,
}


def _spice_type_to_proto(spice_type: str | int) -> int:
    """Convert string or int spice_type to proto enum value."""
    if isinstance(spice_type, int):
        return spice_type
    return _SPICE_TYPE_MAP.get(spice_type.upper(), vckt.SpiceType.SUBCKT)


def expand_netlist(netlist: dict) -> dict:
    """Expand a simple netlist by looking up vlsir info from active PDK.

    Args:
        netlist: Dict with 'instances' (component names) and 'nets'

    Returns:
        Expanded netlist with vlsir info for each instance
    """
    import gdsfactory as gf

    pdk = gf.get_active_pdk()

    expanded = {"instances": {}, "nets": netlist.get("nets", [])}
    for inst_name, inst_data in netlist["instances"].items():
        comp_name = inst_data["component"]
        comp_func = pdk.cells[comp_name]
        comp = comp_func()  # instantiate to get info
        expanded["instances"][inst_name] = {"info": {"vlsir": comp.info["vlsir"]}}
    return expanded


def netlist_to_vlsir(
    netlist: dict, top_name: str, domain: str = "ihp"
) -> tuple[vckt.Package, list[str]]:
    """Convert a gdsfactory netlist dict to a VLSIR Package.

    Args:
        netlist: The netlist dictionary (single module, not recursive)
        top_name: Name for the top-level module
        domain: VLSIR domain name (default: "ihp")

    Returns:
        Tuple of (vckt.Package, list of required SPICE libraries)
    """
    yaml_schematic = netlist

    # Parse instances into VLSIR devices
    device_instances = []
    lib_set = set()
    for k, v in yaml_schematic["instances"].items():
        if "vlsir" in v["info"].keys():
            device_instances.append(k)
            lib_set.add(v["info"]["vlsir"]["spice_lib"])

    # Build graph of all connections (port-to-port)
    # Each node in graph is "instance,port"
    from collections import defaultdict

    connection_graph = defaultdict(set)

    for net in yaml_schematic.get("nets", []):
        p1 = net["p1"]
        p2 = net["p2"]
        connection_graph[p1].add(p2)
        connection_graph[p2].add(p1)

    # BFS to find connected components → electrical nodes
    all_ports = set(connection_graph.keys())
    visited = set()
    port_to_node = {}
    node_id = 0

    for start in all_ports:
        if start in visited:
            continue
        queue = [start]
        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)
            port_to_node[curr] = f"net_{node_id}"
            queue.extend(connection_graph[curr] - visited)
        node_id += 1

    # Map device ports to nodes
    device_port_nodes = {d: {} for d in device_instances}

    for port_key, node_name in port_to_node.items():
        comp, port = port_key.split(",")
        if comp in device_port_nodes:
            device_port_nodes[comp][port] = node_name

    # Now construct vckt.Package
    package = vckt.Package(domain=domain)

    # Collect unique ExternalModules by model name
    ext_modules = {}
    for inst_name in device_instances:
        info = yaml_schematic["instances"][inst_name]["info"]["vlsir"]
        model = info["model"]

        if model not in ext_modules:
            qname = vlsir.utils.QualifiedName(name=model, domain=domain)
            spice_type = _spice_type_to_proto(info.get("spice_type", "SUBCKT"))
            ext_mod = vckt.ExternalModule(name=qname, spicetype=spice_type)

            for port_name in info["port_order"]:
                ext_mod.signals.append(vckt.Signal(name=port_name, width=1))
                ext_mod.ports.append(
                    vckt.Port(
                        signal=port_name,
                        direction=vckt.Port.Direction.INOUT,  # codespell:ignore-line
                    )
                )

            # Add parameters to ExternalModule definition
            for key, val in info.get("params", {}).items():
                param = vlsir.Param(name=key)
                if isinstance(val, float):
                    param.value.double_value = val
                elif isinstance(val, int):
                    param.value.int64_value = val
                else:
                    param.value.literal = str(val)
                ext_mod.parameters.append(param)

            ext_modules[model] = ext_mod

    package.ext_modules.extend(ext_modules.values())

    # Build top module
    top_module = vckt.Module(name=top_name)

    # Add signals for each electrical node
    node_set = set()
    for ports in device_port_nodes.values():
        node_set.update(ports.values())

    for node_name in sorted(node_set):
        top_module.signals.append(vckt.Signal(name=node_name, width=1))

    # Create instances with connections
    for inst_name in device_instances:
        info = yaml_schematic["instances"][inst_name]["info"]["vlsir"]
        port_map = info.get("port_map", {})

        inst = vckt.Instance(name=inst_name)
        inst.module.external.CopyFrom(
            vlsir.utils.QualifiedName(name=info["model"], domain=domain)
        )

        # Add parameters
        for key, val in info.get("params", {}).items():
            param = vlsir.Param(name=key)
            if isinstance(val, float):
                param.value.double_value = val
            elif isinstance(val, int):
                param.value.int64_value = val
            else:
                param.value.literal = str(val)
            inst.parameters.append(param)

        # Add connections: map GDS port -> VLSIR port -> node
        for gds_port, node in device_port_nodes[inst_name].items():
            vlsir_port = port_map.get(gds_port, gds_port).lower()
            inst.connections.append(
                vckt.Connection(
                    portname=vlsir_port, target=vckt.ConnectionTarget(sig=node)
                )
            )

        top_module.instances.append(inst)

    package.modules.append(top_module)

    return package, list(lib_set)


if __name__ == "__main__":
    import yaml

    from ihp import PDK

    PDK.activate()

    netlist = yaml.safe_load("""
instances:
  M1:
    component: nmos
  M2:
    component: nmos

nets:
  - p1: M1,D
    p2: M2,D
  - p1: M1,S
    p2: M2,S
""")

    expanded = expand_netlist(netlist)
    pkg, libs = netlist_to_vlsir(expanded, "two_nmos")
    print(pkg, libs)
