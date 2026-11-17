"""gflvs LVS rules for the IHP SG13G2 PDK.

Usage::

    import gflvs
    from ihp.lvs.rules import DEFAULT_LVS_CONFIG

    ok, extracted, l2n, report = gflvs.lvs(netlist, lib, DEFAULT_LVS_CONFIG)

Flip the flags below and call ``build_lvs_config()`` for a variant config.

Targets the gflvs ``dev`` API (``gflvs.gflvs_refactor``: ``LvsConfig``, ``NetlistTracerConfig``,
``ElectricalDeviceExtractionConfig``) with templates built from ``gflvs.gflvs_schema`` protos.

gflvs extracts a device only from the polygons a cell draws itself (``depth=0``), so every device
PCell matched here must be flat.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator
from typing import Any

import gdstk
from gflvs import (
    ElectricalDeviceExtractionConfig,
    LvsConfig,
    NetlistTracerConfig,
)
from gflvs.gflvs_schema import (
    DeviceParameterTemplate,
    DeviceTemplate,
    DeviceTerminalTemplate,
    DeviceTerminalType,
    LayerGds,
    LayerOffsetOperation,
    LayerOperation,
    LayerRef,
    LvsRunMode,
)

from ihp import connectivity as pdk_connectivity
from ihp.tech import LAYER

# ── Flags ───────────────────────────────────────────────────────────
ENABLE_ELECTRICAL_TRACING = (
    True  # trace metal/via nets; False → tracer galvanic layers empty
)
ENABLE_DEVICE_EXTRACTION = True  # use DEVICE_TEMPLATES; False → connectivity-only LVS
ENABLE_MOSFET_TEMPLATES = True  # False → drop nmos/pmos(_hv)
ENABLE_RF_MOSFET_TEMPLATES = True  # False → drop rfnmos/rfpmos(_hv)
ENABLE_BJT_TEMPLATES = True  # False → drop npn13G2/L/V and pnpMPA
ENABLE_RESISTOR_TEMPLATES = True  # False → drop rsil/rppd/rhigh
ENABLE_CAPACITOR_TEMPLATES = True  # False → drop cmim/rfcmim
ENABLE_VARACTOR_TEMPLATES = True  # False → drop svaricap
ENABLE_ESD_TEMPLATES = True  # False → drop esd_nmos
ENABLE_INDUCTOR_TEMPLATES = True  # False → drop inductor2/inductor3
ENABLE_PAD_TEMPLATES = True  # False → drop bondpad
ENABLE_DIODE_TEMPLATES = True  # False → drop dantenna/dpantenna
ENABLE_PARAMETER_CHECK = True  # False → every template blackboxed (topology only)
HIERARCHICAL_RUN = False  # True → LVS_RUN_MODE_HIERARCHICAL, else FLAT
VERBOSE = False  # True → LvsConfig.verbose=1
PARAMETER_RELATIVE_TOLERANCE = 1e-3  # relative tolerance for parameter comparison

# ── Helpers ─────────────────────────────────────────────────────────
# ponytail: duplicated per PDK repo; move to gflvs when it ships helpers
LayerKey = tuple[int, int]
Extractor = Callable[[list[gdstk.Polygon]], float]
PIN = DeviceTerminalType.DEVICE_TERMINAL_TYPE_PIN


def _key(layer: Any) -> LayerKey:
    return (int(layer.layer), int(layer.datatype))


def L(layer: Any) -> LayerRef:  # noqa: N802
    """LayerRef for a PDK ``LAYER`` entry."""
    return LayerRef(
        layer=LayerGds(layer=int(layer.layer), datatype=int(layer.datatype))
    )


def op(x: LayerRef | LayerOperation) -> LayerOperation:
    """Wrap a bare LayerRef as a LayerOperation."""
    return x if isinstance(x, LayerOperation) else LayerOperation(layer_ref_left=x)


def grow(x: LayerRef | LayerOperation, d: float) -> LayerOperation:
    """Isotropic sizing by ``d`` µm (the evaluator reads offset_x only)."""
    side = "layer_ref_left" if isinstance(x, LayerRef) else "layer_op_left"
    return LayerOperation(
        **{side: x}, offset_op=LayerOffsetOperation(offset_x=d, offset_y=d)
    )


def pin(name: str, x: LayerRef | LayerOperation) -> DeviceTerminalTemplate:
    """Electrical terminal; the leftmost operand of ``x`` is the net layer."""
    return DeviceTerminalTemplate(
        terminal_name=name, terminal_type=PIN, layer_composed_op=op(x)
    )


def par(
    name: str, x: LayerRef | LayerOperation, extractor: str = "count"
) -> DeviceParameterTemplate:
    """Parameter region; ``extractor`` is the built-in fallback when PARAMETER_EXTRACTORS has no entry."""
    return DeviceParameterTemplate(
        name=name, layer_composed_op=op(x), properties={"extractor": extractor}
    )


def tpl(
    name: str,
    terms: list[DeviceTerminalTemplate],
    params: Iterable[DeviceParameterTemplate] = (),
) -> DeviceTemplate:
    """Device template; ``device_class_name`` is the PCell function name (prefix of the cell name)."""
    return DeviceTemplate(
        device_name=name,
        device_class_name=name,
        device_terminal_template=terms,
        device_parameter_template=list(params),
    )


# custom extractors: PCell-frame axes are valid because extraction runs per cell in its own frame
def _boxes(polys: list[gdstk.Polygon]) -> list[Any]:
    return [p.bounding_box() for p in polys]


def dx_max(polys: list[gdstk.Polygon]) -> float:
    """Widest single polygon in x."""
    return float(max((b[1][0] - b[0][0] for b in _boxes(polys)), default=float("nan")))


def dy_max(polys: list[gdstk.Polygon]) -> float:
    """Tallest single polygon in y."""
    return float(max((b[1][1] - b[0][1] for b in _boxes(polys)), default=float("nan")))


def dx_sum(polys: list[gdstk.Polygon]) -> float:
    """Summed x extent (total width over fingers)."""
    return (
        float(sum(b[1][0] - b[0][0] for b in _boxes(polys))) if polys else float("nan")
    )


def dy_sum(polys: list[gdstk.Polygon]) -> float:
    """Summed y extent (total width over fingers)."""
    return (
        float(sum(b[1][1] - b[0][1] for b in _boxes(polys))) if polys else float("nan")
    )


def n_columns(polys: list[gdstk.Polygon]) -> float:
    """Number of distinct polygon x-centres."""
    if not polys:
        return float("nan")
    return float(len({round((b[0][0] + b[1][0]) / 2, 3) for b in _boxes(polys)}))


def _leaf_layers(operation: LayerOperation) -> Iterator[LayerKey]:
    for side in ("left", "right"):
        field = operation.WhichOneof(f"layer_{side}")
        if field is None:
            continue
        if field.startswith("layer_ref"):
            yield _key(getattr(operation, field).layer)
        else:
            yield from _leaf_layers(getattr(operation, field))


def connectivity(
    chains: Iterable[tuple[LayerKey, LayerKey, LayerKey]],
) -> dict[LayerKey, list[LayerKey]]:
    """Symmetric adjacency from ``(a, via, b)`` chains."""
    c: dict[LayerKey, list[LayerKey]] = defaultdict(list)
    for a, v, b in chains:
        for x, y in ((a, v), (v, a), (v, b), (b, v)):
            if y not in c[x]:
                c[x].append(y)
    return dict(c)


# ── Layers ──────────────────────────────────────────────────────────
# NB: python precedence is `-` before `&` before `|`; the LEFTMOST operand is the terminal's net layer.
Activ, GatPoly, Cont = (
    L(LAYER.Activdrawing),
    L(LAYER.GatPolydrawing),
    L(LAYER.Contdrawing),
)
nSD, nSDblock, pSD = L(LAYER.nSDdrawing), L(LAYER.nSDblock), L(LAYER.pSDdrawing)
Metal1, Metal1pin, Metal2 = (
    L(LAYER.Metal1drawing),
    L(LAYER.Metal1pin),
    L(LAYER.Metal2drawing),
)
Metal5, TopMetal1, TopMetal2 = (
    L(LAYER.Metal5drawing),
    L(LAYER.TopMetal1drawing),
    L(LAYER.TopMetal2drawing),
)
RES, TRANS, HeatTrans = (
    L(LAYER.RESdrawing),
    L(LAYER.TRANSdrawing),
    L(LAYER.HeatTransdrawing),
)
IND, INDpin, SalBlock = L(LAYER.INDdrawing), L(LAYER.INDpin), L(LAYER.SalBlockdrawing)
NWell, nBuLay, PWellblock = (
    L(LAYER.NWelldrawing),
    L(LAYER.nBuLaydrawing),
    L(LAYER.PWellblock),
)
EmWind, EmWiHV, MIM = (
    L(LAYER.EmWinddrawing),
    L(LAYER.EmWiHVdrawing),
    L(LAYER.MIMdrawing),
)
dfpad, ThickGateOx, EXTBlock = (
    L(LAYER.dfpaddrawing),
    L(LAYER.ThickGateOxdrawing),
    L(LAYER.EXTBlockdrawing),
)
MemCap, Varicap, PolyRes = (
    L(LAYER.MemCapdrawing),
    L(LAYER.Varicapdrawing),
    L(LAYER.PolyResdrawing),
)
Recogesd, Recogdiode = L(LAYER.Recogesd), L(LAYER.Recogdiode)

# device marker / recognition / pin layers a terminal op may gate on
MARKER_LAYERS: frozenset[LayerKey] = frozenset(
    {_key(layer) for layer in LAYER if layer.name.startswith("Recog")}
    | {
        _key(layer)
        for layer in (
            LAYER.HeatTransdrawing,
            LAYER.TRANSdrawing,
            LAYER.RESdrawing,
            LAYER.MemCapdrawing,
            LAYER.Varicapdrawing,
            LAYER.INDdrawing,
            LAYER.INDpin,
            LAYER.dfpaddrawing,
            LAYER.EXTBlockdrawing,
            LAYER.Metal1pin,
        )
    }
)

# Grow distances. Values are the swarm's, verified on the variants in tests/test_lvs_rules.py.
# ponytail: tuned on PCell geometry; re-measure if PCell rules change
MOS_SD_REACH = 0.5  # S/D Metal1 pads sit next to the channel
RF_GATE_REACH = 1.0  # RF MOS Metal1 gate ring around the channel
RF_TIE_REACH = 1.5  # RF MOS guard ring around the channel
BJT_REACH = 1.5  # collector/base Metal1 around the emitter window
BJT_EMITTER_KEEPOUT = 0.3  # cut the emitter metal out of the collector op
PNP_REACH = 1.5  # pnpMPA outer TIE ring around nBuLay
CAP_TIE_REACH = 6.0  # rfcmim TIE_LOW guard ring around the MIM
VARICAP_REACH = 1.5  # svaricap Metal1 pads around the channel
IND_TAP_REACH = 10.0  # inductor3 TopMetal2 centre tap near the TopMetal1 pins
IND_GLUE = 5.0  # inductor2 pin glue (pins are 2 x diameter apart)

# Tracer connectivity: the PDK's own `connectivity`, minus Activ.
# Activ not traced: S/D would short through the channel (and C/E/B through bipolar diffusions).
# GatPoly kept: MOS gates and poly-resistor heads are GatPoly terminals.
# TODO(issue: pending): inductor2's spiral is one TopMetal2 polygon from P1 to P2, so the tracer shorts them.
LAYER_CONNECTIVITY: dict[LayerKey, list[LayerKey]] = connectivity(
    (_key(getattr(LAYER, a)), _key(getattr(LAYER, v)), _key(getattr(LAYER, b)))
    for a, v, b in pdk_connectivity
    if "Activdrawing" not in (a, v, b)
)

# ── Templates ───────────────────────────────────────────────────────
PARAMETER_EXTRACTORS: dict[tuple[str, str], Extractor] = {}


def _extract(templates: list[DeviceTemplate], **fns: Extractor) -> list[DeviceTemplate]:
    PARAMETER_EXTRACTORS.update(
        {(t.device_name, k): f for t in templates for k, f in fns.items()}
    )
    return templates


# LV/HV MOS: HeatTrans sits on every finger of these PCells only (not RF, not std cells).
# CONFIDENCE: HIGH
# TODO(issue: pending): the bulk pin is never drawn (no B terminal).
# TODO(issue: pending): finger width is rounded to the grid (width=0.5, nf=3 draws 0.495).
def _implant(o: LayerOperation, p: bool, hv: bool) -> LayerOperation:
    o = (o & pSD) if p else (o - pSD)
    return (o & ThickGateOx) if hv else (o - ThickGateOx)


def _mos(name: str, p: bool, hv: bool) -> DeviceTemplate:
    chan = _implant(Activ & GatPoly & HeatTrans, p, hv)
    return tpl(
        name,
        [
            pin(
                "S/D",
                _implant((Metal1 & Activ & grow(chan, MOS_SD_REACH)) - GatPoly, p, hv),
            ),  # x-ordered S,D,S..
            pin("G", _implant((GatPoly & HeatTrans) - Activ, p, hv)),
        ],
        [
            par("width", chan),
            par("length", chan),
            par("nf", chan),
            par("glue", grow(chan, MOS_SD_REACH)),
        ],
    )


MOSFET_TEMPLATES = _extract(
    [
        _mos("nmos", False, False),
        _mos("pmos", True, False),
        _mos("nmos_hv", False, True),
        _mos("pmos_hv", True, True),
    ],
    width=dy_sum,  # total W over fingers; nf = count
    length=dx_max,
)


# RF MOS: no HeatTrans; S/D stacked in y; Metal1 gate ring; TIE = guard ring (bulk B).
# CONFIDENCE: MEDIUM (standard cells sg13g2_* cross-match: blackbox or subcircuit them)
def _rf(o: LayerOperation, p: bool, hv: bool) -> LayerOperation:
    o = o - HeatTrans - Recogesd - Varicap
    o = (o & pSD & NWell) if p else (o - pSD - NWell)
    return (o & ThickGateOx) if hv else (o - ThickGateOx)


def _rfmos(name: str, p: bool, hv: bool) -> DeviceTemplate:
    chan = _rf(Activ & GatPoly, p, hv)
    sd = (Metal1 & Activ & grow(chan, MOS_SD_REACH)) - GatPoly
    tie = Metal1 & Activ & grow(chan, RF_TIE_REACH)
    return tpl(
        name,
        [
            pin("S/D", (sd & pSD) if p else (sd - pSD)),
            pin("G", (Metal1 & GatPoly & grow(chan, RF_GATE_REACH)) - Activ),
            pin("TIE", (tie - pSD) if p else (tie & pSD)),
        ],
        [
            par("width", chan),
            par("length", chan),
            par("nf", chan),
            par("glue", grow(chan, RF_TIE_REACH)),
        ],
    )


RF_MOSFET_TEMPLATES = _extract(
    [
        _rfmos("rfnmos", False, False),
        _rfmos("rfpmos", True, False),
        _rfmos("rfnmos_hv", False, True),
        _rfmos("rfpmos_hv", True, True),
    ],
    width=dx_sum,
    length=dy_max,
)


# NPN HBTs: seed = emitter window; E on Metal1 (Via1 -> Metal2 E pin).
# CONFIDENCE: HIGH
# TODO(issue: pending): npn13G2 ignores `Ny` (one emitter window row only).
# TODO(issue: pending): the BN (substrate) pin is never drawn.
def _npn(name: str, seed: LayerOperation) -> DeviceTemplate:
    return tpl(
        name,
        [
            pin("E", Metal1 & seed),
            pin(
                "C",
                (Metal1 & Activ & grow(seed, BJT_REACH))
                - pSD
                - grow(seed, BJT_EMITTER_KEEPOUT),
            ),
            pin("B", (Metal1 & Cont & grow(seed, BJT_REACH)) - Activ),
        ],
        [
            par("emitter_width", seed),
            par("emitter_length", seed),
            par("Nx", seed),
            par("glue", grow(seed, BJT_REACH)),
        ],
    )


# pnpMPA: nBuLay is unique to it; Metal1pin gates the terminals (no other marker drawn).
# CONFIDENCE: HIGH
_emitter = Activ & pSD & nBuLay
BJT_TEMPLATES = _extract(
    [
        _npn("npn13G2", EmWind & nSDblock & TRANS),
        _npn("npn13G2L", EmWind & HeatTrans & TRANS),
        _npn("npn13G2V", EmWiHV & TRANS),
    ],
    emitter_width=dx_max,
    emitter_length=dy_max,
    Nx=n_columns,
) + _extract(
    [
        tpl(
            "pnpMPA",
            [
                pin("PLUS", Metal1 & Metal1pin & _emitter),
                pin("MINUS", (Metal1 & Metal1pin & Activ & nBuLay) - pSD),
                pin(
                    "TIE",
                    (Metal1 & Metal1pin & Activ & pSD & grow(nBuLay, PNP_REACH))
                    - NWell,
                ),
            ],
            [
                par("width", _emitter),
                par("length", _emitter),
                par("glue", grow(nBuLay, PNP_REACH)),
            ],
        )
    ],
    width=dx_max,
    length=dy_max,
)


# Poly resistors: GatPoly heads abut the PolyRes body; built-in extractors work (gap=dy, facing edge=dx).
# y-ordered heads: lower = P2, upper = P1 (matches ports).
# CONFIDENCE: HIGH
# TODO(issue: pending): the BN (substrate) pin is never drawn.
RESISTOR_TEMPLATES = [
    tpl(
        name,
        [pin("P2/P1", head)],
        [par("dy", body, "length"), par("dx", body, "width")],
    )
    for name, body, head in [
        ("rsil", (PolyRes & RES) - pSD - nSD, (GatPoly & EXTBlock) - pSD - nSD),
        ("rppd", (PolyRes & pSD & SalBlock) - nSD, (GatPoly & EXTBlock & pSD) - nSD),
        ("rhigh", PolyRes & pSD & nSD & SalBlock, GatPoly & EXTBlock & pSD & nSD),
    ]
]


# MIM caps: TopMetal1 plate is width(y) x length(x).
# cmim CONFIDENCE: HIGH; rfcmim CONFIDENCE: MEDIUM (hierarchy: holds a cmim subcell unless flat)
def _mim(name: str, seed: LayerOperation) -> DeviceTemplate:
    terms = [pin("PLUS", TopMetal1 & seed), pin("MINUS", Metal5 & seed)]
    if name == "rfcmim":
        terms.append(pin("TIE_LOW", Metal1 & Activ & pSD & grow(seed, CAP_TIE_REACH)))
    plate = TopMetal1 & seed
    return tpl(
        name,
        terms,
        [
            par("width", plate),
            par("length", plate),
            par("glue", grow(seed, CAP_TIE_REACH)),
        ],
    )


CAPACITOR_TEMPLATES = _extract(
    [
        _mim("cmim", (MIM & MemCap) - PWellblock),
        _mim("rfcmim", MIM & MemCap & PWellblock),
    ],
    width=dy_max,
    length=dx_max,
)


# svaricap: G = left pad, B = right pad, both Metal1.
# CONFIDENCE: LOW
# TODO(issue: pending): pads don't touch the contacts, the gate has no contact, and ports (G, B)
# don't match the SPICE pins (G1, W, G2, BN).
_vchan = Activ & GatPoly & Varicap
VARACTOR_TEMPLATES = _extract(
    [
        tpl(
            "svaricap",
            [pin("G/B", Metal1 & grow(_vchan, VARICAP_REACH))],
            [
                par("width", _vchan),
                par("length", _vchan),
                par("nf", _vchan),
                par("glue", grow(_vchan, VARICAP_REACH)),
            ],
        )
    ],
    width=dy_sum,
    length=dx_max,
)


# ESD clamp: PAD on Metal2 (-> VDD), GND on Metal1 (-> VSS).
# CONFIDENCE: LOW (length not drawn)
# TODO(issue: pending): GatPoly covers all of Activ, one Metal1 spans S and D, and the Metal2 PAD has no Via1.
ESD_TEMPLATES = _extract(
    [
        tpl(
            "esd_nmos",
            [pin("PAD", Metal2 & Recogesd), pin("GND", Metal1 & Recogesd)],
            [
                par("width", Activ & Recogesd),
                par("nf", Activ & Recogesd),
                par("glue", Recogesd),
            ],
        )
    ],
    width=dy_sum,
)


# Inductors: pins are TopMetal1/TopMetal2 & INDpin & IND.
# inductor2 CONFIDENCE: LOW (turns=1 only); inductor3 CONFIDENCE: MEDIUM
# TODO(issue: pending): inductor2(turns=2) draws the same three-port geometry as inductor3 and is classified as it.
_tm1_pins = TopMetal1 & INDpin & IND
_ind2_pins = (TopMetal2 & INDpin & IND) - grow(_tm1_pins, IND_TAP_REACH)
INDUCTOR_TEMPLATES = [
    tpl(
        "inductor2",
        [pin("P1/P2", _ind2_pins)],
        [par("glue", grow(_ind2_pins, IND_GLUE))],
    ),
    tpl(
        "inductor3",
        [
            pin("P1", TopMetal2 & INDpin & IND & grow(_tm1_pins, IND_TAP_REACH)),
            pin("P2/P3", _tm1_pins),
        ],
        [par("glue", grow(_tm1_pins, IND_TAP_REACH))],
    ),
]


# Bondpad: pad on TopMetal2 (-> PAD).
# CONFIDENCE: MEDIUM
PAD_TEMPLATES = _extract(
    [tpl("bondpad", [pin("pad", TopMetal2 & dfpad)], [par("diameter", dfpad)])],
    diameter=dx_max,
)


# Antenna diodes: no ports in the PCells; terminal named by SPICE pin, the other pin is the implicit
# substrate (dantenna) or well (dpantenna).
# CONFIDENCE: MEDIUM
_dn = (Activ & Recogdiode) - pSD - NWell
_dp = Activ & Recogdiode & pSD & NWell
DIODE_TEMPLATES = _extract(
    [
        tpl(
            "dantenna",
            [pin("2", Metal1 & _dn)],
            [par("width", _dn), par("length", _dn)],
        ),
        tpl(
            "dpantenna",
            [pin("1", Metal1 & _dp)],
            [par("width", _dp), par("length", _dp)],
        ),
    ],
    width=dx_max,
    length=dy_max,
)

# Templates whose terminals cannot gate on a marker, with the reason.
NO_MARKER_TEMPLATES: frozenset[str] = frozenset(
    # RF MOS draw no marker, and Metal1pin covers only the port fingers (nf>1 would lose S/D fingers)
    {"rfnmos", "rfpmos", "rfnmos_hv", "rfpmos_hv"}
)

# via_stack_*, via_array_*, via_stack_with_pads_* (matched as a lowercase cell-name prefix)
PASSTHROUGH_DEVICE_CLASS_NAMES: tuple[str, ...] = ("via",)


def _groups() -> list[tuple[bool, list[DeviceTemplate]]]:
    return [
        (ENABLE_MOSFET_TEMPLATES, MOSFET_TEMPLATES),
        (ENABLE_RF_MOSFET_TEMPLATES, RF_MOSFET_TEMPLATES),
        (ENABLE_BJT_TEMPLATES, BJT_TEMPLATES),
        (ENABLE_RESISTOR_TEMPLATES, RESISTOR_TEMPLATES),
        (ENABLE_CAPACITOR_TEMPLATES, CAPACITOR_TEMPLATES),
        (ENABLE_VARACTOR_TEMPLATES, VARACTOR_TEMPLATES),
        (ENABLE_ESD_TEMPLATES, ESD_TEMPLATES),
        (ENABLE_INDUCTOR_TEMPLATES, INDUCTOR_TEMPLATES),
        (ENABLE_PAD_TEMPLATES, PAD_TEMPLATES),
        (ENABLE_DIODE_TEMPLATES, DIODE_TEMPLATES),
    ]


DEVICE_TEMPLATES: list[DeviceTemplate] = [t for _, group in _groups() for t in group]


def template_layers(templates: Iterable[DeviceTemplate]) -> frozenset[LayerKey]:
    """Every leaf layer read by any terminal or parameter op of ``templates``."""
    return frozenset(
        layer
        for t in templates
        for x in (*t.device_terminal_template, *t.device_parameter_template)
        for layer in _leaf_layers(x.layer_composed_op)
    )


def build_lvs_config() -> LvsConfig:
    """Build an LvsConfig from the module flags, read at call time."""
    templates = (
        [t for on, group in _groups() if on for t in group]
        if ENABLE_DEVICE_EXTRACTION
        else []
    )
    if not ENABLE_PARAMETER_CHECK:
        blackboxed = []
        for t in templates:
            t2 = DeviceTemplate()
            t2.CopyFrom(t)
            t2.properties["blackbox"] = "true"
            blackboxed.append(t2)
        templates = blackboxed
    return LvsConfig(
        device_templates=templates,
        netlist_tracer_config=NetlistTracerConfig(
            layer_connectivity=LAYER_CONNECTIVITY,
            # routing metals, vias and GatPoly only: Activ/PolyRes/plates stay out or they short devices
            galvanic_drawing_layers=frozenset(LAYER_CONNECTIVITY)
            if ENABLE_ELECTRICAL_TRACING
            else frozenset(),
            passthrough_device_class_names=PASSTHROUGH_DEVICE_CLASS_NAMES,
        ),
        electrical_device_extraction_config=ElectricalDeviceExtractionConfig(
            galvanic_drawing_layers=template_layers(templates),
            parameter_extractors=PARAMETER_EXTRACTORS,
        ),
        parameter_relative_tolerance=PARAMETER_RELATIVE_TOLERANCE,
        run_mode=LvsRunMode.LVS_RUN_MODE_HIERARCHICAL
        if HIERARCHICAL_RUN
        else LvsRunMode.LVS_RUN_MODE_FLAT,
        verbose=1 if VERBOSE else 0,
    )


DEFAULT_LVS_CONFIG = build_lvs_config()
