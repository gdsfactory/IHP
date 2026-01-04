"""IHP PDK Technology definitions.

- LayerMap with IHP PDK layers
- LayerStack for 3D representation
- Cross-sections for routing
- Technology parameters
"""

import sys
from functools import partial
from typing import Any

import gdsfactory as gf
from doroutes.bundles import add_bundle_astar
from gdsfactory import typings
from gdsfactory.component import Component
from gdsfactory.cross_section import (
    CrossSection,
    get_cross_sections,
    port_names_electrical,
    port_types_electrical,
    xsection,
)
from gdsfactory.technology import LayerLevel, LayerMap, LayerStack
from gdsfactory.typings import Layer, LayerSpec
from pydantic import BaseModel

# Import CNI tech for cells2 compatibility
from cni.tech import Tech as _CNITech
from ihp.config import PATH

nm = 1e-3
pin_length = 10 * nm
heater_width = 4


class LayerMapIHP(LayerMap):
    ActivOPC: Layer = (1, 26)
    Activboundary: Layer = (1, 4)
    Activdrawing: Layer = (1, 0)
    Activfiller: Layer = (1, 22)
    ActiviOPC: Layer = (1, 27)
    Activlabel: Layer = (1, 1)
    Activlvs: Layer = (1, 19)
    Activmask: Layer = (1, 20)
    Activnet: Layer = (1, 3)
    Activnofill: Layer = (1, 23)
    Activnoqrc: Layer = (1, 28)
    Activpin: Layer = (1, 2)
    AlCuStopdrawing: Layer = (159, 0)
    AntMetal1drawing: Layer = (132, 0)
    AntMetal2drawing: Layer = (84, 0)
    AntVia1drawing: Layer = (83, 0)
    BackMetal1OPC: Layer = (20, 26)
    BackMetal1boundary: Layer = (20, 4)
    BackMetal1diffprb: Layer = (20, 34)
    BackMetal1drawing: Layer = (20, 0)
    BackMetal1filler: Layer = (20, 22)
    BackMetal1iprobe: Layer = (20, 33)
    BackMetal1label: Layer = (20, 1)
    BackMetal1mask: Layer = (20, 20)
    BackMetal1net: Layer = (20, 3)
    BackMetal1nofill: Layer = (20, 23)
    BackMetal1noqrc: Layer = (20, 28)
    BackMetal1pin: Layer = (20, 2)
    BackMetal1res: Layer = (20, 29)
    BackMetal1slit: Layer = (20, 24)
    BackMetal1text: Layer = (20, 25)
    BackPassivdrawing: Layer = (23, 0)
    BasPolyboundary: Layer = (13, 4)
    BasPolydrawing: Layer = (13, 0)
    BasPolylabel: Layer = (13, 1)
    BasPolynet: Layer = (13, 3)
    BasPolypin: Layer = (13, 2)
    BiWindOPC: Layer = (3, 26)
    BiWinddrawing: Layer = (3, 0)
    ColOpendrawing: Layer = (101, 0)
    ColWinddrawing: Layer = (139, 0)
    ContOPC: Layer = (6, 26)
    Contboundary: Layer = (6, 4)
    Contdrawing: Layer = (6, 0)
    Contnet: Layer = (6, 3)
    CtrGatdrawing: Layer = (154, 0)
    DeepCodrawing: Layer = (35, 0)
    DeepViadrawing: Layer = (152, 0)
    DevBondMetdrawing: Layer = (75, 0)
    DevBondViadrawing: Layer = (74, 0)
    DevTrenchdrawing: Layer = (76, 0)
    DigiBnddrawing: Layer = (16, 0)
    DigiBnddrawing0: Layer = (16, 10)
    DigiSubdrawing: Layer = (60, 0)
    EXTBlockdrawing: Layer = (111, 0)
    EdgeSealboundary: Layer = (39, 4)
    EdgeSealdrawing: Layer = (39, 0)
    EmPolydrawing: Layer = (55, 0)
    EmWiHV3drawing: Layer = (91, 0)
    EmWiHVdrawing: Layer = (156, 0)
    EmWind3drawing: Layer = (90, 0)
    EmWindOPC: Layer = (33, 26)
    EmWinddrawing: Layer = (33, 0)
    Exchange0drawing: Layer = (190, 0)
    Exchange0label: Layer = (190, 1)
    Exchange0pin: Layer = (190, 2)
    Exchange0text: Layer = (190, 25)
    Exchange1drawing: Layer = (191, 0)
    Exchange1label: Layer = (191, 1)
    Exchange1pin: Layer = (191, 2)
    Exchange1text: Layer = (191, 25)
    Exchange2drawing: Layer = (192, 0)
    Exchange2label: Layer = (192, 1)
    Exchange2pin: Layer = (192, 2)
    Exchange2text: Layer = (192, 25)
    Exchange3drawing: Layer = (193, 0)
    Exchange3label: Layer = (193, 1)
    Exchange3pin: Layer = (193, 2)
    Exchange3text: Layer = (193, 25)
    Exchange4drawing: Layer = (194, 0)
    Exchange4label: Layer = (194, 1)
    Exchange4pin: Layer = (194, 2)
    Exchange4text: Layer = (194, 25)
    FBEdrawing: Layer = (54, 0)
    FGEtchdrawing: Layer = (153, 0)
    FGImpdrawing: Layer = (155, 0)
    FLMdrawing: Layer = (142, 0)
    GatPolyOPC: Layer = (5, 26)
    GatPolyboundary: Layer = (5, 4)
    GatPolydrawing: Layer = (5, 0)
    GatPolyfiller: Layer = (5, 22)
    GatPolyiOPC: Layer = (5, 27)
    GatPolylabel: Layer = (5, 1)
    GatPolynet: Layer = (5, 3)
    GatPolynofill: Layer = (5, 23)
    GatPolynoqrc: Layer = (5, 28)
    GatPolypin: Layer = (5, 2)
    GraphBotdrawing: Layer = (78, 0)
    GraphContdrawing: Layer = (85, 0)
    GraphGatedrawing: Layer = (118, 0)
    GraphMet1LOPC: Layer = (110, 26)
    GraphMet1Ldrawing: Layer = (110, 0)
    GraphMet1Lfiller: Layer = (110, 22)
    GraphMet1Lnofill: Layer = (110, 23)
    GraphMet1Lslit: Layer = (110, 24)
    GraphMetal1OPC: Layer = (109, 26)
    GraphMetal1drawing: Layer = (109, 0)
    GraphMetal1filler: Layer = (109, 22)
    GraphMetal1nofill: Layer = (109, 23)
    GraphMetal1slit: Layer = (109, 24)
    GraphPaddrawing: Layer = (97, 0)
    GraphPasdrawing: Layer = (89, 0)
    GraphTopdrawing: Layer = (79, 0)
    HafniumOxdrawing: Layer = (143, 0)
    HeatResdrawing: Layer = (52, 0)
    HeatTransdrawing: Layer = (51, 0)
    ICdrawing: Layer = (48, 0)
    INDboundary: Layer = (27, 4)
    INDdrawing: Layer = (27, 0)
    INDpin: Layer = (27, 2)
    INDtext: Layer = (27, 25)
    INLDPWLdrawing: Layer = (127, 0)
    IntBondMetdrawing: Layer = (73, 0)
    IntBondViadrawing: Layer = (72, 0)
    LBEdrawing: Layer = (157, 0)
    MEMPADdrawing: Layer = (124, 0)
    MEMViadrawing: Layer = (145, 0)
    MIMboundary: Layer = (36, 4)
    MIMdrawing: Layer = (36, 0)
    MIMnet: Layer = (36, 3)
    MemCapdrawing: Layer = (69, 0)
    Metal1OPC: Layer = (8, 26)
    Metal1boundary: Layer = (8, 4)
    Metal1diffprb: Layer = (8, 34)
    Metal1drawing: Layer = (8, 0)
    Metal1filler: Layer = (8, 22)
    Metal1iprobe: Layer = (8, 33)
    Metal1label: Layer = (8, 1)
    Metal1mask: Layer = (8, 20)
    Metal1net: Layer = (8, 3)
    Metal1nofill: Layer = (8, 23)
    Metal1noqrc: Layer = (8, 28)
    Metal1pin: Layer = (8, 2)
    Metal1res: Layer = (8, 29)
    Metal1slit: Layer = (8, 24)
    Metal1text: Layer = (8, 25)
    Metal2OPC: Layer = (10, 26)
    Metal2boundary: Layer = (10, 4)
    Metal2diffprb: Layer = (10, 34)
    Metal2drawing: Layer = (10, 0)
    Metal2filler: Layer = (10, 22)
    Metal2iprobe: Layer = (10, 33)
    Metal2label: Layer = (10, 1)
    Metal2mask: Layer = (10, 20)
    Metal2net: Layer = (10, 3)
    Metal2nofill: Layer = (10, 23)
    Metal2noqrc: Layer = (10, 28)
    Metal2pin: Layer = (10, 2)
    Metal2res: Layer = (10, 29)
    Metal2slit: Layer = (10, 24)
    Metal2text: Layer = (10, 25)
    Metal3OPC: Layer = (30, 26)
    Metal3boundary: Layer = (30, 4)
    Metal3diffprb: Layer = (30, 34)
    Metal3drawing: Layer = (30, 0)
    Metal3filler: Layer = (30, 22)
    Metal3iprobe: Layer = (30, 33)
    Metal3label: Layer = (30, 1)
    Metal3mask: Layer = (30, 20)
    Metal3net: Layer = (30, 3)
    Metal3nofill: Layer = (30, 23)
    Metal3noqrc: Layer = (30, 28)
    Metal3pin: Layer = (30, 2)
    Metal3res: Layer = (30, 29)
    Metal3slit: Layer = (30, 24)
    Metal3text: Layer = (30, 25)
    Metal4OPC: Layer = (50, 26)
    Metal4boundary: Layer = (50, 4)
    Metal4diffprb: Layer = (50, 34)
    Metal4drawing: Layer = (50, 0)
    Metal4filler: Layer = (50, 22)
    Metal4iprobe: Layer = (50, 33)
    Metal4label: Layer = (50, 1)
    Metal4mask: Layer = (50, 20)
    Metal4net: Layer = (50, 3)
    Metal4nofill: Layer = (50, 23)
    Metal4noqrc: Layer = (50, 28)
    Metal4pin: Layer = (50, 2)
    Metal4res: Layer = (50, 29)
    Metal4slit: Layer = (50, 24)
    Metal4text: Layer = (50, 25)
    Metal5OPC: Layer = (67, 26)
    Metal5boundary: Layer = (67, 4)
    Metal5diffprb: Layer = (67, 34)
    Metal5drawing: Layer = (67, 0)
    Metal5filler: Layer = (67, 22)
    Metal5iprobe: Layer = (67, 33)
    Metal5label: Layer = (67, 1)
    Metal5mask: Layer = (67, 20)
    Metal5net: Layer = (67, 3)
    Metal5nofill: Layer = (67, 23)
    Metal5noqrc: Layer = (67, 28)
    Metal5pin: Layer = (67, 2)
    Metal5res: Layer = (67, 29)
    Metal5slit: Layer = (67, 24)
    Metal5text: Layer = (67, 25)
    NExtHVdrawing: Layer = (116, 0)
    NExtdrawing: Layer = (114, 0)
    NLDBdrawing: Layer = (15, 0)
    NLDDdrawing: Layer = (112, 0)
    NWellboundary: Layer = (31, 4)
    NWelldrawing: Layer = (31, 0)
    NWelllabel: Layer = (31, 1)
    NWellnet: Layer = (31, 3)
    NWellpin: Layer = (31, 2)
    NoDRCdrawing: Layer = (62, 0)
    NoMetFillerdrawing: Layer = (160, 0)
    NoRCXdrawing: Layer = (148, 0)
    NoRCXm1sub: Layer = (148, 123)
    NoRCXm2m3: Layer = (148, 41)
    NoRCXm2m4: Layer = (148, 42)
    NoRCXm2m5: Layer = (148, 43)
    NoRCXm2sub: Layer = (148, 124)
    NoRCXm2tm1: Layer = (148, 44)
    NoRCXm2tm2: Layer = (148, 45)
    NoRCXm3m4: Layer = (148, 46)
    NoRCXm3m5: Layer = (148, 47)
    NoRCXm3sub: Layer = (148, 125)
    NoRCXm3tm1: Layer = (148, 48)
    NoRCXm3tm2: Layer = (148, 49)
    NoRCXm4m5: Layer = (148, 50)
    NoRCXm4sub: Layer = (148, 126)
    NoRCXm4tm1: Layer = (148, 51)
    NoRCXm4tm2: Layer = (148, 52)
    NoRCXm5sub: Layer = (148, 127)
    NoRCXm5tm1: Layer = (148, 53)
    NoRCXm5tm2: Layer = (148, 54)
    NoRCXtm1sub: Layer = (148, 300)
    NoRCXtm1tm2: Layer = (148, 55)
    NoRCXtm2sub: Layer = (148, 301)
    PExtHVdrawing: Layer = (117, 0)
    PExtdrawing: Layer = (115, 0)
    PLDBdrawing: Layer = (45, 0)
    PLDDdrawing: Layer = (113, 0)
    PWellblock: Layer = (46, 21)
    PWellboundary: Layer = (46, 4)
    PWelldrawing: Layer = (46, 0)
    PWelllabel: Layer = (46, 1)
    PWellnet: Layer = (46, 3)
    PWellpin: Layer = (46, 2)
    Passivboundary: Layer = (9, 4)
    Passivdrawing: Layer = (9, 0)
    Passivlabel: Layer = (9, 1)
    Passivnet: Layer = (9, 3)
    Passivpdl: Layer = (9, 40)
    Passivpillar: Layer = (9, 35)
    Passivpin: Layer = (9, 2)
    Passivsbump: Layer = (9, 36)
    Polimidedrawing: Layer = (98, 0)
    Polimidelabel: Layer = (98, 1)
    Polimidenet: Layer = (98, 3)
    Polimidepin: Layer = (98, 2)
    PolyResboundary: Layer = (128, 4)
    PolyResdrawing: Layer = (128, 0)
    PolyReslabel: Layer = (128, 1)
    PolyResnet: Layer = (128, 3)
    PolyRespin: Layer = (128, 2)
    RESdrawing: Layer = (24, 0)
    RESlabel: Layer = (24, 1)
    RFMEMdrawing: Layer = (147, 0)
    RadHarddrawing: Layer = (68, 0)
    Recogdiffprb: Layer = (99, 34)
    Recogdiode: Layer = (99, 31)
    Recogdrawing: Layer = (99, 0)
    Recogesd: Layer = (99, 30)
    Recogiprobe: Layer = (99, 33)
    Recogmom: Layer = (99, 39)
    Recogotp: Layer = (99, 37)
    Recogpcm: Layer = (99, 100)
    Recogpdiode: Layer = (99, 38)
    Recogpillar: Layer = (99, 35)
    Recogpin: Layer = (99, 2)
    Recogsbump: Layer = (99, 36)
    Recogtsv: Layer = (99, 32)
    RedBuLaydrawing: Layer = (92, 0)
    Redistdrawing: Layer = (77, 0)
    SMOSdrawing: Layer = (93, 0)
    SNSArmsdrawing: Layer = (137, 0)
    SNSBotViadrawing: Layer = (149, 0)
    SNSCMOSViadrawing: Layer = (138, 0)
    SNSRingdrawing: Layer = (135, 0)
    SNSTopViadrawing: Layer = (151, 0)
    SRAMboundary: Layer = (25, 4)
    SRAMdrawing: Layer = (25, 0)
    SRAMlabel: Layer = (25, 1)
    SalBlockdrawing: Layer = (28, 0)
    Sensordrawing: Layer = (136, 0)
    SiGratingdrawing: Layer = (87, 0)
    SiNGratingdrawing: Layer = (88, 0)
    SiNWGdrawing: Layer = (119, 0)
    SiNWGfiller: Layer = (119, 22)
    SiNWGnofill: Layer = (119, 23)
    SiWGdrawing: Layer = (86, 0)
    SiWGfiller: Layer = (86, 22)
    SiWGnofill: Layer = (86, 23)
    Substratedrawing: Layer = (40, 0)
    Substratetext: Layer = (40, 25)
    TEXTdrawing: Layer = (63, 0)
    TRANSdrawing: Layer = (26, 0)
    ThickGateOxdrawing: Layer = (44, 0)
    ThinFilmResdrawing: Layer = (146, 0)
    TopMetal1boundary: Layer = (126, 4)
    TopMetal1diffprb: Layer = (126, 34)
    TopMetal1drawing: Layer = (126, 0)
    TopMetal1filler: Layer = (126, 22)
    TopMetal1iprobe: Layer = (126, 33)
    TopMetal1label: Layer = (126, 1)
    TopMetal1mask: Layer = (126, 20)
    TopMetal1net: Layer = (126, 3)
    TopMetal1nofill: Layer = (126, 23)
    TopMetal1noqrc: Layer = (126, 28)
    TopMetal1pin: Layer = (126, 2)
    TopMetal1res: Layer = (126, 29)
    TopMetal1slit: Layer = (126, 24)
    TopMetal1text: Layer = (126, 25)
    TopMetal2boundary: Layer = (134, 4)
    TopMetal2diffprb: Layer = (134, 34)
    TopMetal2drawing: Layer = (134, 0)
    TopMetal2filler: Layer = (134, 22)
    TopMetal2iprobe: Layer = (134, 33)
    TopMetal2label: Layer = (134, 1)
    TopMetal2mask: Layer = (134, 20)
    TopMetal2net: Layer = (134, 3)
    TopMetal2nofill: Layer = (134, 23)
    TopMetal2noqrc: Layer = (134, 28)
    TopMetal2pin: Layer = (134, 2)
    TopMetal2res: Layer = (134, 29)
    TopMetal2slit: Layer = (134, 24)
    TopMetal2text: Layer = (134, 25)
    TopVia1boundary: Layer = (125, 4)
    TopVia1drawing: Layer = (125, 0)
    TopVia1net: Layer = (125, 3)
    TopVia2boundary: Layer = (133, 4)
    TopVia2drawing: Layer = (133, 0)
    TopVia2net: Layer = (133, 3)
    Varicapdrawing: Layer = (70, 0)
    Via1boundary: Layer = (19, 4)
    Via1drawing: Layer = (19, 0)
    Via1net: Layer = (19, 3)
    Via2boundary: Layer = (29, 4)
    Via2drawing: Layer = (29, 0)
    Via2net: Layer = (29, 3)
    Via3boundary: Layer = (49, 4)
    Via3drawing: Layer = (49, 0)
    Via3net: Layer = (49, 3)
    Via4boundary: Layer = (66, 4)
    Via4drawing: Layer = (66, 0)
    Via4net: Layer = (66, 3)
    Vmimdrawing: Layer = (129, 0)
    dfpaddrawing: Layer = (41, 0)
    dfpadpillar: Layer = (41, 35)
    dfpadsbump: Layer = (41, 36)
    isoNWelldrawing: Layer = (257, 0)
    nBuLayCutdrawing: Layer = (131, 0)
    nBuLayblock: Layer = (32, 21)
    nBuLayboundary: Layer = (32, 4)
    nBuLaydrawing: Layer = (32, 0)
    nBuLaylabel: Layer = (32, 1)
    nBuLaynet: Layer = (32, 3)
    nBuLaypin: Layer = (32, 2)
    nSDblock: Layer = (7, 21)
    nSDdrawing: Layer = (7, 0)
    pSDdrawing: Layer = (14, 0)
    prBoundaryboundary: Layer = (189, 4)
    prBoundarydrawing: Layer = (189, 0)
    prBoundarylabel: Layer = (189, 1)


