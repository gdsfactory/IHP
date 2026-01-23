import gdsfactory as gf
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

def to_vlsir(
        top : gf.Component
) -> tuple[vckt.Package, list[str]]:
    
    # Get .YAML schematic in dict form
    yaml_schematic = top.get_netlist(recursive=True)[top.name]

    # Parse instances into VLSIR components and routing
    device_instances = []
    routing_instances = []
    lib_set = set()
    for k,v in yaml_schematic['instances'].items():
        if 'vlsir' in v['info'].keys():
            device_instances.append(k)
            lib_set.add(v['info']['vlsir']['spice_lib'])
        else:
            routing_instances.append(k)

    # Build graph of routing-to-routing connections
    routing_graph = {r: set() for r in routing_instances}

    for net in yaml_schematic.get('nets', []):
        p1_comp, _ = net['p1'].split(",")
        p2_comp, _ = net['p2'].split(",")

        if p1_comp in routing_graph and p2_comp in routing_graph:
            routing_graph[p1_comp].add(p2_comp)
            routing_graph[p2_comp].add(p1_comp)

    # BFS to find connected components → electrical nodes
    visited = set()
    routing_to_node = {}
    node_id = 0

    for start in routing_instances:
        if start in visited:
            continue
        queue = [start]
        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)
            routing_to_node[curr] = f"net_{node_id}"
            queue.extend(routing_graph[curr] - visited)
        node_id += 1

    # Map device ports to nodes via their routing connections
    device_port_nodes = {d: {} for d in device_instances}

    for net in yaml_schematic.get('nets', []):
        p1_comp, p1_port = net['p1'].split(",")
        p2_comp, p2_port = net['p2'].split(",")

        if p1_comp in device_port_nodes and p2_comp in routing_to_node:
            device_port_nodes[p1_comp][p1_port] = routing_to_node[p2_comp]
        elif p2_comp in device_port_nodes and p1_comp in routing_to_node:
            device_port_nodes[p2_comp][p2_port] = routing_to_node[p1_comp]

    # Now construct vckt.Package
    package = vckt.Package(domain="ihp")

    # Collect unique ExternalModules by model name
    ext_modules = {}
    for inst_name in device_instances:
        info = yaml_schematic['instances'][inst_name]['info']['vlsir']
        model = info['model']

        if model not in ext_modules:
            qname = vlsir.utils.QualifiedName(name=model, domain="ihp")
            spice_type = _spice_type_to_proto(info.get('spice_type', 'SUBCKT'))
            ext_mod = vckt.ExternalModule(name=qname, spicetype=spice_type)

            for port_name in info['port_order']:
                ext_mod.signals.append(vckt.Signal(name=port_name, width=1))
                ext_mod.ports.append(vckt.Port(
                    signal=port_name,
                    direction=vckt.Port.Direction.INOUT
                ))

            # Add parameters to ExternalModule definition
            for key, val in info.get('params', {}).items():
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
    top_module = vckt.Module(name=top.name)

    # Add signals for each electrical node
    node_set = set()
    for ports in device_port_nodes.values():
        node_set.update(ports.values())

    for node_name in sorted(node_set):
        top_module.signals.append(vckt.Signal(name=node_name, width=1))

    # Create instances with connections
    for inst_name in device_instances:
        info = yaml_schematic['instances'][inst_name]['info']['vlsir']
        port_map = info.get('port_map', {})

        inst = vckt.Instance(name=inst_name)
        inst.module.external.CopyFrom(vlsir.utils.QualifiedName(name=info['model'], domain="ihp"))

        # Add parameters
        for key, val in info.get('params', {}).items():
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
            inst.connections.append(vckt.Connection(
                portname=vlsir_port,
                target=vckt.ConnectionTarget(sig=node)
            ))

        top_module.instances.append(inst)

    package.modules.append(top_module)

    return package, list(lib_set)

if __name__ == "__main__":

    from ihp import PDK, LAYER
    import ihp.cells.transistors as xtors

    import gdsfactory as gf

    PDK.activate()

    c = gf.Component(name="TOP")
    x = xtors.nmos()

    p1 = c << x
    p2 = c << x
    p2.movex(2)

    gf.routing.route_single(
        c,
        p1['D'],
        p2['D'],
        cross_section="metal1_routing",
        auto_taper=False
    )

    gf.routing.route_single(
        c,
        p1['S'],
        p2['S'],
        cross_section="metal1_routing",
        auto_taper=False
    )

    pkg, libs = to_vlsir(c)
    print(pkg, libs)