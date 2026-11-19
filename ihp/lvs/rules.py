"""gflvs LVS rules for the IHP SG13G2 PDK.

Usage::

    import gflvs
    from ihp.lvs.rules import DEFAULT_LVS_CONFIG

    ok, extracted, l2n, report = gflvs.lvs(
        netlist, lib, DEFAULT_LVS_CONFIG, topcell=component.name
    )

An empty topcell picks gdsfactory's ``$$$CONTEXT_INFO$$$`` cell (doplaydo/gflvs#137), so pass it.

Flip the flags below and call ``build_lvs_config()`` for a variant config.

Targets the gflvs ``dev`` API (``gflvs.gflvs_refactor``: ``LvsConfig``, ``NetlistTracerConfig``,
``ElectricalDeviceExtractionConfig``) with templates built from ``gflvs.gflvs_schema`` protos.

gflvs extracts a device only from the polygons a cell draws itself (``depth=0``), so every device
PCell matched here must be flat.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator
from itertools import pairwise
from typing import Any, cast

import gdstk
from gflvs import (
    ElectricalDeviceExtractionConfig,
    LvsConfig,
    NetlistTracerConfig,
    WaveguideDeviceExtractionConfig,
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
from ihp.cells import inductor2
from ihp.tech import LAYER

# ── Flags ───────────────────────────────────────────────────────────
ENABLE_ELECTRICAL_TRACING = (
    True  # trace metal/via nets; False → tracer galvanic layers empty
)
ENABLE_DEVICE_EXTRACTION = True  # use DEVICE_TEMPLATES; False → connectivity-only LVS
ENABLE_MOSFET_TEMPLATES = True  # False → drop nmos/pmos(_hv)
ENABLE_RF_MOSFET_TEMPLATES = (
    False  # True → add rfnmos/rfpmos(_hv); they then double-match MOS (no RF layer)
)
ENABLE_BJT_TEMPLATES = True  # False → drop npn13G2/L/V and pnpMPA
ENABLE_RESISTOR_TEMPLATES = True  # False → drop rsil/rppd/rhigh
ENABLE_CAPACITOR_TEMPLATES = True  # False → drop cmim/rfcmim/cmom
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
# an extractor may also take `geometry_by_layer`: the cell's polygons by layer (gflvs passes it by keyword)
Extractor = Callable[..., float]
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
Metal3, Metal4 = L(LAYER.Metal3drawing), L(LAYER.Metal4drawing)
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
Activmask, Substrate = L(LAYER.Activmask), L(LAYER.Substratedrawing)

# device marker / recognition / pin layers a terminal op may gate on
MARKER_LAYERS: frozenset[LayerKey] = frozenset(
    {
        _key(layer)
        for layer in cast(Iterable[Any], LAYER)
        if layer.name.startswith("Recog")
    }
    | {
        _key(layer)
        for layer in (
            LAYER.HeatTransdrawing,
            LAYER.TRANSdrawing,
            LAYER.RESdrawing,
            LAYER.MemCapdrawing,
            LAYER.MIMdrawing,
            LAYER.Varicapdrawing,
            LAYER.INDdrawing,
            LAYER.INDpin,
            LAYER.dfpaddrawing,
            LAYER.EXTBlockdrawing,
            LAYER.Metal1pin,
        )
    }
)

# Grow distances, measured on the PCells in tests/test_lvs_rules.py.
# ponytail: tuned on PCell geometry; re-measure if PCell rules change
# NB: every glue grow feeds gflvs' bbox device grouping (G2: neighbours merge); keep them minimal.
MOS_SD_REACH = 0.5  # S/D Metal1 pads and gate endcaps sit next to the channel
MOS_ENDCAP_PROBE = 0.01  # gate-end probe strip (needs gate endcap > 0.02; IHP min 0.18)
RF_GATE_REACH = 1.0  # RF MOS Metal1 gate ring around the channel
RF_TIE_REACH = 1.5  # RF MOS guard ring around the channel
BJT_REACH = 1.5  # collector/base Metal1 around the emitter window
BJT_EMITTER_KEEPOUT = 0.3  # cut the emitter metal out of the collector op
BJT_E_REACH = (
    1.0  # Metal2 E strap between emitters (pitch 1.85, gap 1.15) and over the E port
)
PNP_BASE_REACH = 1.0  # pnpMPA MINUS (base) pin from the emitter (max 0.72)
PNP_TIE_REACH = 2.5  # pnpMPA TIE (collector) pin from the emitter (max 2.01)
PNP_POLY_KEEPOUT = (
    3.0  # p+ diffusion this close to GatPoly is MOS S/D, not a pnp emitter
)
# ponytail: a real pnp emitter within 3 um of any GatPoly won't extract; the deck instead requires
# base/collector rings around it (pnp_mpa_e), which needs gflvs "interacting" selection
RES_REACH = 0.3  # Metal1 head pads to the PolyRes body (max 0.15: rhigh)
CAP_PLATE_REACH = (
    0.6  # Metal5 bottom plate overhang beyond MIM, MINUS port inside it (0.6)
)
CAP_TIE_REACH = 6.0  # rfcmim TIE_LOW guard ring around the MIM
VARICAP_REACH = 1.5  # svaricap Metal1 pads around the channel
VARICAP_PGATE_REACH = (
    0.3  # pSD-covered gate ends of official svaricaps (0.25 deep), not pmos
)
ESD_REACH = 2.0  # esd_nmos Metal2 PAD strip from the gate (max 2.0)
IND_TAP_REACH = 10.0  # inductor3 TopMetal2 centre tap near the TopMetal1 pins

# Tracer connectivity: the PDK's own `connectivity`, minus Activ.
# Activ not traced: S/D would short through the channel (and C/E/B through bipolar diffusions).
# GatPoly kept: MOS gates are GatPoly terminals (poly-resistor heads are Metal1 pads).
# TODO(https://github.com/gdsfactory/IHP/issues/302): inductor spirals are one continuous metal path between their pins, so the tracer
# shorts P1/P2 (inductor2) and P1/P2/P3 (inductor3).
LAYER_CONNECTIVITY: dict[LayerKey, list[LayerKey]] = connectivity(
    (
        _key(getattr(LAYER, chain[0])),
        _key(getattr(LAYER, chain[1])),
        _key(getattr(LAYER, chain[2])),
    )
    # ponytail: 2-tuple (direct conductor-conductor) specs are skipped; ihp declares none
    for chain in pdk_connectivity
    if len(chain) == 3 and "Activdrawing" not in chain
)

# ── Templates ───────────────────────────────────────────────────────
PARAMETER_EXTRACTORS: dict[tuple[str, str], Extractor] = {}


def _extract(templates: list[DeviceTemplate], **fns: Extractor) -> list[DeviceTemplate]:
    PARAMETER_EXTRACTORS.update(
        {(t.device_name, k): f for t in templates for k, f in fns.items()}
    )
    return templates


def _minus(o: LayerRef | LayerOperation, *layers: LayerRef) -> LayerOperation:
    for layer in layers:
        o = o - layer
    return op(o)


# IHP deck `mos_exclude`: a gate under any of these is another device, not a MOS.
_MOS_EXCLUDE: tuple[LayerRef, ...] = (
    PWellblock,
    nSD,
    TRANS,
    EmWind,
    EmWiHV,
    SalBlock,
    PolyRes,
    EXTBlock,
    RES,
)
_MOS_EXCLUDE += (Activmask, Recogdiode, Recogesd, IND, INDpin, Substrate, nSDblock)
# svaricap core (deck varicap_core): an n-gate inside NWell, gated by Varicap (our PCell) or nBuLay
# (official layouts draw nBuLay, the deck's nwell_iso, and no Varicap); see VARACTOR_TEMPLATES
_nwell_ngate = _minus(
    Activ & GatPoly & NWell, pSD, nSDblock, PWellblock, Recogesd, Recogdiode, Substrate
)
_vchan = _nwell_ngate & (Varicap | nBuLay)


# LV/HV MOS: the deck's gate = Activ & GatPoly minus `mos_exclude`, split by pSD and ThickGateOx.
# nmos also excludes NWell (an n-gate in NWell is the svaricap). Matches std cells and official layouts.
# CONFIDENCE: HIGH
# TODO(https://github.com/gdsfactory/IHP/issues/302): the bulk pin is never drawn (no B terminal).
# TODO(https://github.com/gdsfactory/IHP/issues/302): finger width is rounded to the grid (width=0.5, nf=3 draws 0.495).
# TODO(https://github.com/gdsfactory/IHP/issues/302): multi-finger nmos/pmos(_hv) leave S/D fingers unstrapped (P5; gflvs G1 hides it).
# TODO(gflvs): moscap_n/p are told apart from MOS by a 63/0 text; gflvs can't key on text, so they extract as MOS.
def _implant(o: LayerOperation, p: bool, hv: bool) -> LayerOperation:
    o = (o & pSD) if p else (o - pSD - NWell)
    return (o & ThickGateOx) if hv else (o - ThickGateOx)


def _mos(name: str, p: bool, hv: bool) -> DeviceTemplate:
    # official svaricaps put pSD over their gate ends: a p-gate touching a varicap core is not a pmos
    # (unclipped core: the official gate ends lie past nBuLay)
    chan = _implant(_minus(Activ & GatPoly, *_MOS_EXCLUDE), p, hv) - grow(
        _nwell_ngate, VARICAP_PGATE_REACH
    )
    # gates plus thin GatPoly strips just past each gate end, which show the W axis (rf PCells turn gates)
    probe = (GatPoly & grow(chan, 2 * MOS_ENDCAP_PROBE)) - grow(Activ, MOS_ENDCAP_PROBE)
    wl = chan | probe
    return tpl(
        name,
        [
            pin(
                "S/D",
                _implant((Metal1 & Activ & grow(chan, MOS_SD_REACH)) - GatPoly, p, hv),
            ),  # x-ordered S,D,S..
            # GatPoly is traced; the region covers the channel, where the G port sits
            pin("G", GatPoly & grow(chan, MOS_SD_REACH)),
        ],
        [
            par("width", wl),
            par("length", wl),
            par("nf", chan),
            par("glue", grow(chan, MOS_SD_REACH)),
        ],
    )


def _mos_wl(polys: list[gdstk.Polygon]) -> tuple[float, float]:
    """(total W, L) from gate fingers plus the thin GatPoly probes past each gate end (W axis)."""
    dims = [(b[1][0] - b[0][0], b[1][1] - b[0][1]) for b in _boxes(polys)]
    probes = [d for d in dims if min(d) < 2 * MOS_ENDCAP_PROBE]
    gates = [d for d in dims if min(d) >= 2 * MOS_ENDCAP_PROBE]
    if not gates:
        return float("nan"), float("nan")
    if not probes:  # no endcap seen: vertical gates (W along y), the IHP default
        return float(sum(dy for _, dy in gates)), float(max(dx for dx, _ in gates))
    length = max(max(d) for d in probes)
    width = sum(dy if abs(dx - length) <= abs(dy - length) else dx for dx, dy in gates)
    return float(width), float(length)


def mos_width(polys: list[gdstk.Polygon]) -> float:
    """Total gate width over fingers, in either gate orientation."""
    return _mos_wl(polys)[0]


def mos_length(polys: list[gdstk.Polygon]) -> float:
    """Gate length, in either gate orientation."""
    return _mos_wl(polys)[1]


MOSFET_TEMPLATES = _extract(
    [
        _mos("nmos", False, False),
        _mos("pmos", True, False),
        _mos("nmos_hv", False, True),
        _mos("pmos_hv", True, True),
    ],
    width=mos_width,  # total W over fingers; nf = count
    length=mos_length,
)


# RF MOS: S/D stacked in y; Metal1 gate ring; TIE = guard ring (bulk B).
# Off by default (ENABLE_RF_MOSFET_TEMPLATES): no geometric layer tells RF MOS from MOS.
# TODO(gflvs): the deck recognises RF MOS by a 63/0 "rfnmos"/"rfpmos"(HV) text in the guard ring; gflvs can't
# key on text, so RF MOS extract as nmos/pmos (as KLayout does for our rf PCells, which lack that text).
# TODO(https://github.com/gdsfactory/IHP/issues/302): rfnmos/rfpmos(_hv) PCells don't draw the 63/0 RF text (P2), so the deck reads them as MOS.
# CONFIDENCE: MEDIUM
def _rf(o: LayerOperation, p: bool, hv: bool) -> LayerOperation:
    o = _minus(o, *_MOS_EXCLUDE, Varicap)
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


# NPN HBTs: positive keys like the deck's emitter windows (bjt_derivations.lvs); exclusions partial
# (the deck also drops Activ/EmWiHV/npn_exclude from npn13G2 and EmWind/EmWiHV/npn_exclude from L/V):
#   npn13G2 = EmWind & Activmask & nSDblock; npn13G2L = EmWind & Activ, not Activmask/nSDblock;
#   npn13G2V = EmWiHV & Activ, not Activmask/nSDblock. All inside TRANS. (HeatTrans is on all three.)
# E sits on the Metal2 strap over the emitters, where the E port is.
# CONFIDENCE: HIGH
# TODO(https://github.com/gdsfactory/IHP/issues/302): npn13G2 ignores `Ny` (one emitter window row only).
# TODO(https://github.com/gdsfactory/IHP/issues/302): the BN (substrate) pin is never drawn.
# TODO(https://github.com/gdsfactory/IHP/issues/302): npn13G2 draws a 0.7 um emitter; the deck needs 0.07-0.9 um bbox, 0.063 um2 (P1).
# TODO(gflvs): the B and C ports sit on Metal1 straps outside these clipped regions, so a route landing there
# stays open (G3: device-cell metal is never traced). Covering them needs whole-polygon selection or G3.
def _npn(name: str, seed: LayerOperation) -> DeviceTemplate:
    return tpl(
        name,
        [
            pin("E", Metal2 & grow(seed, BJT_E_REACH)),
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


# pnpMPA, keyed like the deck's pnp_mpa_e: p+ Activ in NWell & nBuLay, away from any gate and outside
# the deck's `pnp_exclude` layers. Metal1pin gates the terminals (no other marker drawn).
# CONFIDENCE: HIGH
_emitter = _minus(
    Activ & pSD & NWell & nBuLay,
    *(
        TRANS,
        EmWind,
        EmWiHV,
        nSDblock,
        PWellblock,
        nSD,
        SalBlock,
        PolyRes,
        EXTBlock,
        RES,
    ),
    *(Recogdiode, Recogesd, IND, INDpin, Substrate),
) - grow(GatPoly, PNP_POLY_KEEPOUT)
BJT_TEMPLATES = _extract(
    [
        _npn("npn13G2", EmWind & Activmask & nSDblock & TRANS),
        _npn("npn13G2L", (EmWind & Activ & TRANS) - Activmask - nSDblock),
        _npn("npn13G2V", (EmWiHV & Activ & TRANS) - Activmask - nSDblock),
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
                pin(
                    "MINUS",
                    (
                        Metal1
                        & Metal1pin
                        & Activ
                        & nBuLay
                        & grow(_emitter, PNP_BASE_REACH)
                    )
                    - pSD,
                ),
                pin(
                    "TIE",
                    (Metal1 & Metal1pin & Activ & pSD & grow(_emitter, PNP_TIE_REACH))
                    - NWell,
                ),
            ],
            [
                par("width", _emitter),
                par("length", _emitter),
                par("glue", grow(_emitter, PNP_TIE_REACH)),
            ],
        )
    ],
    width=dx_max,
    length=dy_max,
)


# Poly resistors: P1/P2 are the Metal1 pads on the GatPoly heads (ports sit on Metal1pin);
# dy/dx are measured on the PolyRes body between the heads. y-ordered: lower = P2, upper = P1.
# CONFIDENCE: HIGH
# TODO(https://github.com/gdsfactory/IHP/issues/302): the BN (substrate) pin is never drawn.
RESISTOR_TEMPLATES = _extract(
    [
        tpl(
            name,
            [pin("P2/P1", Metal1 & head)],
            [
                par("dy", body - GatPoly),
                par("dx", body - GatPoly),
                par("glue", grow(body - GatPoly, RES_REACH)),
            ],
        )
        for name, body, head in [
            ("rsil", (PolyRes & RES) - pSD - nSD, (GatPoly & EXTBlock) - pSD - nSD),
            (
                "rppd",
                (PolyRes & pSD & SalBlock) - nSD,
                (GatPoly & EXTBlock & pSD) - nSD,
            ),
            ("rhigh", PolyRes & pSD & nSD & SalBlock, GatPoly & EXTBlock & pSD & nSD),
        ]
    ],
    dy=dy_max,
    dx=dx_max,
)


# MIM caps, keyed like the deck (cap_derivations.lvs): MIM between TopMetal1 and Metal5, rfcmim when
# PWellblock covers it, never under IND/INDpin. w/l are the MIM extents (deck `calc_cmim_params`):
# cmim w = x, l = y; rfcmim swaps them (l = x, w = y).
# cmim CONFIDENCE: HIGH; rfcmim CONFIDENCE: MEDIUM (the PCell is flattened, so gflvs sees its cmim core)
# TODO(https://github.com/gdsfactory/IHP/issues/302): the PCell draws MIM 0.72 um larger than its width/length arguments (P4).
def _mim(name: str, seed: LayerOperation) -> DeviceTemplate:
    terms = [
        pin("PLUS", TopMetal1 & seed),
        # the MINUS port sits on the Metal5 overhang outside MIM
        pin("MINUS", Metal5 & grow(seed, CAP_PLATE_REACH)),
    ]
    if name == "rfcmim":
        terms.append(pin("TIE_LOW", Metal1 & Activ & pSD & grow(seed, CAP_TIE_REACH)))
    return tpl(
        name,
        terms,
        [
            par("width", seed),
            par("length", seed),
            par(
                "glue",
                grow(seed, CAP_TIE_REACH if name == "rfcmim" else CAP_PLATE_REACH),
            ),
        ],
    )


_mim_seed = MIM - IND - INDpin
CAPACITOR_TEMPLATES = _extract(
    [_mim("cmim", _mim_seed - PWellblock)], width=dx_max, length=dy_max
) + _extract([_mim("rfcmim", _mim_seed & PWellblock)], width=dy_max, length=dx_max)


# MOM caps: two interdigitated combs under MemCap, drawn on every metal from botmetal to topmetal and
# unioned here into one comb pair. In the PCell frame the 2 * nfingers + 1 fingers run along y, each comb
# a finger set plus its pad bar; PLUS is the top comb, MINUS the bottom one. Parameters are the PCell's
# arguments, metals numbered 1-5 (Metal1-Metal5). MIM caps draw MemCap too: their plates and tie rings
# (within CAP_TIE_REACH of the MIM) are cut out.
# CONFIDENCE: MEDIUM (measured on the PCell; official layouts untested)
MOM_METAL_NUMBERS: dict[LayerKey, int] = {
    _key(getattr(LAYER, f"Metal{number}drawing")): number for number in range(1, 6)
}
MOM_FINGER_PROBE = 0.001  # height of the strip cut across the fingers at mid-length
_mom = (Metal1 | Metal2 | Metal3 | Metal4 | Metal5) & (
    MemCap - grow(MIM, CAP_TIE_REACH)
)


def _mom_finger_boxes(polys: list[gdstk.Polygon]) -> list[Any]:
    """Finger cross-sections at the combs' mid-height, left to right."""
    (x_min, y_min), (x_max, y_max) = gdstk.Cell("mom").add(*polys).bounding_box()
    y_mid = (y_min + y_max) / 2
    strip = gdstk.rectangle(
        (x_min, y_mid - MOM_FINGER_PROBE), (x_max, y_mid + MOM_FINGER_PROBE)
    )
    return sorted(
        (cut.bounding_box() for cut in gdstk.boolean(polys, strip, "and")),
        key=lambda box: box[0][0],
    )