LAYER = LayerMapIHP


def add_labels_to_ports_optical(
    component: Component,
    label_layer: LayerSpec = LAYER.TEXTdrawing,
    port_type: str | None = "optical",
    **kwargs,
) -> Component:
    """Add labels to component ports.

    Args:
        component: to add labels.
        label_layer: layer spec for the label.
        port_type: to select ports.

    keyword Args:
        layer: select ports with GDS layer.
        prefix: select ports with prefix in port name.
        orientation: select ports with orientation in degrees.
        width: select ports with port width.
        layers_excluded: List of layers to exclude.
        port_type: select ports with port_type (optical, electrical, vertical_te).
        clockwise: if True, sort ports clockwise, False: counter-clockwise.
    """
    suffix = "o3_0" if len(component.ports) == 4 else "o2_0"
    ports = component.ports.filter(port_type=port_type, suffix=suffix, **kwargs)
    for port in ports:
        component.add_label(text=port.name, position=port.center, layer=label_layer)

    return component


margin = 0.5


def get_layer_stack(
    thickness_active: float = 0.40,  # Active/STI thickness (400 nm from process specs)
    thickness_poly: float = 0.16,  # Gate polysilicon thickness (160 nm from process specs)
    thickness_contact: float = 0.64,  # Contact thickness (640 nm from process specs)
    thickness_metal1: float = 0.42,  # Metal1 thickness (420 nm from process specs)
    thickness_metal: float = 0.49,  # Metal2-5 thickness (490 nm from process specs)
    thickness_via1: float = 0.54,  # Via1 thickness (540 nm from process specs)
    thickness_via: float = 0.54,  # Via2-4 thickness (540 nm from process specs)
    thickness_topvia1: float = 0.85,  # TopVia1 thickness (850 nm from process specs)
    thickness_topmetal1: float = 2.0,  # TopMetal1 thickness (2000 nm from process specs)
    thickness_topvia2: float = 2.8,  # TopVia2 thickness (2800 nm from process specs)
    thickness_topmetal2: float = 3.0,  # TopMetal2 thickness (3000 nm from process specs)
    thickness_mim: float = 0.15,  # MIM capacitor top plate thickness (150 nm)
    thickness_passivation: float = 1.9,  # Passivation thickness (1500 + 400 nm)
    substrate_thickness: float = 300.0,  # Full substrate
) -> LayerStack:
    """Returns IHP PDK LayerStack for 3D visualization and simulation.

    Layer thicknesses are based on the IHP SG13 process specifications.
    Reference: https://ihp-open-pdk-docs.readthedocs.io/en/latest/process_specs/02_process_control_params.html

    Args:
        thickness_active: Active/STI layer thickness in um (default: 0.40).
        thickness_poly: Gate polysilicon thickness in um (default: 0.16).
        thickness_contact: Contact layer thickness in um (default: 0.64).
        thickness_metal1: Metal1 layer thickness in um (default: 0.42).
        thickness_metal: Metal2-5 layer thickness in um (default: 0.49).
        thickness_via1: Via1 layer thickness in um (default: 0.54).
        thickness_via: Via2-4 layer thickness in um (default: 0.54).
        thickness_topvia1: TopVia1 layer thickness in um (default: 0.85).
        thickness_topmetal1: TopMetal1 layer thickness in um (default: 2.0).
        thickness_topvia2: TopVia2 layer thickness in um (default: 2.8).
        thickness_topmetal2: TopMetal2 layer thickness in um (default: 3.0).
        thickness_mim: MIM capacitor top plate thickness in um (default: 0.15).
        thickness_passivation: Passivation layer thickness in um (default: 1.9).
        substrate_thickness: Substrate thickness in um (default: 300.0).

    Returns:
        LayerStack for IHP PDK with properly connected metal and via layers.
    """

    return LayerStack(
        layers=dict(
            # Substrate
            substrate=LayerLevel(
                layer=LAYER.Substratedrawing,
                thickness=substrate_thickness,
                zmin=-substrate_thickness,
                material="si",
                info={"mesh_order": 99},
            ),
            # Active silicon (STI region)
            active=LayerLevel(
                layer=LAYER.Activdrawing,
                thickness=thickness_active,
                zmin=0.0,
                material="si",
                info={"mesh_order": 1},
            ),
            # Poly gate
            poly=LayerLevel(
                layer=LAYER.GatPolydrawing,
                thickness=thickness_poly,
                zmin=0.0,
                material="poly_si",
                info={"mesh_order": 2},
            ),
            # Contact (Metal1-Active isolator)
            contact=LayerLevel(
                layer=LAYER.Contdrawing,
                thickness=thickness_contact,
                zmin=thickness_active,
                material="tungsten",
                info={"mesh_order": 3},
            ),
            # Metal 1
            metal1=LayerLevel(
                layer=LAYER.Metal1drawing,
                thickness=thickness_metal1,
                zmin=thickness_active + thickness_contact,
                material="aluminum",
                info={"mesh_order": 4},
            ),
            # Via 1
            via1=LayerLevel(
                layer=LAYER.Via1drawing,
                thickness=thickness_via1,
                zmin=thickness_active + thickness_contact + thickness_metal1,
                material="tungsten",
                info={"mesh_order": 5},
            ),
            # Metal 2
            metal2=LayerLevel(
                layer=LAYER.Metal2drawing,
                thickness=thickness_metal,
                zmin=thickness_active
                + thickness_contact
                + thickness_metal1
                + thickness_via1,
                material="aluminum",
                info={"mesh_order": 6},
            ),
            # Via 2
            via2=LayerLevel(
                layer=LAYER.Via2drawing,
                thickness=thickness_via,
                zmin=thickness_active
                + thickness_contact
                + thickness_metal1
                + thickness_via1
                + thickness_metal,
                material="tungsten",
                info={"mesh_order": 7},
            ),
            # Metal 3
            metal3=LayerLevel(
                layer=LAYER.Metal3drawing,
                thickness=thickness_metal,
                zmin=thickness_active
                + thickness_contact
                + thickness_metal1
                + thickness_via1
                + thickness_metal
                + thickness_via,
                material="aluminum",
                info={"mesh_order": 8},
            ),
            # Via 3
            via3=LayerLevel(
                layer=LAYER.Via3drawing,
                thickness=thickness_via,
                zmin=thickness_active
                + thickness_contact
                + thickness_metal1
                + thickness_via1
                + 2 * thickness_metal
                + thickness_via,
                material="tungsten",
                info={"mesh_order": 9},
            ),
            # Metal 4
            metal4=LayerLevel(
                layer=LAYER.Metal4drawing,
                thickness=thickness_metal,
                zmin=thickness_active
                + thickness_contact
                + thickness_metal1
                + thickness_via1
                + 2 * thickness_metal
                + 2 * thickness_via,
                material="aluminum",
                info={"mesh_order": 10},
            ),
            # Via 4
            via4=LayerLevel(
                layer=LAYER.Via4drawing,
                thickness=thickness_via,
                zmin=thickness_active
                + thickness_contact
                + thickness_metal1
                + thickness_via1
                + 3 * thickness_metal
                + 2 * thickness_via,
                material="tungsten",
                info={"mesh_order": 11},
            ),
            # Metal 5
            metal5=LayerLevel(
                layer=LAYER.Metal5drawing,
                thickness=thickness_metal,
                zmin=thickness_active
                + thickness_contact
                + thickness_metal1
                + thickness_via1
                + 3 * thickness_metal
                + 3 * thickness_via,
                material="aluminum",
                info={"mesh_order": 12},
            ),
            # Top Via 1
            topvia1=LayerLevel(
                layer=LAYER.TopVia1drawing,
                thickness=thickness_topvia1,
                zmin=thickness_active
                + thickness_contact
                + thickness_metal1
                + thickness_via1
                + 4 * thickness_metal
                + 3 * thickness_via,
                material="tungsten",
                info={"mesh_order": 13},
            ),
            # Top Metal 1
            topmetal1=LayerLevel(
                layer=LAYER.TopMetal1drawing,
                thickness=thickness_topmetal1,
                zmin=thickness_active
                + thickness_contact
                + thickness_metal1
                + thickness_via1
                + 4 * thickness_metal
                + 3 * thickness_via
                + thickness_topvia1,
                material="aluminum",
                info={"mesh_order": 14},
            ),
            # Top Via 2
            topvia2=LayerLevel(
                layer=LAYER.TopVia2drawing,
                thickness=thickness_topvia2,
                zmin=thickness_active
                + thickness_contact
                + thickness_metal1
                + thickness_via1
                + 4 * thickness_metal
                + 3 * thickness_via
                + thickness_topvia1
                + thickness_topmetal1,
                material="tungsten",
                info={"mesh_order": 15},
            ),
            # Top Metal 2
            topmetal2=LayerLevel(
                layer=LAYER.TopMetal2drawing,
                thickness=thickness_topmetal2,
                zmin=thickness_active
                + thickness_contact
                + thickness_metal1
                + thickness_via1
                + 4 * thickness_metal
                + 3 * thickness_via
                + thickness_topvia1
                + thickness_topmetal1
                + thickness_topvia2,
                material="aluminum",
                info={"mesh_order": 16},
            ),
            # MIM Capacitor (between Metal5 and TopMetal1)
            mim=LayerLevel(
                layer=LAYER.MIMdrawing,
                thickness=thickness_mim,
                zmin=thickness_active
                + thickness_contact
                + thickness_metal1
                + thickness_via1
                + 4 * thickness_metal
                + 3 * thickness_via
                + 0.02,  # slight offset above Metal5
                material="aluminum",
                info={"mesh_order": 17},
            ),
            # Passivation
            passivation=LayerLevel(
                layer=LAYER.Passivdrawing,
                thickness=thickness_passivation,
                zmin=thickness_active
                + thickness_contact
                + thickness_metal1
                + thickness_via1
                + 4 * thickness_metal
                + 3 * thickness_via
                + thickness_topvia1
                + thickness_topmetal1
                + thickness_topvia2
                + thickness_topmetal2,
                material="oxide",
                info={"mesh_order": 18},
            ),
        )
    )


