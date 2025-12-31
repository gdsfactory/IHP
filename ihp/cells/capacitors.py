"""Capacitor components for IHP PDK."""

from numpy import floor

import gdsfactory as gf
from gdsfactory import Component
from gdsfactory.typings import LayerSpec

from ihp import tech, cells
from ihp.cells2.ihp_pycell.utility_functions import CbCapCalc
from ihp.cells import via_stack
from ihp.cells.passives import guard_ring

def snap_to_grid(p, grid: float = 0.005):
    return round(p / grid) * grid

# TODO: snap dims to grid

def cmom_extractor(
    nfingers: int = 1,
    length: float = 2.0,
    spacing: float = 0.26,
    min_width: float = 0.2,
    mom_metals: list[LayerSpec] = [],
    **kwargs
) -> float:
    
    layer_thickness = {
        'Metal1': tech.LAYER_STACK['metal1'].thickness,
        'Metal2': tech.LAYER_STACK['metal2'].thickness,
        'Metal3': tech.LAYER_STACK['metal3'].thickness,
        'Metal4': tech.LAYER_STACK['metal4'].thickness,
        'Metal5': tech.LAYER_STACK['metal5'].thickness,
    }

    total_cap: float = 0.0
    fringe_field_factor = kwargs.get('fringe_field_factor', 0.2)
    permitivity = kwargs.get('interlayer_dielectric', 3.8)
    eps0 = 8.8541878188e-3 # 

    for metal in mom_metals:
        th = layer_thickness[metal]
        min_finger_width = min_width
        total_cap += permitivity*eps0*(th / spacing)* \
            ( ( nfingers * 2 ) * (length + spacing) + min_finger_width*(nfingers*2 + 1) )
    return total_cap * (1 + fringe_field_factor)

