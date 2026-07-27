#
# This creates a technology definition example for IHP sg13g2:
#
# See page5 of
# https://github.com/IHP-GmbH/IHP-Open-PDK/blob/main/ihp-sg13g2/libs.doc/doc/SG13G2_os_process_spec.pdf
# and https://github.com/IHP-GmbH/IHP-Open-PDK/blob/main/ihp-sg13g2/libs.tech/openems/testcase/SG13_Octagon_L2n0/OpenEMS_Python/Using%20OpenEMS%20Python%20with%20IHP%20SG13G2%20v1.1.pdf
#

import sys
import warnings

try:
    from gf_pex.techfile import (
        CapacitanceInfo,
        ComputedLayerInfo,
        ComputedLayerKind,
        ConformalDielectricLayer,
        Contact,
        ContactResistance,
        DiffusionLayer,
        FieldOxideLayer,
        GDSPair,
        LayerInfo,
        LayerPurpose,
        LayerResistance,
        MetalLayer,
        NWellLayer,
        OverlapCapacitance,
        ProcessParasiticsInfo,
        ProcessStackInfo,
        ResistanceInfo,
        SideOverlapCapacitance,
        SidewallCapacitance,
        SimpleDielectricLayer,
        StackLayerInfo,
        StackLayerType,
        SubstrateCapacitance,
        SubstrateLayer,
        Techfile,
        ViaResistance,
    )
except ImportError:
    warnings.warn(
        "gf_pex is not installed. Cannot build techfile from gf180mcuD. "
        "Install it with: pip install gf-pex",
        stacklevel=2,
    )
    sys.exit(1)

DNWELL = LayerPurpose.PURPOSE_DNWELL
NWELL = LayerPurpose.PURPOSE_NWELL
PWELL = LayerPurpose.PURPOSE_PWELL
DIFF = LayerPurpose.PURPOSE_DIFF
N_P_TAP = LayerPurpose.PURPOSE_NTAP_OR_PTAP
NTAP = LayerPurpose.PURPOSE_NTAP
PTAP = LayerPurpose.PURPOSE_PTAP
PIMP = LayerPurpose.PURPOSE_P_IMPLANT
NIMP = LayerPurpose.PURPOSE_N_IMPLANT
CONT = LayerPurpose.PURPOSE_CONTACT
METAL = LayerPurpose.PURPOSE_METAL
VIA = LayerPurpose.PURPOSE_VIA
MIM = LayerPurpose.PURPOSE_MIM_CAP

KREG = ComputedLayerKind.KIND_REGULAR
KCAP = ComputedLayerKind.KIND_DEVICE_CAPACITOR
KPIN = ComputedLayerKind.KIND_PIN
KLBL = ComputedLayerKind.KIND_LABEL


def build_layers(tech: Techfile) -> None:
    tech.layers.append(LayerInfo(purpose=DIFF,  name="Activ",     drw_gds_pair=GDSPair(layer=1,   datatype=0), pin_gds_pair=GDSPair(layer=1,   datatype=2),                                           description="Active (diffusion) area"))
    tech.layers.append(LayerInfo(purpose=NWELL, name="NWell",     drw_gds_pair=GDSPair(layer=31,  datatype=0), pin_gds_pair=GDSPair(layer=31,  datatype=2),                                           description="N-well region"))
    tech.layers.append(LayerInfo(purpose=PWELL, name="PWell",     drw_gds_pair=GDSPair(layer=46,  datatype=0), pin_gds_pair=GDSPair(layer=46,  datatype=2),                                           description="P-well region"))
    tech.layers.append(LayerInfo(purpose=NIMP,  name="nSD",       drw_gds_pair=GDSPair(layer=7,   datatype=0),                                                                                        description="Defines areas to receive N+ S/D implant"))
    tech.layers.append(LayerInfo(purpose=PIMP,  name="pSD",       drw_gds_pair=GDSPair(layer=14,  datatype=0),                                                                                        description="Defines areas to receive P+ S/D implant"))
    tech.layers.append(LayerInfo(purpose=METAL, name="GatPoly",   drw_gds_pair=GDSPair(layer=5,   datatype=0), pin_gds_pair=GDSPair(layer=5,   datatype=2), label_gds_pair=GDSPair(layer=5,   datatype=25), description="Poly"))
    tech.layers.append(LayerInfo(purpose=CONT,  name="Cont",      drw_gds_pair=GDSPair(layer=6,   datatype=0),                                                                                        description="Defines 1-st metal contacts to Activ, GatPoly"))
    tech.layers.append(LayerInfo(purpose=METAL, name="Metal1",    drw_gds_pair=GDSPair(layer=8,   datatype=0), pin_gds_pair=GDSPair(layer=8,   datatype=2), label_gds_pair=GDSPair(layer=8,   datatype=25), description="Defines 1-st metal interconnect"))
    tech.layers.append(LayerInfo(purpose=VIA,   name="Via1",      drw_gds_pair=GDSPair(layer=19,  datatype=0),                                                                                        description="Defines 1-st metal to 2-nd metal contact"))
    tech.layers.append(LayerInfo(purpose=METAL, name="Metal2",    drw_gds_pair=GDSPair(layer=10,  datatype=0), pin_gds_pair=GDSPair(layer=10,  datatype=2), label_gds_pair=GDSPair(layer=10,  datatype=25), description="Defines 2-nd metal interconnect"))
    tech.layers.append(LayerInfo(purpose=VIA,   name="Via2",      drw_gds_pair=GDSPair(layer=29,  datatype=0),                                                                                        description="Defines 2-nd metal to 3-rd metal contact"))
    tech.layers.append(LayerInfo(purpose=METAL, name="Metal3",    drw_gds_pair=GDSPair(layer=30,  datatype=0), pin_gds_pair=GDSPair(layer=30,  datatype=2), label_gds_pair=GDSPair(layer=30,  datatype=25), description="Defines 3-rd metal interconnect"))
    tech.layers.append(LayerInfo(purpose=VIA,   name="Via3",      drw_gds_pair=GDSPair(layer=49,  datatype=0),                                                                                        description="Defines 3-rd metal to 4-th metal contact"))
    tech.layers.append(LayerInfo(purpose=METAL, name="Metal4",    drw_gds_pair=GDSPair(layer=50,  datatype=0), pin_gds_pair=GDSPair(layer=50,  datatype=2), label_gds_pair=GDSPair(layer=50,  datatype=25), description="Defines 4-th metal interconnect"))
    tech.layers.append(LayerInfo(purpose=VIA,   name="Via4",      drw_gds_pair=GDSPair(layer=66,  datatype=0),                                                                                        description="Defines 4-th metal to 5-th metal contact"))
    tech.layers.append(LayerInfo(purpose=METAL, name="Metal5",    drw_gds_pair=GDSPair(layer=67,  datatype=0), pin_gds_pair=GDSPair(layer=67,  datatype=2), label_gds_pair=GDSPair(layer=67,  datatype=25), description="Defines 5-th metal interconnect"))
    tech.layers.append(LayerInfo(purpose=VIA,   name="TopVia1",   drw_gds_pair=GDSPair(layer=125, datatype=0),                                                                                        description="Defines 3-rd (or 5-th) metal to TopMetal1 contact"))
    tech.layers.append(LayerInfo(purpose=METAL, name="TopMetal1", drw_gds_pair=GDSPair(layer=126, datatype=0), pin_gds_pair=GDSPair(layer=126, datatype=2), label_gds_pair=GDSPair(layer=126, datatype=25), description="Defines 1-st thick TopMetal layer"))
    tech.layers.append(LayerInfo(purpose=VIA,   name="TopVia2",   drw_gds_pair=GDSPair(layer=133, datatype=0),                                                                                        description="Defines via between TopMetal1 and TopMetal2"))
    tech.layers.append(LayerInfo(purpose=METAL, name="TopMetal2", drw_gds_pair=GDSPair(layer=134, datatype=0), pin_gds_pair=GDSPair(layer=134, datatype=2), label_gds_pair=GDSPair(layer=134, datatype=25), description="Defines 2-nd thick TopMetal layer"))