class TechIHP(BaseModel):
    """IHP PDK Technology parameters."""

    # Grid and precision
    grid: float = 0.005  # 5nm grid
    precision: float = 1e-9

    # Design rules - transistors
    nmos_min_width: float = 0.15
    nmos_min_length: float = 0.13
    pmos_min_width: float = 0.15
    pmos_min_length: float = 0.13

    # Design rules - contacts and vias
    cont_size: float = 0.16
    cont_spacing: float = 0.18
    cont_enc_active: float = 0.07
    cont_enc_poly: float = 0.07
    cont_enc_metal: float = 0.06

    via1_size: float = 0.26
    via1_spacing: float = 0.36
    via1_enc_metal: float = 0.06

    # Design rules - metal
    metal1_width: float = 0.14
    metal1_spacing: float = 0.14
    metal2_width: float = 0.16
    metal2_spacing: float = 0.16
    metal3_width: float = 0.20
    metal3_spacing: float = 0.20
    metal4_width: float = 0.20
    metal4_spacing: float = 0.20
    metal5_width: float = 0.20
    metal5_spacing: float = 0.20
    topmetal1_width: float = 1.0
    topmetal1_spacing: float = 1.0
    topmetal2_width: float = 2.0
    topmetal2_spacing: float = 2.0

    # Design rules - resistors
    rsil_min_width: float = 0.4
    rsil_min_length: float = 0.8
    rsil_sheet_res: float = 7.0  # ohms/square

    rppd_min_width: float = 0.4
    rppd_min_length: float = 0.8
    rppd_sheet_res: float = 300.0  # ohms/square

    rhigh_min_width: float = 1.4
    rhigh_min_length: float = 5.0
    rhigh_sheet_res: float = 1350.0  # ohms/square

    # Design rules - capacitors
    mim_min_size: float = 0.5
    mim_cap_density: float = 1.5  # fF/um^2

    # Design rules - inductors
    inductor_min_width: float = 2.0
    inductor_min_spacing: float = 2.1
    inductor_min_diameter: float = 15.0


