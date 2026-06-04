import gdsfactory as gf
from gdsfactory.cross_section import port_names_electrical, port_types_electrical
from gdsfactory.typings import CrossSectionSpec, LayerSpec, Size

from math import cosh, exp, log, pi, sin, sinh, sqrt, asin

from scipy.constants import c

from ihp.cells.waveguides import _calculate_effective_dielectric_constant, _calculate_width_from_Z0, _get_stack_geometry, tline, coupler_tline, tline_corner
from .. import tech


def _estimate_rppd_length(resistance_ohm: float, width_um: float, sheet_res_ohm_per_sq: float = 300.0) -> float:
    """Estimate rppd length from target resistance using upstream resistor model constants."""
    if resistance_ohm <= 0 or width_um <= 0:
        return 0.5
    return max(resistance_ohm * width_um / sheet_res_ohm_per_sq, 0.5)



@gf.cell
def branch_line_coupler(
    connection_length: float = 100,
    frequency: float = 10e9,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "topmetal1_routing",
    Z0: float = 50,
    e_r: float = 4.1
) -> gf.Component:
    """Returns a branch line coupler coplanar transmission line.

    Creates signal and ground lines for a branch line coupler.
    
    Args:
        connection_length: Length of the input line.
        frequency: Operating frequency (Hz).
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
        Z0: Target characteristic impedance (ohms).
        e_r: Relative permittivity of the substrate. Defaults to 4.1 for silicon dioxide.
    """
    wave_length = 3e8 / frequency * 1e6  
    
    c = gf.Component()

    corner = gf.Component()

    # calculate the needed widths
    width_Z0 = _calculate_width_from_Z0(
        Z0=Z0, 
        ground_cross_section=ground_cross_section, 
        signal_cross_section=signal_cross_section,
        e_r=e_r
    )  
    width_Z0_sqrt2 = _calculate_width_from_Z0(
        Z0=Z0/sqrt(2), 
        ground_cross_section=ground_cross_section, 
        signal_cross_section=signal_cross_section,
        e_r=e_r
    ) 
    e_eff = _calculate_effective_dielectric_constant(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        e_r=e_r
    )
    
    quater_wave_length = wave_length / 4  / sqrt(e_eff)  
    quater_wave_length = quater_wave_length - quater_wave_length % (tech.nm)  # truncate to 5 nm
    
    # create corner component for the 4 corners of the coupler
    corner.add_polygon(
        points=[
            (0, 0),
            (0, width_Z0),
            (width_Z0-(width_Z0_sqrt2 - width_Z0), width_Z0),
            (width_Z0, width_Z0_sqrt2),
            (width_Z0, 0)
        ],
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    corner.add_port(
        name="e1",
        center=(width_Z0/2, 0),
        width=width_Z0,
        orientation=270,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    corner.add_port(
        name="e2",
        center=(width_Z0, width_Z0_sqrt2/2),
        width=width_Z0_sqrt2,
        orientation=0,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    corner.add_port(
        name="e3",
        center=(0, width_Z0/2),
        width=width_Z0,
        orientation=180,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )

    # start with the top left corner
    corner_nw = c.add_ref(corner)

    # create and connect the top Z0/sqrt(2) transmission line
    tline_top = c.add_ref(tline(
        length=quater_wave_length - width_Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0_sqrt2,
    ))   
    
    tline_top.connect(
        "e1", corner_nw.ports["e2"]
    )
    
    # create and connect the top right corner
    corner_ne = c.add_ref(corner).mirror(p1=(0,0), p2=(0,1))

    corner_ne.connect(
        "e2", tline_top.ports["e2"]
    )

    # create and connect the left Z0 transmission line
    tline_left = c.add_ref(tline(
        length=quater_wave_length - width_Z0_sqrt2,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))

    tline_left.connect(
        "e1", corner_nw.ports["e1"]
    )

    # create and connect the bottom left corner
    corner_sw = c.add_ref(corner).mirror(p1=(0,0), p2=(1,0))

    corner_sw.connect(
        "e1", tline_left.ports["e2"]
    )

    # create and connect the bottom Z0/sqrt(2) transmission line
    tline_bottom = c.add_ref(tline(
        length=quater_wave_length - width_Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0_sqrt2,
    ))

    tline_bottom.connect(
        "e1", corner_sw.ports["e2"]
    )

    # create and connect the bottom right corner
    corner_se = c.add_ref(corner).mirror(p1=(0,0), p2=(1,0)).mirror(p1=(0,0), p2=(0,1))

    corner_se.connect(
        "e2", tline_bottom.ports["e2"]
    )

    # create and connect the right Z0 transmission line
    tline_right = c.add_ref(tline(
        length=quater_wave_length - width_Z0_sqrt2,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))

    tline_right.connect(
        "e1", corner_ne.ports["e1"]
    )

    # create and connect input/output lines
    connection1 = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))

    connection1.connect(
        "e1", corner_nw.ports["e3"]
    )

    connection2 = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))

    connection2.connect(
        "e1", corner_ne.ports["e3"]
    )

    connection3 = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))

    connection3.connect(
        "e1", corner_se.ports["e3"]
    )

    connection4 = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))

    connection4.connect(
        "e1", corner_sw.ports["e3"]
    )

    # add ports to the component
    c.add_port(name = "e1", port=connection1.ports["e2"])
    c.add_port(name = "e2", port=connection2.ports["e2"])
    c.add_port(name = "e3", port=connection3.ports["e2"])
    c.add_port(name = "e4", port=connection4.ports["e2"])
    
    return c