def mom_nfingers(polys: list[gdstk.Polygon]) -> float:
    """PCell nfingers: the combs draw 2 * nfingers + 1 fingers."""
    return (len(_mom_finger_boxes(polys)) - 1) / 2


def mom_spacing(polys: list[gdstk.Polygon]) -> float:
    """Gap between neighbouring fingers; NaN (a bound error in gflvs) without two fingers."""
    boxes = _mom_finger_boxes(polys)
    return float(
        min(
            (right[0][0] - left[1][0] for left, right in pairwise(boxes)),
            default=float("nan"),
        )
    )


def mom_length(polys: list[gdstk.Polygon]) -> float:
    """Finger length: each comb is length + bar tall, the pair length + spacing + 2 bars."""
    comb_height = dy_max(polys)
    (_, y_min), (_, y_max) = gdstk.Cell("mom").add(*polys).bounding_box()
    return 2 * comb_height - (y_max - y_min) + mom_spacing(polys)


def _mom_metals(
    polys: list[gdstk.Polygon], geometry_by_layer: dict[LayerKey, list[gdstk.Polygon]]
) -> list[int]:
    (x_min, y_min), (x_max, y_max) = gdstk.Cell("mom").add(*polys).bounding_box()
    return sorted(
        number
        for layer, number in MOM_METAL_NUMBERS.items()
        if any(
            (box := polygon.bounding_box())[0][0] < x_max
            and box[1][0] > x_min
            and box[0][1] < y_max
            and box[1][1] > y_min
            for polygon in geometry_by_layer.get(layer, ())
        )
    )