TECH = TechIHP()
LAYER_STACK = get_layer_stack()
LAYER_VIEWS = gf.technology.LayerViews(PATH.lyp_yaml)


############################
# Cross-sections functions
############################
cross_section = gf.cross_section.metal1


@xsection
def metal_routing(
    width: float = 1,
    layer: typings.LayerSpec = "M3",
    radius: float | None = None,
    port_names: typings.IOPorts = port_names_electrical,
    port_types: typings.IOPorts = port_types_electrical,
    **kwargs: Any,
) -> CrossSection:
    """Return Metal Strip cross_section."""
    radius = radius or width
    return cross_section(
        width=width,
        layer=layer,
        radius=radius,
        port_names=port_names,
        port_types=port_types,
        **kwargs,
    )


# Metal routing cross-sections
metal1_routing = partial(
    metal_routing,
    layer=LAYER.Metal1drawing,
    width=TECH.metal1_width * 2,
    port_names=gf.cross_section.port_names_electrical,
    port_types=gf.cross_section.port_types_electrical,
    radius=None,
)

metal2_routing = partial(
    metal_routing,
    layer=LAYER.Metal2drawing,
    width=TECH.metal2_width * 2,
    port_names=gf.cross_section.port_names_electrical,
    port_types=gf.cross_section.port_types_electrical,
    radius=None,
)