@gf.cell
def cmom(
    nfingers: int = 1,
    length: float = 4.0,
    spacing: float = 0.26,
    botmetal: LayerSpec = "Metal1",
    topmetal: LayerSpec = "Metal3",
    layer_metal1: LayerSpec = 'Metal1drawing',
    layer_metal2: LayerSpec = 'Metal2drawing',
    layer_metal3: LayerSpec = 'Metal3drawing',
    layer_metal4: LayerSpec = 'Metal4drawing',
    layer_metal5: LayerSpec = 'Metal5drawing',
    layer_metal1pin: LayerSpec = 'Metal1pin',
    layer_metal2pin: LayerSpec = 'Metal2pin',
    layer_metal3pin: LayerSpec = 'Metal3pin',
    layer_metal4pin: LayerSpec = 'Metal4pin',
    layer_metal5pin: LayerSpec = 'Metal5pin',
    layer_metal1label: LayerSpec = 'Metal1label',
    layer_metal2label: LayerSpec = 'Metal2label',
    layer_metal3label: LayerSpec = 'Metal3label',
    layer_metal4label: LayerSpec = 'Metal4label',
    layer_metal5label: LayerSpec = 'Metal5label',
    layer_metal1nofill: LayerSpec = 'Metal1nofill',
    layer_metal2nofill: LayerSpec = 'Metal2nofill',
    layer_metal3nofill: LayerSpec = 'Metal3nofill',
    layer_metal4nofill: LayerSpec = 'Metal4nofill',
    layer_metal5nofill: LayerSpec = 'Metal5nofill',
    layer_cap_mark: LayerSpec = "MemCapdrawing",
    layer_text: LayerSpec = "TEXTdrawing",
    model: str = 'cmom',
    **kwargs
) -> Component: 
    """Create a MOM (Metal-Over-Metal) interdigitated capacitor.

    Args:
        nfingers: Number of inside fingers.
        length: Length of the capacitor in micrometers.
        spacing: Spacing between top and bottom electrodes. 
            Higher spacing, lower capacitance.
        botmetal: Bottom Metal layer for the capacitor stack.
        topmetal: Top Metal layer for the capacitor stack. 
        --- Layers
        layer_metal1: Metal1 drawing layer.
        layer_metal2: Metal2 drawing layer.
        layer_metal3: Metal3 drawing layer.
        layer_metal4: Metal4 drawing layer.
        layer_metal5: Metal5 drawing layer.
        layer_metal1pin: Metal1 pin logic layer.
        layer_metal2pin: Metal2 pin logic layer.
        layer_metal3pin: Metal3 pin logic layer.
        layer_metal4pin: Metal4 pin logic layer.
        layer_metal5pin: Metal5 pin logic layer.
        layer_metal1label: Metal1 label logic layer.
        layer_metal2label: Metal2 label logic layer.
        layer_metal3label: Metal3 label logic layer.
        layer_metal4label: Metal4 label logic layer.
        layer_metal5label: Metal5 label logic layer.
        layer_metal1nofill: Metal1 nofill logic layer.
        layer_metal2nofill: Metal2 nofill logic layer.
        layer_metal3nofill: Metal3 nofill logic layer.
        layer_metal4nofill: Metal4 nofill logic layer.
        layer_metal5nofill: Metal5 nofill logic layer.
        layer_cap_mark: MemCapdrawing logic layer.
        layer_text: TEXT drawing layer
        model: Device model name.

    Returns:
        Component with MOM capacitor layout.
    Raises:
    """

    metals = {
        'Metal1': layer_metal1,
        'Metal2': layer_metal2,
        'Metal3': layer_metal3,
        'Metal4': layer_metal4,
        'Metal5': layer_metal5,
    }

    labels = {
        'Metal1': layer_metal1label,
        'Metal2': layer_metal2label,
        'Metal3': layer_metal3label,
        'Metal4': layer_metal4label,
        'Metal5': layer_metal5label,
    }

    pins = {
        'Metal1': layer_metal1pin,
        'Metal2': layer_metal2pin,
        'Metal3': layer_metal3pin,
        'Metal4': layer_metal4pin,
        'Metal5': layer_metal5pin,
    }

    nofills = {
        'Metal1': layer_metal1nofill,
        'Metal2': layer_metal2nofill,
        'Metal3': layer_metal3nofill,
        'Metal4': layer_metal4nofill,
        'Metal5': layer_metal5nofill,
    }

    pdk_design_rules = {
        'Metal1':{'min_width':tech.TECH.metal1_width, 'min_spacing':tech.TECH.metal1_spacing},
        'Metal2':{'min_width':tech.TECH.metal2_width, 'min_spacing':tech.TECH.metal2_spacing},
        'Metal3':{'min_width':tech.TECH.metal3_width, 'min_spacing':tech.TECH.metal3_spacing},
        'Metal4':{'min_width':tech.TECH.metal4_width, 'min_spacing':tech.TECH.metal4_spacing},
        'Metal5':{'min_width':tech.TECH.metal5_width, 'min_spacing':tech.TECH.metal5_spacing}
    }
    
    min_width_global = min([v['min_width'] for v in pdk_design_rules.values()])
    min_spacing_global = min([v['min_spacing'] for v in pdk_design_rules.values()])
    min_length = 3 * min_width_global # to comply with minimum metal area DRC

    assert length > min_length, f"Minimum Area for all metals > {min_length * min_width_global}"
    assert spacing > min_spacing_global, f"Minimum metal spacing for all metals > {min_spacing_global}"

    ordered_metals = list(metals.keys())
    #ordered_vias = [lay for lay in ordered_layers if "via" in lay]
    assert botmetal in ordered_metals, "{botmetal} not it available layers: {_ordered_metals}"
    assert topmetal in ordered_metals, "{topmetal} not it available layers: {_ordered_metals}"
    mom_metals = ordered_metals[
        ordered_metals.index(botmetal) : ordered_metals.index(topmetal)+1
    ]
    c = gf.Component()
    total_length = 0.0
    top_pad_ref = None
    bot_pad_ref = None
    for metal_layer in mom_metals:
        min_width = min_width_global
        layer = metals[metal_layer]
        top_finger = gf.components.rectangle(
            size=(min_width, length), layer=layer)
        top_finger_array = c.add_ref(
            top_finger, columns=nfingers+1, rows=1, 
            column_pitch=2*(spacing+min_width))
        top_finger_array.ymin += spacing
        bot_finger = gf.components.rectangle(
            size=(min_width, length), layer=layer)
        bot_finger_array = c.add_ref(
            bot_finger, columns=nfingers, rows=1, 
            column_pitch=2*(spacing+min_width))
        bot_finger_array.xmin += min_width + spacing      
        total_length = (min_width + spacing) * (2*nfingers + 1) - spacing
        top_pad = gf.components.rectangle(
            size=(total_length, 3*min_width), layer=layer)
        top_pad_ref = c.add_ref(top_pad)
        top_pad_ref.ymin += length + spacing
        bot_pad_ref = c.add_ref(top_pad)
        bot_pad_ref.ymax = 0
        
        
        #   add no fill and no QRC layers to the mom device region
        #nofill_layer = metal_layer.capitalize()+'nofill'
        nofill_layer = nofills[metal_layer.capitalize()]
        c.add_ref(gf.components.bbox(
            c, layer=nofill_layer
        ))


    # add capacitor region marker
    c.add_ref(gf.components.bbox(
        c, layer=layer_cap_mark
    ))

    # add ports 
    #pin_layer: LayerSpec = metal_layer.capitalize()+'pin'
    #label_layer: LayerSpec = metal_layer.capitalize()+'label'
    pin_layer = pins[metal_layer.capitalize()]
    label_layer = labels[metal_layer.capitalize()]
    c.add_port(
        "PLUS",
        center=(top_pad_ref.x, top_pad_ref.y), 
        width=min_width, layer=pin_layer)
    c.add_port(
        "MINUS",
        center=(bot_pad_ref.x, bot_pad_ref.y), 
        width=min_width, layer=pin_layer)
    
    c.add_label(
        text="PLUS",
        position=(top_pad_ref.x, top_pad_ref.y),
        layer=label_layer
    )
    c.add_label(
        text="MINUS",
        position=(bot_pad_ref.x, bot_pad_ref.y),
        layer=label_layer
    )
    c.add_label(
        text="PLUS",
        position=(top_pad_ref.x, top_pad_ref.y),
        layer=layer_text
    )
    c.add_label(
        text="MINUS",
        position=(bot_pad_ref.x, bot_pad_ref.y),
        layer=layer_text
    )

    c.add_label(
        text=model,
        position=(c.x, c.y + min_width),
        layer=layer_text
    )
    

    #   add a via array stack to the top and bottom pads
    mom_via_stack = via_stack(
        bottom_layer = botmetal.capitalize(),
        top_layer = topmetal.capitalize(),
        size = (total_length, 3*min_width),
        vn_columns = nfingers * 4,
        vn_rows = 1
    )

    via_stack_bot = c.add_ref(mom_via_stack)
    via_stack_bot.xmin = bot_pad_ref.xmin
    via_stack_bot.ymax = bot_pad_ref.ymax
    via_stack_top = c.add_ref(mom_via_stack)
    via_stack_top.xmin = top_pad_ref.xmin
    via_stack_top.ymin = top_pad_ref.ymin
    
    #   add place and route layers to define the device's bounding box
    prboundary_layer = 'prBoundarydrawing'
    c.add_ref(gf.components.bbox(
        c, layer=prboundary_layer
    ))
    c.info['capacitance'] = cmom_extractor(
        nfingers,
        length,
        spacing,
        min_width = min_width_global,
        mom_metals = mom_metals,
        **kwargs
        )
    c.add_label(
        text=f'C = {c.info['capacitance']} fF',
        position=(c.x, c.y - min_width),
        layer=layer_text
    )
    c.info['model'] = model
    c.info['nfingers'] = nfingers
    c.info['length'] = length
    c.info['spacing'] = spacing
    
    #   return the component
    return c