def mom_botmetal(
    polys: list[gdstk.Polygon], geometry_by_layer: dict[LayerKey, list[gdstk.Polygon]]
) -> float:
    """Lowest metal (1-5) drawn inside the combs."""
    return float(_mom_metals(polys, geometry_by_layer)[0])


def mom_topmetal(
    polys: list[gdstk.Polygon], geometry_by_layer: dict[LayerKey, list[gdstk.Polygon]]
) -> float:
    """Highest metal (1-5) drawn inside the combs."""
    return float(_mom_metals(polys, geometry_by_layer)[-1])


CAPACITOR_TEMPLATES += _extract(
    [
        tpl(
            "cmom",
            [pin("MINUS/PLUS", _mom)],
            [
                par(name, _mom)
                for name in ("nfingers", "length", "spacing", "botmetal", "topmetal")
            ],
        )
    ],
    nfingers=mom_nfingers,
    length=mom_length,
    spacing=mom_spacing,
    botmetal=mom_botmetal,
    topmetal=mom_topmetal,
)


# svaricap, keyed like the deck's varicap_core: an n-gate (Activ & GatPoly, no pSD) inside NWell.
# Our PCell also draws Varicap; official layouts draw nBuLay instead. G = left pad, B = right pad (Metal1).
# CONFIDENCE: LOW
# TODO(https://github.com/gdsfactory/IHP/issues/302): pads don't touch the contacts, the gate has no contact, and ports (G, B)
# don't match the SPICE pins (G1, W, G2, BN); no 63/0 "SVaricap" text, so the deck skips it (P3).
# TODO(gflvs): the deck measures on the 63/0 "SVaricap" text region; gflvs can't key on text.
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