metal3_routing = partial(
    metal_routing,
    layer=LAYER.Metal3drawing,
    width=TECH.metal3_width * 2,
    port_names=gf.cross_section.port_names_electrical,
    port_types=gf.cross_section.port_types_electrical,
    radius=None,
)

topmetal1_routing = partial(
    metal_routing,
    layer=LAYER.TopMetal1drawing,
    width=TECH.topmetal1_width,
    port_names=gf.cross_section.port_names_electrical,
    port_types=gf.cross_section.port_types_electrical,
    radius=None,
)

topmetal2_routing = partial(
    metal_routing,
    layer=LAYER.TopMetal2drawing,
    width=TECH.topmetal2_width,
    port_names=gf.cross_section.port_names_electrical,
    port_types=gf.cross_section.port_types_electrical,
    radius=None,
)

strip = topmetal2_routing
metal_routing = topmetal2_routing

cross_sections = get_cross_sections(sys.modules[__name__])

############################
# Routing functions
############################

route_bundle = partial(gf.routing.route_bundle, cross_section="strip")
route_bundle_rib = partial(
    route_bundle,
    cross_section="rib",
)
route_bundle_metal = partial(
    route_bundle,
    straight="straight_metal",
    bend="bend_metal",
    taper=None,
    cross_section="metal_routing",
    port_type="electrical",
)
route_bundle_metal_corner = partial(
    route_bundle,
    straight="straight_metal",
    bend="wire_corner",
    taper=None,
    cross_section="metal_routing",
    port_type="electrical",
)

route_astar = partial(
    add_bundle_astar,
    layers=["TOPMETAL2"],
    bend="bend_euler",
    straight="straight",
    grid_unit=500,
    spacing=3,
)

route_astar_metal = partial(
    add_bundle_astar,
    layers=["TOPMETAL2"],
    bend="wire_corner",
    straight="straight_metal",
    grid_unit=500,
    spacing=15,
)


routing_strategies = dict(
    route_bundle=route_bundle,
    route_bundle_rib=route_bundle_rib,
    route_bundle_metal=route_bundle_metal,
    route_bundle_metal_corner=route_bundle_metal_corner,
    route_astar=route_astar,
    route_astar_metal=route_astar_metal,
)

# techParams from CNI layer for cells2 compatibility
techParams = _CNITech.get("SG13_dev").getTechParams()

if __name__ == "__main__":
    LAYER_VIEWS.to_lyp(PATH.lyp)