@gf.cell
def cmim(
    width: float = 6.0,
    length: float = 6.0,
    layer_metal5: LayerSpec = "Metal5drawing",
    layer_mim: LayerSpec = "MIMdrawing",
    layer_vmim: LayerSpec = "Vmimdrawing",
    layer_topmetal1: LayerSpec = "TopMetal1drawing",
    layer_cap_mark: LayerSpec = "MemCapdrawing",
    layer_m4nofill: LayerSpec = "Metal4nofill",
    layer_m5nofill: LayerSpec = "Metal5nofill",
    layer_tm1nofill: LayerSpec = "TopMetal1nofill",
    layer_tm2nofill: LayerSpec = "TopMetal2nofill",
    layer_text: LayerSpec = "TEXTdrawing",
    layer_metal5label: LayerSpec = "Metal5label",
    layer_topmetal1label: LayerSpec = "TopMetal1label",
    layer_metal5pin: LayerSpec = "Metal5pin",
    layer_topmetal1pin: LayerSpec = "TopMetal1pin",
    model: str = 'cmim',
    **kwargs
) -> Component:
    """Create a MIM (Metal-Insulator-Metal) capacitor.

    Args:
        width: Width of the capacitor in micrometers.
        length: Length of the capacitor in micrometers.
        bot_enclosure: Bottol Metal5 layer enclosure
        top_enclosure: 
        layer_metal5: Metal 5 drawing layer.
        layer_mim: MIM device drawing layer.
        layer_vmim: Vmim (MIM-TopMetal1 Via) drawing layer.
        layer_topmetal1: TopMetal1 drawing layer.
        layer_cap_mark: MemCap drawing layer.
        layer_m4nofill: Metal4 nofill logic layer.
        layer_m5nofill: Metal5 nofill logic layer.
        layer_tm1nofill: TopMetal1 nofill logic layer.
        layer_tm2nofill: TopMetal2 nofill logic layer.
        layer_text: TEXT drawing layer.
        layer_metal5label: Metal5 label logic layer.
        layer_topmetal1label: TopMetal1 label logic layer.
        layer_metal5pin: Metal5 pin logic layer.
        layer_topmetal1pin: TopMetal1 pin logic layer.

        model: Device model name.

    Returns:
        Component with MIM capacitor layout.
    Raises:
    """

    c = Component()

    mim_drc = {
        # capacitor
        'mim_min_size': tech.TECH.mim_min_size,
        'mim_cap_density': tech.TECH.mim_cap_density,
        # metals
        'm5_min_width': tech.TECH.metal5_width,
        'm5_min_spacing': tech.TECH.metal5_spacing,
        'topmetal1_width': tech.TECH.topmetal1_width,
        'topmetal1_spacing': tech.TECH.topmetal1_spacing,
        # vias
        'vmim_size': 0.42,
        'vmim_spacing': 0.52,
        'vmim_enc_metal': 0.42,
        'vmim_enc': 0.6, # bot_enclosure
        'mim_enc': 0.36 #top_enclosure
    }

    bot_enclosure = mim_drc['vmim_enc']
    top_enclosure = mim_drc['mim_enc']
    
    # verification
    assert width > mim_drc['mim_min_size'], f"MIM width > {mim_drc['mim_min_size']}"
    assert length > mim_drc['mim_min_size'], f"MIM width > {mim_drc['mim_min_size']}"
    
    # snap to grid
    grid = tech.TECH.grid
    width = round(width / grid) * grid
    length = round(length / grid) * grid

    # build capacitor stack

    # Bottom plate (Metal4)
    bottom_plate_width = width + 2 * bot_enclosure + 2*top_enclosure
    bottom_plate_length = length + 2 * bot_enclosure + 2*top_enclosure

    bottom_plate = gf.components.rectangle(
        size=(bottom_plate_length, bottom_plate_width),
        layer=layer_metal5,
        centered=True,
    )
    bot = c.add_ref(bottom_plate)

    # MIM layer
    mim_layer = gf.components.rectangle(
        size=(length + 2*top_enclosure, width + 2*top_enclosure),
        layer=layer_mim,
        centered=True,
    )
    c.add_ref(mim_layer)

    # add vmim via array
    vmim_min_width = mim_drc['vmim_size'] + mim_drc['vmim_spacing']
    nrows = int(floor(width / vmim_min_width))
    ncols = int(floor(length / vmim_min_width))

    # Top plate (TopMetal1)
    top_plate = gf.components.rectangle(
        size=(length, width),
        layer=layer_topmetal1,
        centered=True,
    )
    top = c.add_ref(top_plate)

    vmim_array = cells.via_array(
        via_type = layer_vmim.split('drawing')[0],
        via_size = mim_drc['vmim_size'],
        via_spacing = mim_drc['vmim_size'] + mim_drc['vmim_spacing'],
        via_enclosure = mim_drc['vmim_enc_metal'],
        columns = ncols,
        rows = nrows
    )
    vias = c.add_ref(vmim_array)
    vias.x = top.x
    vias.y = top.y

    # Add no fill logic layers

    logic = [
        layer_cap_mark, layer_m4nofill, 
        layer_m5nofill, layer_tm1nofill, 
        layer_tm2nofill
    ]
    for layer_spec in logic:
        ll = gf.components.rectangle(
            size=(bottom_plate_length, bottom_plate_width),
            layer=layer_spec,
            centered=True,
        )
        c.add_ref(ll)


    minus = c.add_port(
        name="MINUS",
        center=(bot.xmin + mim_drc['m5_min_width']/2, bot.y),
        width=mim_drc['m5_min_width'],
        orientation=180,
        layer=layer_metal5label,
        port_type="electrical",
    )

    plus = c.add_port(
        name="PLUS",
        center=(top.xmax - mim_drc['topmetal1_width']/2, top.y),
        width=mim_drc['topmetal1_width'],
        orientation=0,
        layer=layer_topmetal1label,
        port_type="electrical",
    )

    pin_minus = gf.components.rectangle(
        size=(mim_drc['topmetal1_width'], 2*mim_drc['topmetal1_width']),
        layer=layer_metal5pin,
        centered=True,
    )
    pin_minus_ref = c.add_ref(pin_minus)
    pin_minus_ref.xmin = bot.xmin
    pin_minus_ref.y = minus.y

    pin_plus = gf.components.rectangle(
        size=(mim_drc['topmetal1_width'], 2*mim_drc['topmetal1_width']),
        layer=layer_topmetal1pin,
        centered=True,
    )
    pin_plus_ref = c.add_ref(pin_plus)
    pin_plus_ref.xmax = top.xmax
    pin_plus_ref.y = plus.y

    c.add_label(
        text="PLUS",
        position=(top.xmax - mim_drc['topmetal1_width']/2, top.y),
        layer=layer_text
    )
    c.add_label(
        text="MINUS",
        position=(bot.xmin + mim_drc['m5_min_width']/2, bot.y),
        layer=layer_text
    )

    c.add_label(
        text=model,
        position=(c.x, c.y + width/2),
        layer=layer_text
    )

    #fringe_factor = kwargs.get("fringe_factor", 0.355)
    #capacitance = width * length * mim_drc['mim_cap_density']
    #capacitance *= (1+fringe_factor)
    capacitance = CbCapCalc("C", 0, length*1e-6, width*1e-6, model)/1e-15

    c.add_label(
        text=f"C = {capacitance} fF",
        position=(c.x, c.y - width/2),
        layer=layer_text
    )

    c.info["model"] = model
    c.info["width"] = width
    c.info["length"] = length
    c.info["capacitance_fF"] = capacitance
    c.info["area_um2"] = width * length
    return c

