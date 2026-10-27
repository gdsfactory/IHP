"""5-transistor CMOS OTA built on IHP SG13G2 test cells.

Topology (classic single-stage differential OTA):

          VDD
           |
   +-------+-------+
   |               |
  |M3|==========|M4|   <- PMOS current mirror (M3 diode)
   |               |
   +---nodeA       +---- vout  (node B)
       |               |
   |M1|               |M2|    <- NMOS differential input pair
       |               |
       +-------+-------+
               |
              |M5|            <- NMOS tail current source
               |
              GND

Device sizing is illustrative only; pick numeric targets in a real design.
"""

from __future__ import annotations

import gdsfactory as gf
from gdsfactory.component import Component
from ihp import PDK, cells

_PDK_READY = False


def _ensure_pdk() -> None:
    global _PDK_READY
    if not _PDK_READY:
        PDK.activate()
        _PDK_READY = True


def _lift_to_topmetal2(
    c: Component,
    port: gf.Port,
    bottom_layer: str,
    index: int,
) -> gf.Port:
    """Drop a via_stack at `port.center` lifting bottom_layer -> TopMetal2.

    Returns a freshly synthesised port on TopMetal2drawing (not the pin layer
    that via_stack exposes) so the gdsfactory router can taper into it.
    """
    vs = c << cells.via_stack(bottom_layer=bottom_layer, top_layer="TopMetal2")
    vs.move(port.center)
    top = vs.ports["TopMetal2_E"]
    name = f"_lift_{index}"
    c.add_port(
        name=name,
        center=top.center,
        width=top.width,
        orientation=0,
        layer="TopMetal2drawing",
        port_type="electrical",
    )
    return c.ports[name]


@gf.cell(tags={"type": "opamps"})
def opamp_5t(
    input_width: float = 2.0,
    input_length: float = 0.5,
    load_width: float = 4.0,
    load_length: float = 0.5,
    tail_width: float = 4.0,
    tail_length: float = 1.0,
    pair_dx: float = 20.0,
    load_dy: float = 20.0,
    tail_dy: float = -15.0,
) -> Component:
    """Return a placed 5-transistor OTA with intra-core nets routed.

    The core exposes six electrical ports: VDD, GND, VIN_P, VIN_N, VOUT, VBIAS.
    Top-level pads can be attached by wrapping this cell with
    :func:`ihp.cells.add_pads_top` if desired.
    """
    _ensure_pdk()

    c = gf.Component()

    # --- Devices -------------------------------------------------------
    m1 = c << cells.nmos(width=input_width, length=input_length)  # Vin_p
    m2 = c << cells.nmos(width=input_width, length=input_length)  # Vin_n
    m3 = c << cells.pmos(width=load_width, length=load_length)  # diode load
    m4 = c << cells.pmos(width=load_width, length=load_length)  # mirror out
    m5 = c << cells.nmos(width=tail_width, length=tail_length)  # tail

    m1.move((-pair_dx / 2, 0.0))
    m2.move((pair_dx / 2, 0.0))
    m3.move((-pair_dx / 2, load_dy))
    m4.move((pair_dx / 2, load_dy))
    m5.move((0.0, tail_dy))

    # --- Intra-core routing -------------------------------------------
    # All transistor drains/sources are already on Metal1; gates on GatPoly.
    # Route with TopMetal2 by lifting every participating port through a
    # via_stack first; this keeps the routing graph single-layer.
    tm2_xs = "metal_routing"  # IHP preset: TopMetal2, metal bends
    route_kwargs = dict(
        cross_section=tm2_xs,
        straight="straight_metal",
        bend="bend_metal",
        taper=None,
        port_type="electrical",
        allow_width_mismatch=True,
    )

    _idx = [0]

    def lift(port, metal):
        i = _idx[0]
        _idx[0] += 1
        return _lift_to_topmetal2(c, port, metal, i)

    # Node A (M1.D == M3.D == M3.G == M4.G)
    nodeA_ports = [
        lift(m1.ports["D"], "Metal1"),
        lift(m3.ports["D"], "Metal1"),
        lift(m3.ports["G"], "GatPoly"),
        lift(m4.ports["G"], "GatPoly"),
    ]
    # Node B (M2.D == M4.D) == vout
    nodeB_ports = [
        lift(m2.ports["D"], "Metal1"),
        lift(m4.ports["D"], "Metal1"),
    ]
    # Tail node (M1.S == M2.S == M5.D)
    tail_ports = [
        lift(m1.ports["S"], "Metal1"),
        lift(m2.ports["S"], "Metal1"),
        lift(m5.ports["D"], "Metal1"),
    ]
    # VDD (M3.S == M4.S)
    vdd_ports = [lift(m3.ports["S"], "Metal1"), lift(m4.ports["S"], "Metal1")]
    # GND (M5.S)
    gnd_ports = [lift(m5.ports["S"], "Metal1")]
    # Vbias (M5.G)
    vbias_ports = [lift(m5.ports["G"], "GatPoly")]
    # Vin_p, Vin_n (M1.G, M2.G)
    vinp_ports = [lift(m1.ports["G"], "GatPoly")]
    vinn_ports = [lift(m2.ports["G"], "GatPoly")]

    def _bundle_tie(ports):
        if len(ports) < 2:
            return
        first = ports[0]
        for p in ports[1:]:
            gf.routing.route_bundle(c, [first], [p], **route_kwargs)

    _bundle_tie(nodeA_ports)
    _bundle_tie(nodeB_ports)
    _bundle_tie(tail_ports)
    _bundle_tie(vdd_ports)

    # --- Expose external ports ---------------------------------------
    c.add_port("VDD", port=vdd_ports[0])
    c.add_port("GND", port=gnd_ports[0])
    c.add_port("VIN_P", port=vinp_ports[0])
    c.add_port("VIN_N", port=vinn_ports[0])
    c.add_port("VOUT", port=nodeB_ports[0])
    c.add_port("VBIAS", port=vbias_ports[0])

    return c


if __name__ == "__main__":
    c = opamp_5t()
    c.show()
    c.write_gds("opamp_5t.gds", with_metadata=False)
    print("wrote opamp_5t.gds")