@gf.cell
def wilkinson_power_divider(
    connection_length: float = 50,
    frequency: float = 30e9,
    Z0: float = 50,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec | list[CrossSectionSpec] = "topmetal1_routing",
    shape: str = "C",
    e_r: float = 4.1,
) -> gf.Component:
    """Return a Wilkinson power divider coplanar transmission line.

    Constructs a two-way Wilkinson divider from quarter-wave transformer
    branches (impedance $Z_0 / sqrt{2}$) arranged in a loop.  The
    quarter-wave length is derived from *frequency* and the effective
    dielectric constant of the selected cross-section stack.

    Args:
        connection_length: Length of the input/output feed lines (um).
        frequency: Operating frequency (Hz).
        Z0: Target characteristic impedance of the input/output ports
            (ohms).
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
            Accepts a single spec for microstrip or a two-element list
            ``[lower, upper]`` for stripline.
        shape: Shape of the Wilkinson divider. Can be either "C" or "U". In a "C" shape, the quarter-wave branches are connected in a loop, while in a "U" shape, the branches are not braught together again
    Returns:
        A Component containing the Wilkinson power divider with ports
        ``e1`` (input), ``e2`` and ``e3`` (outputs).
    """

    

    c = gf.Component()

    # calculate the needed widths
    width_Z0 = _calculate_width_from_Z0(
        Z0=Z0, 
        ground_cross_section=ground_cross_section, 
        signal_cross_section=signal_cross_section,
        e_r=e_r,
    )
    width_Z0_sqrt2  = _calculate_width_from_Z0(
        Z0=Z0*sqrt(2), 
        ground_cross_section=ground_cross_section, 
        signal_cross_section=signal_cross_section,
        e_r=e_r
    )
    
    # create and connect the input line
    connection_in = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        width=width_Z0,
    ))   
    
    # calculate the quarter wave length for the given frequency and cross-section
    e_eff = _calculate_effective_dielectric_constant(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        e_r=e_r
    )
    wave_length = 3e8 / frequency * 1e6 / sqrt(e_eff)  # in um, assuming effective index of 3.5
    quater_wave_length = wave_length / 4
    quater_wave_length = quater_wave_length - quater_wave_length % (tech.nm)  # truncate to 5 nm


    # for future use
    width_R = 100
    length_R = _estimate_rppd_length(resistance_ohm=2 * Z0, width_um=width_R)
    
    
    
    
    # create and connect the corner piece for the connection line
    connection_corner = gf.Component()
    
    connection_corner.add_polygon(
        points=[
            (0, 0),
            (0, width_Z0),
            (width_Z0_sqrt2, width_Z0),
            (width_Z0_sqrt2, 0)
        ],
        layer=gf.get_cross_section(signal_cross_section).layer,
        
    )
    connection_corner.add_port(
        name="e1",
        center=(0, width_Z0/2),
        width=width_Z0,
        orientation=180,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    connection_corner.add_port(
        name="e2",
        center=(width_Z0_sqrt2/2, width_Z0),
        width=width_Z0_sqrt2,
        orientation=90,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    connection_corner.add_port(
        name="e3",
        center=(width_Z0_sqrt2/2, 0),
        width=width_Z0_sqrt2,
        orientation=270,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    
    
    connection_corner_ref = c.add_ref(connection_corner)
    
    connection_corner_ref.connect(
        "e1", connection_in.ports["e2"]
    )
    
    if shape == "C":
        
        # Calculate the circumference of the square
        circumference = quater_wave_length * 2  + length_R
    
        # create and connect upper branch line
        branch_left_up = c.add_ref(tline(
            length= circumference/8 - width_Z0_sqrt2 - width_Z0/2,  
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width_Z0_sqrt2,))
        
        branch_left_up.connect(
            "e1", connection_corner_ref.ports["e2"]
        )
        
        corner_piece_upper_left = c.add_ref(tline_corner(
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            Z0=Z0*sqrt(2)
        ))
        corner_piece_upper_left.connect(
            "e2", branch_left_up.ports["e2"]
        )
        
        branch_left_down = c.add_ref(tline(
            length= circumference/8 - width_Z0_sqrt2 - width_Z0/2,  
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width_Z0_sqrt2,))
        
        branch_left_down.connect(
            "e1", connection_corner_ref.ports["e3"]
        )
        
        corner_piece_lower_left = c.add_ref(tline_corner(
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            Z0=Z0*sqrt(2)
        ))
        corner_piece_lower_left.connect(
            "e1", branch_left_down.ports["e2"]
        )
        
        branch_top = c.add_ref(tline(
            length= circumference/4 - width_Z0_sqrt2*2,  
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width_Z0_sqrt2,))
        
        branch_top.connect(
            "e1", corner_piece_upper_left.ports["e1"]
        )
        
        branch_bottom = c.add_ref(tline(
            length= circumference/4 - width_Z0_sqrt2*2,  
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width_Z0_sqrt2,))
        
        branch_bottom.connect(
            "e1", corner_piece_lower_left.ports["e2"]
        )
        
        corner_piece_upper_right = c.add_ref(tline_corner(
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            Z0=Z0*sqrt(2)
        ))
        
        corner_piece_upper_right.connect(
            "e2", branch_top.ports["e2"]
        )
        
        branch_right_down = c.add_ref(tline(
            length= circumference/8 - width_Z0_sqrt2*2 - length_R/2,
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width_Z0_sqrt2,))
        
        branch_right_down.connect(
            "e1", corner_piece_upper_right.ports["e1"]
        )
        
        corner_piece_lower_right = c.add_ref(tline_corner(
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            Z0=Z0*sqrt(2)
        ))
        corner_piece_lower_right.connect(
            "e1", branch_bottom.ports["e2"]
        )
        
        branch_right_up = c.add_ref(tline(
            length= circumference/8 - width_Z0_sqrt2*2 - length_R/2,
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width_Z0_sqrt2,))
        
        branch_right_up.connect(
            "e1", corner_piece_lower_right.ports["e2"]
        )
        
        corner_output_p2 = c.add_ref(tline_corner(
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            Z0=Z0*sqrt(2)
        ))
        corner_output_p2.connect(
            "e1", branch_right_down.ports["e2"]
        )
        
        corner_output_p3 = c.add_ref(tline_corner(
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            Z0=Z0*sqrt(2)
        ))
        corner_output_p3.connect(
            "e2", branch_right_up.ports["e2"]
        )
        
        connection_out_p2 = c.add_ref(tline(
            length=connection_length,
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width_Z0,
        ))
        
        connection_out_p2.connect(
            "e1", corner_output_p2.ports["e2"], allow_width_mismatch=True
        )
        connection_out_p2.movey(width_Z0/2 - width_Z0_sqrt2/2)
        
        connection_out_p3 = c.add_ref(tline(
            length=connection_length,
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width_Z0,
        ))
        
        connection_out_p3.connect(
            "e1", corner_output_p3.ports["e1"], allow_width_mismatch=True
        )
        connection_out_p3.movey(-(width_Z0/2 - width_Z0_sqrt2/2))
        
        c.add_port(name="e1", port=connection_in.ports["e1"])
        c.add_port(name="e2", port=connection_out_p2.ports["e2"])
        c.add_port(name="e3", port=connection_out_p3.ports["e2"])
        
    
    elif shape == "U":
        # Calculate the circumference of the square
        circumference = quater_wave_length * 2
    
         # create and connect upper branch line
        branch_left_up = c.add_ref(tline(
            length= circumference/6 - width_Z0_sqrt2 - width_Z0/2,  
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width_Z0_sqrt2,))
        
        branch_left_up.connect(
            "e1", connection_corner_ref.ports["e2"]
        )
        
        corner_piece_upper_left = c.add_ref(tline_corner(
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            Z0=Z0*sqrt(2)
        ))
        corner_piece_upper_left.connect(
            "e2", branch_left_up.ports["e2"]
        )
        
        branch_left_down = c.add_ref(tline(
            length= circumference/6 - width_Z0_sqrt2 - width_Z0/2,  
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width_Z0_sqrt2,))
        
        branch_left_down.connect(
            "e1", connection_corner_ref.ports["e3"]
        )
        
        corner_piece_lower_left = c.add_ref(tline_corner(
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            Z0=Z0*sqrt(2)
        ))
        corner_piece_lower_left.connect(
            "e1", branch_left_down.ports["e2"]
        )
        
        branch_top = c.add_ref(tline(
            length= circumference/3 - width_Z0_sqrt2*2,  
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width_Z0_sqrt2,))
        
        branch_top.connect(
            "e1", corner_piece_upper_left.ports["e1"]
        )
        
        branch_bottom = c.add_ref(tline(
            length= circumference/3 - width_Z0_sqrt2*2,  
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width_Z0_sqrt2,))
        
        branch_bottom.connect(
            "e1", corner_piece_lower_left.ports["e2"]
        )
        
        corner_output_p2 = c.add_ref(tline_corner(
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            Z0=Z0*sqrt(2)
        ))
        corner_output_p2.connect(
            "e1", branch_top.ports["e2"]
        )
        
        corner_output_p3 = c.add_ref(tline_corner(
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            Z0=Z0*sqrt(2)
        ))
        corner_output_p3.connect(
            "e2", branch_bottom.ports["e2"]
        )
        
        connection_out_p2 = c.add_ref(tline(
            length=connection_length,
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width_Z0,
        ))
        
        connection_out_p2.connect(
            "e1", corner_output_p2.ports["e2"], allow_width_mismatch=True
        )
        connection_out_p2.movex(-width_Z0/2 + width_Z0_sqrt2/2)
        
        connection_out_p3 = c.add_ref(tline(
            length=connection_length,
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            width=width_Z0,
        ))
        
        connection_out_p3.connect(
            "e1", corner_output_p3.ports["e1"], allow_width_mismatch=True
        )
        connection_out_p3.movex(-width_Z0/2 + width_Z0_sqrt2/2)
        
        c.add_port(name="e1", port=connection_in.ports["e1"])
        c.add_port(name="e2", port=connection_out_p2.ports["e2"])
        c.add_port(name="e3", port=connection_out_p3.ports["e2"])
        
    else:
        
        raise ValueError("Invalid shape. Must be either 'C' or 'U'.")
    
    # for future use, add the resistor in the middle of the coupler
    # c.add_ref(rppd(
    #     length=length_R,
    #     width=width_R,
    #     polySpace=0.18,
    #     bends=0
    # ))
    
    return c


@gf.cell
def directional_coupler(
    connection_length: float = 100,
    frequency: float = 10e9,
    coupling_factor: float = 3,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "topmetal1_routing",
    Z0: float = 50,
    e_r: float = 4.1
) -> gf.Component:
    """Returns a directional coupler coplanar transmission line.

    Creates signal and ground lines for a directional coupler.
    
    Args:
        connection_length: Length of the input line.
        frequency: Operating frequency (Hz).
        coupling_factor: Coupling factor in dB.
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
        Z0: Target characteristic impedance (ohms).
        e_r: Relative permittivity of the substrate. Defaults to 4.1 for silicon dioxide.
    """
    wave_length = c / frequency * 1e6  
    
    c = gf.Component()
    
    e_eff = _calculate_effective_dielectric_constant(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        e_r=e_r
    )
    
    quater_wave_length = wave_length / 4  / sqrt(e_eff)  
    quater_wave_length = quater_wave_length - quater_wave_length % (tech.nm)  # truncate to 5 nm
    
    # couping factor must be negative
    if coupling_factor > 0:
        coupling_factor = -coupling_factor  # enforce negative coupling factor for the formula below
        
    coupling_factor_linear = 10 ** (coupling_factor / 20)
    
    # create the first line of the coupler
    coupled_lines = c.add_ref(coupler_tline(
        Z0e= Z0 * (1 + coupling_factor_linear) / (1 - coupling_factor_linear),
        Z0o= Z0 * (1 - coupling_factor_linear) / (1 + coupling_factor_linear),
        length=quater_wave_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    ))
    
    # create and connect the input line
    connection_port1 = c.add_ref(tline(
        length=connection_length,
        Z0=Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    ))
    connection_port1.connect("e1", coupled_lines.ports["e1"])
    # create and connect the through port line
    connection_port2 = c.add_ref(tline(
        length=connection_length,
        Z0=Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    ))
    connection_port2.connect("e1", coupled_lines.ports["e2"])
    
    corner_left = c.add_ref(tline_corner(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        Z0=Z0,
    ))
    
    corner_left.connect("e1", coupled_lines.ports["e4"])
    connection_port4 = c.add_ref(tline(
        length=connection_length,
        Z0=Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    ))
    
    corner_right = c.add_ref(tline_corner(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        Z0=Z0,
    ))
    connection_port4.connect("e1", corner_left.ports["e2"])
    
    corner_right.connect("e1", coupled_lines.ports["e3"])
    connection_port3 = c.add_ref(tline(
        length=connection_length,
        Z0=Z0,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    ))
    connection_port3.connect("e1", corner_right.ports["e4"])
    
    
    
    c.add_port(name="e1", port=connection_port1.ports["e2"])
    c.add_port(name="e2", port=connection_port2.ports["e2"])
    c.add_port(name="e3", port=connection_port3.ports["e2"])
    c.add_port(name="e4", port=connection_port4.ports["e2"])
    c.flatten()
    return c


@gf.cell
def quarter_wave_transformer(
    connection_length: float = 100,
    frequency: float = 50e9,
    Z_in: float = 50,
    Z_L: float = 100,
    signal_cross_section: CrossSectionSpec = "topmetal2_routing",
    ground_cross_section: CrossSectionSpec = "topmetal1_routing",
    e_r: float = 4.1
) -> gf.Component:
    """Returns a quarter-wave transformer coplanar transmission line.

    Creates a quarter-wave transformer for impedance matching between an
    input impedance Z_in and a load impedance Z_L at a given frequency.
    
    Args:
        connection_length: Length of the input line.
        frequency: Operating frequency (Hz).
        Z_in: Characteristic impedance of the input line (ohms).
        Z_L: Load impedance to be matched (ohms).
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
        e_r: Relative permittivity of the substrate. Defaults to 4.1 for silicon dioxide.
    """
    wave_length = c / frequency * 1e6  
    
    c = gf.Component()
    
    e_eff = _calculate_effective_dielectric_constant(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        e_r=e_r
    )
    
    quater_wave_length = wave_length / 4  / sqrt(e_eff)  
    quater_wave_length = quater_wave_length - quater_wave_length % (tech.nm)  # truncate to 5 nm
    
    Z0_transformer = sqrt(Z_in * Z_L)
    
    transformer_line = c.add_ref(tline(
        length=quater_wave_length,
        Z0=Z0_transformer,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    ))
    
    connection_port1 = c.add_ref(tline(
        length=connection_length,
        Z0=Z_in,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    ))
    
    connection_port1.connect("e1", transformer_line.ports["e1"], allow_width_mismatch=True)
    
    connection_port2 = c.add_ref(tline(
        length=connection_length,
        Z0=Z_L,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
    ))
    
    connection_port2.connect("e1", transformer_line.ports["e2"], allow_width_mismatch=True)
    
    c.add_port(name="e1", port=connection_port1.ports["e2"])
    c.add_port(name="e2", port=connection_port2.ports["e2"])
    
    return c


def _butterworth_prototype(N: int) -> list[float]:
    """Return Butterworth lowpass prototype element values g_0 … g_{N+1}."""
    # g = [1.0]
    g = []
    for k in range(1, N + 1):
        g.append(2 * sin((2 * k - 1) * pi / (2 * N)))
    g.append(1.0)
    return g


def _chebyshev_prototype(N: int, ripple_dB: float) -> list[float]:
    """Return Chebyshev lowpass prototype element values g_1 … g_{N+1}.

    Uses the standard recursion from Pozar / Matthaei-Young-Jones.

    Args:
        N: Filter order.
        ripple_dB: Pass-band ripple in dB (must be > 0).
    """
    x = ripple_dB / 17.37
    beta = log(cosh(x) / sinh(x))  # ln(coth(x))
    gamma = sinh(beta / (2 * N))

    a = [0.0] * (N + 1)
    b = [0.0] * (N + 1)
    for k in range(1, N + 1):
        a[k] = sin((2 * k - 1) * pi / (2 * N))
        b[k] = gamma ** 2 + sin(k * pi / N) ** 2

    g = []
    # g_1
    g.append(2 * a[1] / gamma)
    # g_2 ... g_N
    for k in range(2, N + 1):
        g.append(4 * a[k - 1] * a[k] / (b[k - 1] * g[-1]))
    # g_{N+1}
    if N % 2 == 1:
        g.append(1.0)
    else:
        g.append((cosh(beta / 4) / sinh(beta / 4)) ** 2)  # coth²(β/4)

    return g


@gf.cell
def coupled_line_bandpass_filter(
        order: int = 3,
        frequency: float = 10e9,
        bandwidth: float = 1e9,
        connection_length: float = 50,
        Z0: float = 50,
        signal_cross_section: CrossSectionSpec = "topmetal2_routing",
        ground_cross_section: CrossSectionSpec = "topmetal1_routing",
        e_r: float = 4.1,
        filter_type: str = "butter",
        ripple_dB: float = 3,
    ) -> gf.Component:
    """Return a coupled-line bandpass filter.

    Synthesises an *N*-th order coupled-line bandpass filter from
    Butterworth or Chebyshev lowpass prototype coefficients.  Each
    section is realised as a pair of coupled coplanar transmission
    lines whose even/odd-mode impedances are derived from the
    prototype element values and the fractional bandwidth.

    Args:
        order: Filter order (number of resonators).
        frequency: Centre frequency (Hz).
        bandwidth: Absolute bandwidth (Hz).
        connection_length: Length of the input/output feed lines (um).
        Z0: Reference characteristic impedance (ohms).
        signal_cross_section: Cross-section for the signal line.
        ground_cross_section: Cross-section for the ground line.
        e_r: Relative permittivity of the substrate.
            Defaults to 4.1 for silicon dioxide.
        filter_type: Prototype type — ``"butter"`` for Butterworth or
            ``"cheby"`` for Chebyshev.
        ripple_dB: Pass-band ripple in dB (only used when
            *filter_type* is ``"cheby"``).

    Returns:
        A Component with ports ``e1`` (input) and ``e2`` (output).
    """

    c = gf.Component()
    # get filter coefficients
    # g = [g1 g2 ... gN gN+1] for N-th order filter
    if filter_type == "butter":
        g = _butterworth_prototype(order)
    elif filter_type == "cheby":
        g = _chebyshev_prototype(order, ripple_dB)

    

    fractional_bandwidth = bandwidth / frequency
    f_2 = frequency * (1 + fractional_bandwidth / 2)
    f_1 = frequency * (1 - fractional_bandwidth / 2)
    
    delta = fractional_bandwidth


    # initialize lists for Z0J values
    Z0J = [0.0] * (order + 1)

    # first Z0J value
    Z0J[0] = sqrt(pi * delta / (2 * g[0]))

    # calculate Z0J values for j = 1 to N-1
    for j in range(1, order):
        Z0J[j] = pi * delta / (2 * sqrt(g[j-1] * g[j]))

    # last Z0J value 
    Z0J[order] = sqrt(pi * delta / (2 * g[order-1] * g[order]))


    # initialize and calculate Z0e and Z0o values for each section
    Z0e = [0.0] * (order + 1)
    Z0o = [0.0] * (order + 1)
    Z_section = [0.0] * (order + 1)
    
    for j in range(order + 1):
        Z0e[j] = Z0 * (1 + Z0J[j] + Z0J[j] ** 2)
        Z0o[j] = Z0 * (1 - Z0J[j] + Z0J[j] ** 2)
        
        Z_section[j] = sqrt(Z0e[j] * Z0o[j])
    
    # calculate the coupling coefficient k for each section
    g = [1.0] + g  # prepend g0 = 1.0 for easier indexing
    k = [0.0] * (order + 1)
    for j in range(order + 1):
        k[j] = (f_2 - f_1) / sqrt(f_1 * f_2 * g[j] * g[j+1])

    e_eff = _calculate_effective_dielectric_constant(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        e_r=e_r,
    )
    segment_length = scipy.constants.c / frequency * 1e6 / sqrt(e_eff) / 4
    segment_length = segment_length - segment_length % tech.nm  # snap to grid

    connection_in = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        Z0=Z0,
    ))

    connection_out = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        Z0=Z0,
    ))

    previous_section = connection_in

    for i in range(order + 1):
        section_i = c.add_ref(coupler_tline(
            Z0e=Z0e[i],
            Z0o=Z0o[i],
            length=segment_length, 
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
        ))
        section_i.connect("e4", previous_section.ports["e2"], allow_width_mismatch=True)
        previous_section = section_i

    connection_out.connect("e1", previous_section.ports["e2"], allow_width_mismatch=True)
    
    c.add_port(name="e1", port=connection_in.ports["e1"])
    c.add_port(name="e2", port=connection_out.ports["e2"])

    c.flatten()
    
    return c