def build_lvs_computed_layers(tech: Techfile) -> None:
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=PWELL, name="pwell",           description="Computed layer for PWell",                                             drw_gds_pair=GDSPair(layer=46,  datatype=0)),   original_layer_name="PWell"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=PWELL, name="pwell_sub",       description="Computed layer for PWell",                                             drw_gds_pair=GDSPair(layer=46,  datatype=0)),   original_layer_name="PWell"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=NWELL, name="nwell_drw",       description="Computed layer for NWell",                                             drw_gds_pair=GDSPair(layer=31,  datatype=0)),   original_layer_name="NWell"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=NIMP,  name="nsd_fet",         description="Computed layer for nSD",                                               drw_gds_pair=GDSPair(layer=7,   datatype=0)),   original_layer_name="nSD"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=PIMP,  name="psd_fet",         description="Computed layer for pSD",                                               drw_gds_pair=GDSPair(layer=14,  datatype=0)),   original_layer_name="pSD"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=NTAP,  name="ntap",            description="Computed layer for ntap",                                              drw_gds_pair=GDSPair(layer=65,  datatype=144)), original_layer_name="Activ"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=PTAP,  name="ptap",            description="Computed layer for ptap",                                              drw_gds_pair=GDSPair(layer=65,  datatype=244)), original_layer_name="Activ"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=METAL, name="poly_con",        description="Computed layer for GatPoly",                                           drw_gds_pair=GDSPair(layer=5,   datatype=0)),   original_layer_name="GatPoly"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=METAL, name="metal1_con",      description="Computed layer for Metal1",                                            drw_gds_pair=GDSPair(layer=8,   datatype=0)),   original_layer_name="Metal1"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=METAL, name="metal2_con",      description="Computed layer for Metal2",                                            drw_gds_pair=GDSPair(layer=10,  datatype=0)),   original_layer_name="Metal2"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=METAL, name="metal3_con",      description="Computed layer for Metal3",                                            drw_gds_pair=GDSPair(layer=30,  datatype=0)),   original_layer_name="Metal3"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=METAL, name="metal4_con",      description="Computed layer for Metal4",                                            drw_gds_pair=GDSPair(layer=50,  datatype=0)),   original_layer_name="Metal4"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=METAL, name="metal5_n_cap",    description="Computed layer for Metal5 (case where no MiM cap)",                   drw_gds_pair=GDSPair(layer=67,  datatype=0)),   original_layer_name="Metal5"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=METAL, name="topmetal1_con",   description="Computed layer for TopMetal1",                                         drw_gds_pair=GDSPair(layer=126, datatype=0)),   original_layer_name="TopMetal1"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=METAL, name="topmetal2_con",   description="Computed layer for TopMetal2",                                         drw_gds_pair=GDSPair(layer=134, datatype=0)),   original_layer_name="TopMetal2"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=CONT,  name="cont_nsd_con",    description="Computed layer for contact from nSD to Metal1",                        drw_gds_pair=GDSPair(layer=6,   datatype=4401)), original_layer_name="Cont"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=CONT,  name="cont_psd_con",    description="Computed layer for contact from pSD to Metal1",                        drw_gds_pair=GDSPair(layer=6,   datatype=4402)), original_layer_name="Cont"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=CONT,  name="cont_poly_con",   description="Computed layer for contact from GatPoly to Metal1",                    drw_gds_pair=GDSPair(layer=6,   datatype=4403)), original_layer_name="Cont"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=VIA,   name="via1_drw",        description="Computed layer for Via1",                                              drw_gds_pair=GDSPair(layer=19,  datatype=0)),   original_layer_name="Via1"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=VIA,   name="via2_drw",        description="Computed layer for Via2",                                              drw_gds_pair=GDSPair(layer=29,  datatype=0)),   original_layer_name="Via2"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=VIA,   name="via3_drw",        description="Computed layer for Via3",                                              drw_gds_pair=GDSPair(layer=49,  datatype=0)),   original_layer_name="Via3"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=VIA,   name="via4_drw",        description="Computed layer for Via4",                                              drw_gds_pair=GDSPair(layer=66,  datatype=0)),   original_layer_name="Via4"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=VIA,   name="topvia1_n_cap",   description="Original TopVia1 is 125/0 (case where no MiM cap)",                   drw_gds_pair=GDSPair(layer=125, datatype=0)),   original_layer_name="TopVia1"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KREG, layer_info=LayerInfo(purpose=VIA,   name="topvia2_drw",     description="Computed layer for TopVia2",                                           drw_gds_pair=GDSPair(layer=133, datatype=0)),   original_layer_name="TopVia2"))

    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KCAP, layer_info=LayerInfo(purpose=VIA,   name="mim_via",         description="Original TopVia1 is 125/0, case MiM cap",                              drw_gds_pair=GDSPair(layer=125, datatype=10)),  original_layer_name="TopVia1"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KCAP, layer_info=LayerInfo(purpose=MIM,   name="metal5_cap",      description="Computed layer for Metal5, case MiM cap",                              drw_gds_pair=GDSPair(layer=67,  datatype=0)),   original_layer_name="Metal5"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KCAP, layer_info=LayerInfo(purpose=MIM,   name="cmim_top",        description="Computed layer for MiM cap above Metal5",                              drw_gds_pair=GDSPair(layer=36,  datatype=0)),   original_layer_name="<TODO>"))

    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KPIN, layer_info=LayerInfo(purpose=METAL, name="poly_pin_con",      description="Poly pin",      drw_gds_pair=GDSPair(layer=5,   datatype=2)),  original_layer_name="GatPoly.pin"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KPIN, layer_info=LayerInfo(purpose=METAL, name="metal1_pin_con",    description="Metal1 pin",    drw_gds_pair=GDSPair(layer=8,   datatype=2)),  original_layer_name="Metal1.pin"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KPIN, layer_info=LayerInfo(purpose=METAL, name="metal2_pin_con",    description="Metal2 pin",    drw_gds_pair=GDSPair(layer=10,  datatype=2)),  original_layer_name="Metal2.pin"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KPIN, layer_info=LayerInfo(purpose=METAL, name="metal3_pin_con",    description="Metal3 pin",    drw_gds_pair=GDSPair(layer=30,  datatype=2)),  original_layer_name="Metal3.pin"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KPIN, layer_info=LayerInfo(purpose=METAL, name="metal4_pin_con",    description="Metal4 pin",    drw_gds_pair=GDSPair(layer=50,  datatype=2)),  original_layer_name="Metal4.pin"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KPIN, layer_info=LayerInfo(purpose=METAL, name="metal5_pin_con",    description="Metal5 pin",    drw_gds_pair=GDSPair(layer=67,  datatype=2)),  original_layer_name="Metal5.pin"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KPIN, layer_info=LayerInfo(purpose=METAL, name="topmetal1_pin_con", description="TopMetal1 pin", drw_gds_pair=GDSPair(layer=126, datatype=2)),  original_layer_name="TopMetal1.pin"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KPIN, layer_info=LayerInfo(purpose=METAL, name="topmetal2_pin_con", description="TopMetal2 pin", drw_gds_pair=GDSPair(layer=134, datatype=2)),  original_layer_name="TopMetal2.pin"))

    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KLBL, layer_info=LayerInfo(purpose=METAL, name="poly_text",         description="Poly label",      drw_gds_pair=GDSPair(layer=5,   datatype=25)), original_layer_name="GatPoly.text"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KLBL, layer_info=LayerInfo(purpose=METAL, name="metal1_text",       description="Metal1 label",    drw_gds_pair=GDSPair(layer=8,   datatype=25)), original_layer_name="Metal1.text"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KLBL, layer_info=LayerInfo(purpose=METAL, name="metal2_text",       description="Metal2 label",    drw_gds_pair=GDSPair(layer=10,  datatype=25)), original_layer_name="Metal2.text"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KLBL, layer_info=LayerInfo(purpose=METAL, name="metal3_text",       description="Metal3 label",    drw_gds_pair=GDSPair(layer=30,  datatype=25)), original_layer_name="Metal3.text"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KLBL, layer_info=LayerInfo(purpose=METAL, name="metal4_text",       description="Metal4 label",    drw_gds_pair=GDSPair(layer=50,  datatype=25)), original_layer_name="Metal4.text"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KLBL, layer_info=LayerInfo(purpose=METAL, name="metal5_text",       description="Metal5 label",    drw_gds_pair=GDSPair(layer=67,  datatype=25)), original_layer_name="Metal5.text"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KLBL, layer_info=LayerInfo(purpose=METAL, name="topmetal1_text",    description="TopMetal1 label", drw_gds_pair=GDSPair(layer=126, datatype=25)), original_layer_name="TopMetal1.text"))
    tech.lvs_computed_layers.append(ComputedLayerInfo(kind=KLBL, layer_info=LayerInfo(purpose=METAL, name="topmetal2_text",    description="TopMetal2 label", drw_gds_pair=GDSPair(layer=134, datatype=25)), original_layer_name="TopMetal2.text"))