@gf.cell
def rfcmim(
    width: float = 6.0,
    length: float = 6.0,
    layer_pwellblock: LayerSpec = "PWellblock",
    layer_metal5: LayerSpec = "Metal5drawing",
    layer_mim: LayerSpec = "MIMdrawing",
    layer_vmim: LayerSpec = "Vmimdrawing",
    layer_topmetal1: LayerSpec = "TopMetal1drawing",
    layer_cap_mark: LayerSpec = "MemCapdrawing",
    layer_m4nofill: LayerSpec = "Metal4nofill",
    layer_m5nofill: LayerSpec = "Metal5nofill",
    layer_tm1nofill: LayerSpec = "TopMetal1nofill",
    layer_tm2nofill: LayerSpec = "TopMetal2nofill",
    layer_activ: LayerSpec = "Activdrawing",
    layer_cont: LayerSpec = "Contdrawing",
    layer_metal1: LayerSpec = "Metal1drawing",
    layer_psd: LayerSpec = "pSDdrawing",
    #layer_rfpad: LayerSpec = "RFPaddrawing",
    layer_activnoqrc: LayerSpec = "Activnoqrc",
    layer_metal1noqrc: LayerSpec = "Metal1noqrc",
    layer_metal2noqrc: LayerSpec = "Metal2noqrc",
    layer_metal3noqrc: LayerSpec = "Metal3noqrc",
    layer_metal4noqrc: LayerSpec = "Metal4noqrc",
    layer_metal5noqrc: LayerSpec = "Metal5noqrc",
    layer_topmetal1noqrc: LayerSpec = "TopMetal1noqrc",
    layer_text: LayerSpec = "TEXTdrawing",
    layer_metal1pin: LayerSpec = "Metal1pin",
    layer_metal5pin: LayerSpec = "Metal5pin",
    layer_topmetal1pin: LayerSpec = "TopMetal1pin",
    layer_metal5label: LayerSpec = "Metal5label",
    layer_topmetal1label: LayerSpec = "TopMetal1label",
    layer_metal1label: LayerSpec = "Metal1label",
    model: str = 'rfcmim'
) -> Component:
    """Create a MIM (Metal-Insulator-Metal) capacitor isolated by a 
    bulk charge-drift encapsulation P-Plus guard-ring.

    Args:
        width: Width of the capacitor in micrometers.
        length: Length of the capacitor in micrometers.
        
        layer_metal5: Metal 5 drawing layer.
        layer_mim: MIM device drawing layer.
        layer_vmim: Vmim (MIM-TopMetal1 Via) drawing layer.
        layer_topmetal1: TopMetal1 drawing layer.
        layer_cap_mark: MemCap drawing layer.
        layer_m4nofill: Metal4 nofill logic layer.
        layer_m5nofill: Metal5 nofill logic layer.
        layer_tm1nofill: TopMetal1 nofill logic layer.
        layer_tm2nofill: TopMetal2 nofill logic layer.
        layer_text: TEXT drawing layer.
        layer_metal5label: Metal5 label logic layer.
        layer_topmetal1label: TopMetal1 label logic layer.
        layer_metal5pin: Metal5 pin logic layer.
        layer_topmetal1pin: TopMetal1 pin logic layer.

        model: Device model name.

    Returns:
        Component with MIM capacitor layout.
    Raises:
    """

    c = Component()
    
    cap = cmim(
        width=width,
        length=length,
        layer_metal5=layer_metal5,
        layer_mim=layer_mim,
        layer_vmim=layer_vmim,
        layer_topmetal1=layer_topmetal1,
        layer_cap_mark=layer_cap_mark,
        layer_m4nofill=layer_m4nofill,
        layer_m5nofill=layer_m5nofill,
        layer_tm1nofill=layer_tm1nofill,
        layer_tm2nofill=layer_tm2nofill,
        layer_text=layer_text,
        layer_metal5pin=layer_metal5pin,
        layer_topmetal1pin=layer_topmetal1pin,
        layer_metal5label = layer_metal5label,
        layer_topmetal1label = layer_topmetal1label,
        model=model
    )
    c.info = cap.info
    c.add_ref(cap)
    c.ports = cap.ports
    # add pwell block
    size = c.bbox_np()
    size = size[1] - size[0]
    pwellblock_enc = 2.4
    pwell = gf.components.rectangle(
        size=(size[0] + 2*pwellblock_enc, size[1]+2*pwellblock_enc),
        layer=layer_pwellblock,
        centered=True,)
    ccenter = (c.x, c.y)
    pwell_ref = c.add_ref(pwell)
    pwell_ref.x = ccenter[0]
    pwell_ref.y = ccenter[1]

    # add p guard ring
    pguardring_seq = 0.6
    pguardring_width = 2.0
    c.add_ref(guard_ring(
        width = pguardring_width,
        guardRingSpacing = pguardring_seq,
        guardRingType = 'psub',
        bbox = tuple(tuple(p) for p in c.bbox_np()),
        path = None,
        layer_activ = layer_activ,
        layer_cont = layer_cont,
        layer_metal1 = layer_metal1,
        layer_psd = layer_psd,))
    
    logic_layers = [
        layer_activnoqrc,
        layer_metal1noqrc,
        layer_metal2noqrc,
        layer_metal3noqrc,
        layer_metal4noqrc,
        layer_metal5noqrc,
        layer_topmetal1noqrc
    ]

    size = c.bbox_np()
    size = size[1] - size[0]
    ccenter = (c.x, c.y)
    for layer_spec in logic_layers:
        ll = gf.components.rectangle(
            size=(size[0], size[1]),
            layer=layer_spec,
            centered=True,)
        ref = c.add_ref(ll)
        ref.x = ccenter[0]
        ref.y = ccenter[1]

    gr_drc = {
        'active_min_enclose_pp': 0.14,
    }

    # add TIE LOW pin
    tie_low = gf.components.rectangle(
        size=(size[0] - 2*gr_drc['active_min_enclose_pp'], pguardring_width),
        layer=layer_metal1pin,
        centered=True,)
    xmin, ymin = c.xmin, c.ymin
    tie_low_ref = c.add_ref(tie_low)
    tie_low_ref.xmin = xmin + gr_drc['active_min_enclose_pp']
    tie_low_ref.ymin = ymin + gr_drc['active_min_enclose_pp']
    
    tie = c.add_port(
        name="TIE_LOW",
        center=(tie_low_ref.x, tie_low_ref.y),
        width=pguardring_width,
        orientation=0,
        layer=layer_metal1,
        port_type="electrical",
    )
    c.add_label(
        text="TIE_LOW",
        position=(tie.x, tie.y),
        layer=layer_metal1label
    )
    c.add_label(
        text="TIE_LOW",
        position=(tie.x, tie.y),
        layer=layer_text
    )

    c.info['model'] = model

    return c


if __name__ == "__main__":
    from math import isclose
    
    # capacitance in femto farad

    c = cmom(nfingers=2)
    assert isclose(c.info['capacitance'],3.8016)
    c.show()

    c2 = cmom(nfingers=4)
    assert c2.info['capacitance'] >= 2*c.info['capacitance']
    assert isclose(c2.info['capacitance'],7.5733)
    c2.show()


if __name__ == "__main__":
    from gdsfactory.difftest import xor

    from ihp import PDK, cells2

    PDK.activate()

    # Test the components
    c0 = cells2.cmim()  # original
    c1 = cmim()  # New
    # c = gf.grid([c0, c1], spacing=100)
    c = xor(c0, c1)
    c.show()

    # c0 = fixed.rfcmim()  # original
    # c1 = rfcmim()  # New
    # # c = gf.grid([c0, c1], spacing=100)
    # c = xor(c0, c1)
    # c.show()