@gf.cell
def _corner_rectangle(
    width: float,
    length: float,
    cross_section: CrossSectionSpec = "topmetal2_routing",
) -> gf.Component:
    """Return a corner rectangle.

    Args:
        width: width of the rectangle.
        length: length of the rectangle.
        cross_section: cross section of the rectangle.
    """
    c = gf.Component()
    c.add_ref(gf.components.rectangle(
        size=(length, width),
        layer=gf.get_cross_section(cross_section).layer,
    ))
    
    c.add_port(
        name="e1",
        center=(length/2, width),
        width=length,
        orientation=90,
        port_type="electrical",
        layer=gf.get_cross_section(cross_section).layer,
    )
    c.add_port(
        name="e2",
        center=(length, width/2),
        width=width,
        orientation=0,
        port_type="electrical",
        layer=gf.get_cross_section(cross_section).layer,
    )
    c.add_port(
        name="e3",
        center=(length/2, 0),
        width=length,
        orientation=270,
        port_type="electrical",
        layer=gf.get_cross_section(cross_section).layer,
    )
    c.add_port(
        name="e4",
        center=(0, width/2),
        width=width,
        orientation=180,
        port_type="electrical",
        layer=gf.get_cross_section(cross_section).layer,
    )
    return c


@gf.cell
def hairpin_coupled_line_bandpass_filter(
        order: int = 3,
        frequency: float = 10e9,
        bandwidth: float = 1e9,
        connection_length: float = 50,
        Z0: float = 50,
        signal_cross_section: CrossSectionSpec = "topmetal2_routing",
        ground_cross_section: CrossSectionSpec = "topmetal1_routing",
        e_r: float = 4.1,
        filter_type: str = "butter",
        ripple_dB: float = 3,
    ) -> gf.Component:
    """Return a hairpin-coupled-line bandpass filter.

    Synthesises an *N*-th order hairpin-coupled-line bandpass filter from
    
    
    
    """
    
    c = gf.Component()
    # get filter coefficients
    # g = [g1 g2 ... gN gN+1] for N-th order filter
    if filter_type == "butter":
        g = _butterworth_prototype(order)
    elif filter_type == "cheby":
        g = _chebyshev_prototype(order, ripple_dB)

    

    fractional_bandwidth = bandwidth / frequency
    f_2 = frequency * (1 + fractional_bandwidth / 2)
    f_1 = frequency * (1 - fractional_bandwidth / 2)
    
    delta = fractional_bandwidth


    # initialize lists for Z0J values
    Z0J = [0.0] * (order + 1)

    # first Z0J value
    Z0J[0] = sqrt(pi * delta / (2 * g[0]))

    # calculate Z0J values for j = 1 to N-1
    for j in range(1, order):
        Z0J[j] = pi * delta / (2 * sqrt(g[j-1] * g[j]))

    # last Z0J value 
    Z0J[order] = sqrt(pi * delta / (2 * g[order-1] * g[order]))


    # initialize and calculate Z0e and Z0o values for each section
    Z0e = [0.0] * (order + 1)
    Z0o = [0.0] * (order + 1)
    Z_section = [0.0] * (order + 1)
    
    for j in range(order + 1):
        Z0e[j] = Z0 * (1 + Z0J[j] + Z0J[j] ** 2)
        Z0o[j] = Z0 * (1 - Z0J[j] + Z0J[j] ** 2)
        
        Z_section[j] = sqrt(Z0e[j] * Z0o[j])
    
    # calculate the coupling coefficient k for each section
    g = [1.0] + g  # prepend g0 = 1.0 for easier indexing
    k = [0.0] * (order + 1)
    for j in range(order + 1):
        k[j] = (f_2 - f_1) / sqrt(f_1 * f_2 * g[j] * g[j+1])

    e_eff = _calculate_effective_dielectric_constant(
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        e_r=e_r,
    )
    
    width_Z0 = _calculate_width_from_Z0(
        Z0=Z0, 
        ground_cross_section=ground_cross_section, 
        signal_cross_section=signal_cross_section,
        e_r=e_r
    )
    
    segment_length = c / frequency * 1e6 / sqrt(e_eff) / 4
    segment_length = segment_length - segment_length % tech.nm  # snap to grid
    
    input_line = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        Z0=Z0,
    ))
    
    first_vertical_line = tline(
        length=segment_length - 2 * width_Z0,  # adjust length to account for the port at the end
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        Z0=Z0,
    ).copy()
    # copy to be able to add port
    
    # from Microstrip Filters for RF/Microwave Applications by Jia-Sheng Hong, M. J. Lancaster
    t = 2*segment_length/scipy.constants.pi * asin(sqrt((fractional_bandwidth)/(g[1])))
    
    first_vertical_line.add_port(
        name="e3",
        center=(segment_length-t, -width_Z0/2),
        width=width_Z0,
        orientation=270,
        port_type="electrical",
        layer=gf.get_cross_section(signal_cross_section).layer,
    )
    
    first_vertical_line_ref = c.add_ref(first_vertical_line)
    
    
    first_vertical_line_ref.connect("e3", input_line.ports["e2"])
    
    previous_line_ref = first_vertical_line_ref
    

    for i in range(order + 1):
        section_i = c.add_ref(coupler_tline(
            Z0e=Z0e[i],
            Z0o=Z0o[i],
            length=segment_length - 2 * width_Z0,  # adjust length to account for the port at the end
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
        ))
        corner_l = c.add_ref(_corner_rectangle(
            width=width_Z0,
            length=previous_line_ref.ports["e3"].width,
            cross_section=signal_cross_section,
        ))
        
        connection_i = c.add_ref(tline(
            length=previous_line_ref.ports["e2"].width + section_i.ports["e3"].width,  # arbitrary length to connect the horizontal line to the coupler, can be adjusted for better performance
            signal_cross_section=signal_cross_section,
            ground_cross_section=ground_cross_section,
            Z0=Z0,
        ))
        
        corner_r = c.add_ref(_corner_rectangle(
            width=width_Z0,
            length=section_i.ports["e3"].width,
            cross_section=signal_cross_section,
        ))
        
        if i % 2 == 0:
            corner_l.connect("e1", previous_line_ref.ports["e2"])
            connection_i.connect("e1", corner_l.ports["e2"])
            corner_r.connect("e4", connection_i.ports["e2"])
            
            section_i.connect("e3", corner_r.ports["e1"])
        else:
            corner_l.connect("e3", previous_line_ref.ports["e1"])
            connection_i.connect("e1", corner_l.ports["e2"])
            corner_r.connect("e4", connection_i.ports["e2"])
            
            section_i.connect("e4", corner_r.ports["e3"])
        
        previous_line_ref = section_i
       
        
    corner_l = c.add_ref(_corner_rectangle(
            width=width_Z0,
            length=previous_line_ref.ports["e3"].width,
            cross_section=signal_cross_section,
        )) 
    
    
        
    connection_i = c.add_ref(tline(
        length=previous_line_ref.ports["e2"].width + width_Z0,  # arbitrary length to connect the horizontal line to the coupler, can be adjusted for better performance
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        Z0=Z0,
    ))
    
    
    
    corner_r = c.add_ref(_corner_rectangle(
        width=width_Z0,
        length=width_Z0,
        cross_section=signal_cross_section,
    ))

    last_vertical_line_ref = c.add_ref(first_vertical_line)
    
    
    
    output_line = c.add_ref(tline(
        length=connection_length,
        signal_cross_section=signal_cross_section,
        ground_cross_section=ground_cross_section,
        Z0=Z0,
    ))
    
    if order % 2 == 1:
        last_vertical_line_ref.mirror()
        corner_l.connect("e1", previous_line_ref.ports["e2"])
        connection_i.connect("e1", corner_l.ports["e2"])
        corner_r.connect("e4", connection_i.ports["e2"])
        last_vertical_line_ref.connect("e2", corner_r.ports["e1"])
        
        output_line.connect("e1", last_vertical_line_ref.ports["e3"])
    else:
        corner_l.connect("e3", previous_line_ref.ports["e1"])
        connection_i.connect("e1", corner_l.ports["e2"])
        corner_r.connect("e4", connection_i.ports["e2"])
            
        last_vertical_line_ref.connect("e2", corner_r.ports["e3"])
        
        output_line.connect("e1", last_vertical_line_ref.ports["e3"])
    
    c.add_port(name="e1", port=input_line.ports["e1"])
    c.add_port(name="e2", port=output_line.ports["e2"])
        
    # c.add_port(name="e1", port=input_line.ports["e1"])
    
    return c