def build_process_stack_info(tech: Techfile) -> None:
    tech.process_stack = ProcessStackInfo()
    psi = tech.process_stack

    capild_k = 6.7
    capild_thickness = 0.04

    poly_z = 0.4
    poly_thickness = 0.16
    met1_thickness = 0.42
    met2_thickness = 0.36
    met3_thickness = 0.49
    met4_thickness = 0.49
    met5_thickness = 0.49
    cmim_cap_thickness = 0.15
    topmet1_thickness = 2.0
    topmet2_thickness = 3.0

    conp_thickness = 0.64 - poly_thickness
    via1_thickness = 0.54
    via2_thickness = 0.54
    via3_thickness = 0.54
    via4_thickness = 0.54
    topvia1_ncap_thickness = 0.85
    mim_via_thickness = topvia1_ncap_thickness - capild_thickness - cmim_cap_thickness
    topvia2_thickness = 2.8

    met1_z = poly_z + poly_thickness + conp_thickness
    met2_z = met1_z + met1_thickness + via1_thickness
    met3_z = met2_z + met2_thickness + via2_thickness
    met4_z = met3_z + met3_thickness + via3_thickness
    met5_z = met4_z + met4_thickness + via4_thickness
    cmim_z = met5_z + met5_thickness + capild_thickness
    topmet1_z = met5_z + met5_thickness + topvia1_ncap_thickness
    topmet2_z = topmet1_z + topmet1_thickness + topvia2_thickness

    # SUBSTRATE
    psi.layers.append(StackLayerInfo(name="subs", layer_type=StackLayerType.LAYER_TYPE_SUBSTRATE,
        substrate_layer=SubstrateLayer(height=0.0, thickness=0.28, reference="fox")))

    # NWELL / DIFF
    psi.layers.append(StackLayerInfo(name="ntap", layer_type=StackLayerType.LAYER_TYPE_NWELL,
        nwell_layer=NWellLayer(z=0.0, reference="fox")))
    psi.layers.append(StackLayerInfo(name="nSD", layer_type=StackLayerType.LAYER_TYPE_DIFFUSION,
        diffusion_layer=DiffusionLayer(z=0.0, reference="fox",
            contact_above=Contact(name="cont_nsd_con", layer_below="nsd_fet", metal_above="metal1_con", thickness=0.4 + 0.64, width=0.16, spacing=0.18, border=0.0))))
    psi.layers.append(StackLayerInfo(name="pSD", layer_type=StackLayerType.LAYER_TYPE_DIFFUSION,
        diffusion_layer=DiffusionLayer(z=0.0, reference="fox",
            contact_above=Contact(name="cont_psd_con", layer_below="psd_fet", metal_above="metal1_con", thickness=0.4 + 0.64, width=0.16, spacing=0.18, border=0.0))))

    # FOX
    psi.layers.append(StackLayerInfo(name="fox", layer_type=StackLayerType.LAYER_TYPE_FIELD_OXIDE,
        field_oxide_layer=FieldOxideLayer(dielectric_k=3.95)))

    # GATPOLY
    psi.layers.append(StackLayerInfo(name="GatPoly", layer_type=StackLayerType.LAYER_TYPE_METAL,
        metal_layer=MetalLayer(z=poly_z, thickness=poly_thickness,
            contact_above=Contact(name="cont_poly_con", layer_below="poly_con", metal_above="metal1_con", thickness=conp_thickness, width=0.16, spacing=0.18, border=0.0))))
    psi.layers.append(StackLayerInfo(name="nitride", layer_type=StackLayerType.LAYER_TYPE_CONFORMAL_DIELECTRIC,
        conformal_dielectric_layer=ConformalDielectricLayer(dielectric_k=6.5, thickness_over_metal=0.05, thickness_where_no_metal=0.05, thickness_sidewall=0.05, reference="GatPoly")))
    psi.layers.append(StackLayerInfo(name="ild0", layer_type=StackLayerType.LAYER_TYPE_SIMPLE_DIELECTRIC,
        simple_dielectric_layer=SimpleDielectricLayer(dielectric_k=4.1, reference="fox")))

    # METAL1
    psi.layers.append(StackLayerInfo(name="Metal1", layer_type=StackLayerType.LAYER_TYPE_METAL,
        metal_layer=MetalLayer(z=met1_z, thickness=met1_thickness,
            contact_above=Contact(name="via1_drw", layer_below="metal1_con", metal_above="metal2_con", thickness=via1_thickness, width=0.19, spacing=0.22, border=0.0))))
    psi.layers.append(StackLayerInfo(name="ild1", layer_type=StackLayerType.LAYER_TYPE_SIMPLE_DIELECTRIC,
        simple_dielectric_layer=SimpleDielectricLayer(dielectric_k=4.1, reference="ild0")))

    # METAL2
    psi.layers.append(StackLayerInfo(name="Metal2", layer_type=StackLayerType.LAYER_TYPE_METAL,
        metal_layer=MetalLayer(z=met2_z, thickness=met2_thickness,
            contact_above=Contact(name="via2_drw", layer_below="metal2_con", metal_above="metal3_con", thickness=via2_thickness, width=0.19, spacing=0.22, border=0.0))))
    psi.layers.append(StackLayerInfo(name="ild2", layer_type=StackLayerType.LAYER_TYPE_SIMPLE_DIELECTRIC,
        simple_dielectric_layer=SimpleDielectricLayer(dielectric_k=4.1, reference="ild1")))

    # METAL3
    psi.layers.append(StackLayerInfo(name="Metal3", layer_type=StackLayerType.LAYER_TYPE_METAL,
        metal_layer=MetalLayer(z=met3_z, thickness=met3_thickness,
            contact_above=Contact(name="via3_drw", layer_below="metal3_con", metal_above="metal4_con", thickness=via3_thickness, width=0.19, spacing=0.22, border=0.0))))
    psi.layers.append(StackLayerInfo(name="ild3", layer_type=StackLayerType.LAYER_TYPE_SIMPLE_DIELECTRIC,
        simple_dielectric_layer=SimpleDielectricLayer(dielectric_k=4.1, reference="ild2")))

    # METAL4
    psi.layers.append(StackLayerInfo(name="Metal4", layer_type=StackLayerType.LAYER_TYPE_METAL,
        metal_layer=MetalLayer(z=met4_z, thickness=met4_thickness,
            contact_above=Contact(name="via4_drw", layer_below="metal4_con", metal_above="metal5_n_cap", thickness=via4_thickness, width=0.19, spacing=0.22, border=0.0))))
    psi.layers.append(StackLayerInfo(name="ild4", layer_type=StackLayerType.LAYER_TYPE_SIMPLE_DIELECTRIC,
        simple_dielectric_layer=SimpleDielectricLayer(dielectric_k=4.1, reference="ild3")))

    # METAL5 (no-cap variant)
    psi.layers.append(StackLayerInfo(name="metal5_n_cap", layer_type=StackLayerType.LAYER_TYPE_METAL,
        metal_layer=MetalLayer(z=met5_z, thickness=met5_thickness,
            contact_above=Contact(name="topvia1_n_cap", layer_below="metal5_n_cap", metal_above="topmetal1_con", thickness=topvia1_ncap_thickness, width=0.42, spacing=0.42, border=0.005))))
    psi.layers.append(StackLayerInfo(name="ildtm1", layer_type=StackLayerType.LAYER_TYPE_SIMPLE_DIELECTRIC,
        simple_dielectric_layer=SimpleDielectricLayer(dielectric_k=4.1, reference="ild4")))

    # METAL5 (MIM cap variant)
    psi.layers.append(StackLayerInfo(name="metal5_cap", layer_type=StackLayerType.LAYER_TYPE_METAL,
        metal_layer=MetalLayer(z=met5_z, thickness=met5_thickness)))
    psi.layers.append(StackLayerInfo(name="ismim", layer_type=StackLayerType.LAYER_TYPE_CONFORMAL_DIELECTRIC,
        conformal_dielectric_layer=ConformalDielectricLayer(dielectric_k=capild_k, thickness_over_metal=capild_thickness, thickness_where_no_metal=0.0, thickness_sidewall=0.0, reference="metal5_cap")))
    psi.layers.append(StackLayerInfo(name="ildtm1", layer_type=StackLayerType.LAYER_TYPE_SIMPLE_DIELECTRIC,
        simple_dielectric_layer=SimpleDielectricLayer(dielectric_k=4.1, reference="ild4")))

    # CMIM cap
    psi.layers.append(StackLayerInfo(name="cmim_top", layer_type=StackLayerType.LAYER_TYPE_METAL,
        metal_layer=MetalLayer(z=cmim_z, thickness=cmim_cap_thickness,
            contact_above=Contact(name="mim_via", layer_below="cmim_top", metal_above="topmetal1_con", thickness=mim_via_thickness, width=0.42, spacing=0.42, border=0.005))))
    psi.layers.append(StackLayerInfo(name="ildtm1", layer_type=StackLayerType.LAYER_TYPE_SIMPLE_DIELECTRIC,
        simple_dielectric_layer=SimpleDielectricLayer(dielectric_k=4.1, reference="ild4")))

    # TOPMETAL1
    psi.layers.append(StackLayerInfo(name="TopMetal1", layer_type=StackLayerType.LAYER_TYPE_METAL,
        metal_layer=MetalLayer(z=topmet1_z, thickness=topmet1_thickness,
            contact_above=Contact(name="topvia2_drw", layer_below="topmetal1_con", metal_above="topmetal2_con", thickness=topvia2_thickness, width=0.9, spacing=1.06, border=0.5))))
    psi.layers.append(StackLayerInfo(name="ildtm2", layer_type=StackLayerType.LAYER_TYPE_SIMPLE_DIELECTRIC,
        simple_dielectric_layer=SimpleDielectricLayer(dielectric_k=4.1, reference="ildtm1")))

    # TOPMETAL2
    psi.layers.append(StackLayerInfo(name="TopMetal2", layer_type=StackLayerType.LAYER_TYPE_METAL,
        metal_layer=MetalLayer(z=topmet2_z, thickness=topmet2_thickness)))
    psi.layers.append(StackLayerInfo(name="pass1", layer_type=StackLayerType.LAYER_TYPE_CONFORMAL_DIELECTRIC,
        conformal_dielectric_layer=ConformalDielectricLayer(dielectric_k=4.1, thickness_over_metal=1.5, thickness_where_no_metal=1.5, thickness_sidewall=0.3, reference="TopMetal2")))
    psi.layers.append(StackLayerInfo(name="pass2", layer_type=StackLayerType.LAYER_TYPE_CONFORMAL_DIELECTRIC,
        conformal_dielectric_layer=ConformalDielectricLayer(dielectric_k=6.6, thickness_over_metal=0.4, thickness_where_no_metal=0.4, thickness_sidewall=0.3, reference="pass1")))
    psi.layers.append(StackLayerInfo(name="air", layer_type=StackLayerType.LAYER_TYPE_SIMPLE_DIELECTRIC,
        simple_dielectric_layer=SimpleDielectricLayer(dielectric_k=1.0, reference="pass2")))