# ESD clamp, keyed like the deck's nmoscl (esd_derivations.lvs): gates inside Recogesd. ESD diodes have
# Recogesd but no gate. PAD on Metal2 (-> VDD), GND on Metal1 (-> VSS).
# CONFIDENCE: LOW (length not drawn)
# TODO(https://github.com/gdsfactory/IHP/issues/302): GatPoly covers all of Activ, one Metal1 spans S and D, and the Metal2 PAD has no Via1;
# no 63/0 "nmoscl_2" text, so the deck skips it (P3).
# TODO(gflvs): the deck tells nmoscl_2/_4 apart by a 63/0 text; gflvs can't key on text.
_esd_gate = Activ & GatPoly & Recogesd
ESD_TEMPLATES = _extract(
    [
        tpl(
            "esd_nmos",
            [
                pin("PAD", Metal2 & Recogesd & grow(_esd_gate, ESD_REACH)),
                pin("GND", Metal1 & Recogesd & grow(_esd_gate, ESD_REACH)),
            ],
            [
                par("width", _esd_gate),
                par("nf", _esd_gate),
                par("glue", grow(_esd_gate, ESD_REACH)),
            ],
        )
    ],
    width=dy_sum,
)


# Inductors: pins are TopMetal1/TopMetal2 & INDpin & IND.
# inductor2 CONFIDENCE: LOW (turns=1 only); inductor3 CONFIDENCE: MEDIUM
# TODO(https://github.com/gdsfactory/IHP/issues/302): inductor2(turns=2) draws the same three-port geometry as inductor3 and is classified as it.
# TODO(https://github.com/gdsfactory/IHP/issues/302): our inductor2 puts its ports on TopMetal2; the deck's are on TopMetal1 (LA/LB), and
# neither PCell draws the 27/25 LA/LB/LC port texts (P3).
# TODO(gflvs): the deck tells inductor2 from inductor3 by those texts; gflvs can't key on text, so official
# inductor3 layouts also match inductor2 (R3, not fixed).
_tm1_pins = TopMetal1 & INDpin & IND
_ind2_pins = (TopMetal2 & INDpin & IND) - grow(_tm1_pins, IND_TAP_REACH)
# inductor2 is fitted to its PCell (gflvs waveguide device extraction): width, space and diameter are
# searched within their bounds until the PCell's TopMetal2 matches the drawn spiral; its P1/P2 pin op
# names the terminals.
INDUCTOR2_FIT_BOUNDS = {
    "width": (2.0, 30.0),
    "space": (2.1, 10.0),
    "diameter": (15.0, 500.0),
}
INDUCTOR2_FIT_LAYERS: frozenset[LayerKey] = frozenset({_key(LAYER.TopMetal2drawing)})
FIT_GRID_UM = 0.001  # fitted PCell arguments snap to the database grid