def build_process_parasitics_info(tech: Techfile) -> None:
    # NOTE: coefficients according to
    # https://github.com/IHP-GmbH/IHP-Open-PDK/blob/7897c7f99fe5538656b4c08e300cfe4d2c8a5503/ihp-sg13g2/libs.tech/magic/ihp-sg13g2.tech#L4515
    tech.process_parasitics = ProcessParasiticsInfo(
        side_halo=8.0,
        resistance=ResistanceInfo(),
        capacitance=CapacitanceInfo(),
    )
    ex = tech.process_parasitics
    ri = ex.resistance
    ci = ex.capacitance

    # sheet resistance (mΩ/sq)
    ri.layers.append(LayerResistance(layer_name="GatPoly",   resistance=7000))
    ri.layers.append(LayerResistance(layer_name="Metal1",    resistance=110))
    ri.layers.append(LayerResistance(layer_name="Metal2",    resistance=88))
    ri.layers.append(LayerResistance(layer_name="Metal3",    resistance=88))
    ri.layers.append(LayerResistance(layer_name="Metal4",    resistance=88))
    ri.layers.append(LayerResistance(layer_name="Metal5",    resistance=88))
    ri.layers.append(LayerResistance(layer_name="TopMetal1", resistance=18))
    ri.layers.append(LayerResistance(layer_name="TopMetal2", resistance=11))

    # contact resistance (mΩ/CNT)
    ri.contacts.append(ContactResistance(contact_name="cont_nsd_con",  device_layer_name="nsd_fet",  layer_above="metal1_con", resistance=17000))
    ri.contacts.append(ContactResistance(contact_name="cont_psd_con",  device_layer_name="psd_fet",  layer_above="metal1_con", resistance=17000))
    ri.contacts.append(ContactResistance(contact_name="cont_poly_con", device_layer_name="poly_con", layer_above="metal1_con", resistance=15000))

    # via resistance (mΩ/CNT)
    ri.vias.append(ViaResistance(via_name="Via1",     resistance=9000))
    ri.vias.append(ViaResistance(via_name="Via2",     resistance=9000))
    ri.vias.append(ViaResistance(via_name="Via3",     resistance=9000))
    ri.vias.append(ViaResistance(via_name="Via4",     resistance=9000))
    ri.vias.append(ViaResistance(via_name="TopVia1",  resistance=2200))
    ri.vias.append(ViaResistance(via_name="TopVia2",  resistance=1100))

    # substrate capacitance (aF/µm² area, aF/µm perimeter)
    ci.substrates.append(SubstrateCapacitance(layer_name="GatPoly",   area_capacitance=87.433, perimeter_capacitance=44.537))
    ci.substrates.append(SubstrateCapacitance(layer_name="Metal1",    area_capacitance=35.015, perimeter_capacitance=39.585))
    ci.substrates.append(SubstrateCapacitance(layer_name="Metal2",    area_capacitance=18.180, perimeter_capacitance=34.798))
    ci.substrates.append(SubstrateCapacitance(layer_name="Metal3",    area_capacitance=11.994, perimeter_capacitance=31.352))
    ci.substrates.append(SubstrateCapacitance(layer_name="Metal4",    area_capacitance=8.948,  perimeter_capacitance=29.083))
    ci.substrates.append(SubstrateCapacitance(layer_name="Metal5",    area_capacitance=7.136,  perimeter_capacitance=27.527))
    ci.substrates.append(SubstrateCapacitance(layer_name="TopMetal1", area_capacitance=5.649,  perimeter_capacitance=37.383))
    ci.substrates.append(SubstrateCapacitance(layer_name="TopMetal2", area_capacitance=3.233,  perimeter_capacitance=31.175))

    diff_lv_nonfet = "Activ"
    diff_hv_nonfet = "Activ"

    # overlap capacitance (aF/µm²)
    ci.overlaps.append(OverlapCapacitance(top_layer_name="GatPoly",   bottom_layer_name="NWell",          capacitance=87.433))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="GatPoly",   bottom_layer_name="PWell",          capacitance=87.433))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal1",    bottom_layer_name="PWell",          capacitance=35.015))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal1",    bottom_layer_name="NWell",          capacitance=35.015))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal1",    bottom_layer_name=diff_lv_nonfet,   capacitance=58.168))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal1",    bottom_layer_name=diff_hv_nonfet,   capacitance=57.702))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal1",    bottom_layer_name="GatPoly",        capacitance=78.653))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal2",    bottom_layer_name="PWell",          capacitance=18.180))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal2",    bottom_layer_name="NWell",          capacitance=18.180))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal2",    bottom_layer_name=diff_lv_nonfet,   capacitance=22.916))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal2",    bottom_layer_name=diff_hv_nonfet,   capacitance=22.844))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal2",    bottom_layer_name="GatPoly",        capacitance=25.537))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal2",    bottom_layer_name="Metal1",         capacitance=67.225))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal3",    bottom_layer_name="NWell",          capacitance=11.994))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal3",    bottom_layer_name="PWell",          capacitance=11.994))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal3",    bottom_layer_name=diff_lv_nonfet,   capacitance=13.887))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal3",    bottom_layer_name=diff_hv_nonfet,   capacitance=13.860))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal3",    bottom_layer_name="GatPoly",        capacitance=14.808))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal3",    bottom_layer_name="Metal1",         capacitance=23.122))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal3",    bottom_layer_name="Metal2",         capacitance=67.225))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal4",    bottom_layer_name="NWell",          capacitance=8.948))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal4",    bottom_layer_name="PWell",          capacitance=8.948))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal4",    bottom_layer_name=diff_lv_nonfet,   capacitance=9.962))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal4",    bottom_layer_name=diff_hv_nonfet,   capacitance=9.948))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal4",    bottom_layer_name="GatPoly",        capacitance=10.427))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal4",    bottom_layer_name="Metal1",         capacitance=13.962))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal4",    bottom_layer_name="Metal2",         capacitance=23.122))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal4",    bottom_layer_name="Metal3",         capacitance=67.225))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal5",    bottom_layer_name="NWell",          capacitance=7.136))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal5",    bottom_layer_name="PWell",          capacitance=7.136))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal5",    bottom_layer_name=diff_lv_nonfet,   capacitance=7.766))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal5",    bottom_layer_name=diff_hv_nonfet,   capacitance=7.758))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal5",    bottom_layer_name="GatPoly",        capacitance=8.046))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal5",    bottom_layer_name="Metal1",         capacitance=10.000))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal5",    bottom_layer_name="Metal2",         capacitance=13.962))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal5",    bottom_layer_name="Metal3",         capacitance=23.122))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="Metal5",    bottom_layer_name="Metal4",         capacitance=67.225))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal1", bottom_layer_name="NWell",          capacitance=5.649))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal1", bottom_layer_name="PWell",          capacitance=5.649))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal1", bottom_layer_name=diff_lv_nonfet,   capacitance=6.036))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal1", bottom_layer_name=diff_hv_nonfet,   capacitance=6.031))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal1", bottom_layer_name="GatPoly",        capacitance=6.204))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal1", bottom_layer_name="Metal1",         capacitance=7.304))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal1", bottom_layer_name="Metal2",         capacitance=9.214))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal1", bottom_layer_name="Metal3",         capacitance=12.475))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal1", bottom_layer_name="Metal4",         capacitance=19.309))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal1", bottom_layer_name="Metal5",         capacitance=42.708))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal2", bottom_layer_name="NWell",          capacitance=3.233))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal2", bottom_layer_name="PWell",          capacitance=3.233))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal2", bottom_layer_name=diff_lv_nonfet,   capacitance=3.357))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal2", bottom_layer_name=diff_hv_nonfet,   capacitance=3.355))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal2", bottom_layer_name="GatPoly",        capacitance=3.408))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal2", bottom_layer_name="Metal1",         capacitance=3.716))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal2", bottom_layer_name="Metal2",         capacitance=4.154))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal2", bottom_layer_name="Metal3",         capacitance=4.708))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal2", bottom_layer_name="Metal4",         capacitance=5.434))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal2", bottom_layer_name="Metal5",         capacitance=6.425))
    ci.overlaps.append(OverlapCapacitance(top_layer_name="TopMetal2", bottom_layer_name="TopMetal1",      capacitance=12.965))

    # sidewall capacitance (aF/µm, offset µm)
    ci.sidewalls.append(SidewallCapacitance(layer_name="GatPoly",   capacitance=11.722,  offset=-0.023))
    ci.sidewalls.append(SidewallCapacitance(layer_name="Metal1",    capacitance=28.735,  offset=-0.057))
    ci.sidewalls.append(SidewallCapacitance(layer_name="Metal2",    capacitance=40.981,  offset=-0.033))
    ci.sidewalls.append(SidewallCapacitance(layer_name="Metal3",    capacitance=37.679,  offset=-0.045))
    ci.sidewalls.append(SidewallCapacitance(layer_name="Metal4",    capacitance=49.526,  offset=0.004))
    ci.sidewalls.append(SidewallCapacitance(layer_name="Metal5",    capacitance=53.129,  offset=0.021))
    ci.sidewalls.append(SidewallCapacitance(layer_name="TopMetal1", capacitance=162.172, offset=0.343))
    ci.sidewalls.append(SidewallCapacitance(layer_name="TopMetal2", capacitance=227.323, offset=1.893))

    # sidewall-overlap capacitance (aF/µm)
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="GatPoly",   out_layer_name="NWell",          capacitance=44.537))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="GatPoly",   out_layer_name="PWell",          capacitance=44.537))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal1",    out_layer_name="NWell",          capacitance=39.585))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal1",    out_layer_name="PWell",          capacitance=39.585))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal1",    out_layer_name=diff_lv_nonfet,   capacitance=44.749))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal1",    out_layer_name=diff_hv_nonfet,   capacitance=45.041))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal1",    out_layer_name="GatPoly",        capacitance=49.378))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="GatPoly",   out_layer_name="Metal1",         capacitance=23.229))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal2",    out_layer_name="NWell",          capacitance=34.798))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal2",    out_layer_name="PWell",          capacitance=34.798))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal2",    out_layer_name=diff_lv_nonfet,   capacitance=36.950))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal2",    out_layer_name=diff_hv_nonfet,   capacitance=36.919))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal2",    out_layer_name="GatPoly",        capacitance=37.616))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="GatPoly",   out_layer_name="Metal2",         capacitance=10.801))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal2",    out_layer_name="Metal1",         capacitance=49.543))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal1",    out_layer_name="Metal2",         capacitance=31.073))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal3",    out_layer_name="NWell",          capacitance=31.352))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal3",    out_layer_name="PWell",          capacitance=31.352))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal3",    out_layer_name=diff_lv_nonfet,   capacitance=32.271))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal3",    out_layer_name=diff_hv_nonfet,   capacitance=32.495))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal3",    out_layer_name="GatPoly",        capacitance=32.795))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="GatPoly",   out_layer_name="Metal3",         capacitance=7.068))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal3",    out_layer_name="Metal1",         capacitance=37.009))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal1",    out_layer_name="Metal3",         capacitance=17.349))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal3",    out_layer_name="Metal2",         capacitance=49.537))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal2",    out_layer_name="Metal3",         capacitance=36.907))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal4",    out_layer_name="NWell",          capacitance=29.083))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal4",    out_layer_name="PWell",          capacitance=29.083))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal4",    out_layer_name=diff_lv_nonfet,   capacitance=29.755))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal4",    out_layer_name=diff_hv_nonfet,   capacitance=29.942))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal4",    out_layer_name="GatPoly",        capacitance=30.101))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="GatPoly",   out_layer_name="Metal4",         capacitance=5.240))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal4",    out_layer_name="Metal1",         capacitance=32.162))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal1",    out_layer_name="Metal4",         capacitance=12.398))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal4",    out_layer_name="Metal2",         capacitance=36.335))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal2",    out_layer_name="Metal4",         capacitance=22.327))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal4",    out_layer_name="Metal3",         capacitance=49.537))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal3",    out_layer_name="Metal4",         capacitance=40.019))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal5",    out_layer_name="NWell",          capacitance=27.527))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal5",    out_layer_name="PWell",          capacitance=27.527))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal5",    out_layer_name=diff_lv_nonfet,   capacitance=28.227))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal5",    out_layer_name=diff_hv_nonfet,   capacitance=28.221))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal5",    out_layer_name="GatPoly",        capacitance=28.414))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="GatPoly",   out_layer_name="Metal5",         capacitance=4.178))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal5",    out_layer_name="Metal1",         capacitance=29.935))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal1",    out_layer_name="Metal5",         capacitance=9.725))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal5",    out_layer_name="Metal2",         capacitance=32.116))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal2",    out_layer_name="Metal5",         capacitance=16.534))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal5",    out_layer_name="Metal3",         capacitance=36.971))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal3",    out_layer_name="Metal5",         capacitance=24.785))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal5",    out_layer_name="Metal4",         capacitance=49.517))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal4",    out_layer_name="Metal5",         capacitance=41.956))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal1", out_layer_name="NWell",          capacitance=37.383))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal1", out_layer_name="PWell",          capacitance=37.383))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal1", out_layer_name=diff_lv_nonfet,   capacitance=38.084))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal1", out_layer_name=diff_hv_nonfet,   capacitance=38.085))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal1", out_layer_name="GatPoly",        capacitance=38.376))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="GatPoly",   out_layer_name="TopMetal1",      capacitance=3.316))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal1", out_layer_name="Metal1",         capacitance=39.678))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal1",    out_layer_name="TopMetal1",      capacitance=7.669))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal1", out_layer_name="Metal2",         capacitance=42.268))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal2",    out_layer_name="TopMetal1",      capacitance=12.649))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal1", out_layer_name="Metal3",         capacitance=46.611))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal3",    out_layer_name="TopMetal1",      capacitance=17.848))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal1", out_layer_name="Metal4",         capacitance=52.657))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal4",    out_layer_name="TopMetal1",      capacitance=24.526))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal1", out_layer_name="Metal5",         capacitance=65.859))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal5",    out_layer_name="TopMetal1",      capacitance=36.377))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal2", out_layer_name="NWell",          capacitance=31.175))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal2", out_layer_name="PWell",          capacitance=31.175))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal2", out_layer_name=diff_lv_nonfet,   capacitance=31.484))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal2", out_layer_name=diff_hv_nonfet,   capacitance=30.835))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal2", out_layer_name="GatPoly",        capacitance=30.971))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="GatPoly",   out_layer_name="TopMetal2",      capacitance=1.909))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal2", out_layer_name="Metal1",         capacitance=32.318))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal1",    out_layer_name="TopMetal2",      capacitance=4.344))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal2", out_layer_name="Metal2",         capacitance=33.245))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal2",    out_layer_name="TopMetal2",      capacitance=6.975))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal2", out_layer_name="Metal3",         capacitance=34.339))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal3",    out_layer_name="TopMetal2",      capacitance=9.381))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal2", out_layer_name="Metal4",         capacitance=35.630))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal4",    out_layer_name="TopMetal2",      capacitance=11.825))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal2", out_layer_name="Metal5",         capacitance=37.206))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="Metal5",    out_layer_name="TopMetal2",      capacitance=14.415))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal2", out_layer_name="TopMetal1",      capacitance=44.735))
    ci.sideoverlaps.append(SideOverlapCapacitance(in_layer_name="TopMetal1", out_layer_name="TopMetal2",      capacitance=33.071))


def build_tech() -> Techfile:
    tech = Techfile(name="ihp-sg13g2")
    build_layers(tech)
    build_lvs_computed_layers(tech)
    build_process_stack_info(tech)
    build_process_parasitics_info(tech)
    return tech