def generate_inductor2(width: float, space: float, diameter: float) -> gdstk.Cell:
    """One-turn inductor2 as a flat gdstk cell, its arguments snapped to the grid."""
    # ponytail: every distinct argument set adds a cached PCell to the layout; bounded by the fit's evaluations
    component = inductor2(
        **{
            name: round(value / FIT_GRID_UM) * FIT_GRID_UM
            for name, value in {
                "width": width,
                "space": space,
                "diameter": diameter,
            }.items()
        },
        turns=1,
    )
    cell = gdstk.Cell("inductor2_fit")
    for (layer, datatype), points in component.get_polygons_points(by="tuple").items():
        cell.add(*(gdstk.Polygon(p, layer=layer, datatype=datatype) for p in points))
    return cell


PCELL_GENERATORS: dict[str, Callable[..., gdstk.Cell]] = {
    "inductor2": generate_inductor2
}

INDUCTOR_TEMPLATES = [
    tpl(
        "inductor2",
        [pin("P1/P2", _ind2_pins)],
        [
            DeviceParameterTemplate(
                name=name, param_bound_min=low, param_bound_max=high
            )
            for name, (low, high) in INDUCTOR2_FIT_BOUNDS.items()
        ],
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


# Antenna diodes, keyed like the deck's antenna_d_mk: Recogdiode minus `antenna_d_exc` (schottky draws
# nSDblock/SalBlock/PWellblock, ESD diodes draw Recogesd). No ports in the PCells; terminal named by SPICE
# pin, the other pin is the implicit substrate (dantenna) or well (dpantenna).
# CONFIDENCE: MEDIUM
_antenna = _minus(
    Activ & Recogdiode,
    *(PWellblock, SalBlock, nSDblock, GatPoly, nSD, TRANS, EmWind, EmWiHV, PolyRes),
    *(EXTBlock, RES, Activmask, Recogesd, IND, INDpin, Substrate),
)
_dn = _antenna - pSD - NWell
_dp = _antenna & pSD & NWell
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
    # the deck keys MOS on the gate itself (Activ & GatPoly), not on HeatTrans; std cells draw no marker
    | {"nmos", "pmos", "nmos_hv", "pmos_hv"}
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


# the default-enabled templates (DEFAULT_LVS_CONFIG's)
DEVICE_TEMPLATES: list[DeviceTemplate] = [
    t for on, group in _groups() if on for t in group
]


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
        # TODO(gflvs): no substrate net (R6). The deck puts bulk/BN/TIE on one substrate net; here
        # `net_to_layer_op_map` stays empty because no template has a bulk terminal to hang on it.
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
        waveguide_device_extraction_config=WaveguideDeviceExtractionConfig(
            pcell_generators={
                name: generator
                for name, generator in PCELL_GENERATORS.items()
                if any(t.device_class_name == name for t in templates)
            },
            waveguide_layers=INDUCTOR2_FIT_LAYERS,
            # extraction runs in the device cell's own frame, where a PCell is never rotated
            rotation_bounds_degrees=(0.0, 0.0),
            # the inductor PCells snap width and diameter to 0.01 um: report the fit on that grid
            parameter_decimal_places=2,
        ),
        parameter_relative_tolerance=PARAMETER_RELATIVE_TOLERANCE,
        run_mode=LvsRunMode.LVS_RUN_MODE_HIERARCHICAL
        if HIERARCHICAL_RUN
        else LvsRunMode.LVS_RUN_MODE_FLAT,
        verbose=1 if VERBOSE else 0,
    )


DEFAULT_LVS_CONFIG = build_lvs_config()
