import numpy as _np
import pyg4ometry.gdml as _gd
import pyg4ometry.geant4 as _g4
import pyg4ometry.visualisation as _vi
from dataclasses import dataclass

# === Constants ===
WORLD_DIMENSIONS = 10000.0  # mm

# CYLINDER DIMENSIONS
CYLINDER_MATERIAL = "G4_GRAPHITE"
CYLINDER_RADIUS = 300.0
CYLINDER_HALF_THICKNESS = 10.0

# CYLINDER POSITIONS
LEADING_CYLINDER_Z_POSITION = 0.0
SECOND_CYLINDER_Z_POSITION = 5000.0 + LEADING_CYLINDER_Z_POSITION # DISTANCE BETWEEN WINDOWS

# Stainless steel pipe dimensions
PIPE_MATERIAL = "G4_STAINLESS-STEEL"
PIPE_WINDOW_TOLERANCE = 2
PIPE_HALF_THICKNESS = 10
PIPE_INNER_RADIUS = CYLINDER_RADIUS + PIPE_WINDOW_TOLERANCE
PIPE_OUTER_RADIUS = CYLINDER_RADIUS + PIPE_WINDOW_TOLERANCE + PIPE_HALF_THICKNESS
PIPE_HALF_LENGTH = SECOND_CYLINDER_Z_POSITION
PIPE_Z_POSITION = + 1/2*SECOND_CYLINDER_Z_POSITION

# Argon tube (inner pipe) dimensions
ARGON_MATERIAL = "G4_Ar"
ARGON_INNER_RADIUS = 0.0
ARGON_OUTER_RADIUS = PIPE_INNER_RADIUS  # fills inside of stainless steel pipe
ARGON_HALF_LENGTH = PIPE_HALF_LENGTH
ARGON_Z_POSITION = PIPE_Z_POSITION

# Lead glass bars
BAR_CROSS_HALF = 150.0
BAR_LENGTH_HALF = 250.0
DISTANCE_FROM_PIPE_RADIUS = PIPE_OUTER_RADIUS + BAR_CROSS_HALF
DISTANCE_FROM_PIPE_Z_BARS = 0
N_BARS = 8

# Lead cube
LEAD_CUBE_DIMENSION = 1000
LEAD_CUBE_Z_POSITION = PIPE_HALF_LENGTH + PIPE_HALF_THICKNESS + 1/2*LEAD_CUBE_DIMENSION

# ---------- Dataclass for build config ----------
@dataclass
class GeometryConfig:
    build_world: bool = True
    build_leading_cylinder: bool = True
    build_sec_cylinder: bool = True
    build_pipe: bool = True
    build_argon_pipe: bool = False
    build_lead_glass_bars: bool = True
    build_lead_cube_dump: bool = True

# ---------- Registry ----------
def setup_registry():
    reg = _g4.Registry()
    zero = _gd.Constant("zero", 0.0, reg)
    twopi = _gd.Constant("twopi", "2*pi", reg)
    return reg, zero, twopi

# ---------- World ----------
def make_world(reg):
    world_solid = _g4.solid.Box(
        "world_solid",
        WORLD_DIMENSIONS,
        WORLD_DIMENSIONS,
        WORLD_DIMENSIONS,
        reg,
        "mm"
    )
    world_material = _g4.MaterialPredefined("G4_Galactic")
    world_lv = _g4.LogicalVolume(world_solid, world_material, "world_lv", reg)
    reg.setWorld(world_lv.name)
    return world_lv

# ---------- Cylinder ----------
def make_cylinder(reg, zero, twopi, name):
    cyl_solid = _g4.solid.Tubs(
        f"{name}_solid",
        zero,
        CYLINDER_RADIUS,
        CYLINDER_HALF_THICKNESS,
        0,
        twopi,
        reg,
        "mm",
        "rad"
    )
    cyl_material = _g4.MaterialPredefined(CYLINDER_MATERIAL)
    cyl_lv = _g4.LogicalVolume(cyl_solid, cyl_material, f"{name}_lv", reg)
    return cyl_lv

def place_cylinder(world_lv, cyl_lv, cyl_pos, name):
    _g4.PhysicalVolume(
        [0.0, 0.0, 0.0],
        [0.0, 0.0, cyl_pos],
        cyl_lv,
        f"{name}_pv",
        world_lv,
        cyl_lv.registry
    )

def make_pipe(reg, zero, twopi, name):
    pipe_solid = _g4.solid.Tubs(
        f"{name}_solid",
        PIPE_INNER_RADIUS,
        PIPE_OUTER_RADIUS,
        PIPE_HALF_LENGTH,
        0,
        twopi,
        reg,
        "mm",
        "rad"
    )

    pipe_material = _g4.MaterialPredefined(PIPE_MATERIAL)
    pipe_lv = _g4.LogicalVolume(
        pipe_solid,
        pipe_material,
        f"{name}_lv",
        reg
    )
    return pipe_lv

def place_pipe(world_lv, pipe_lv, name):
    _g4.PhysicalVolume(
        [0.0, 0.0, 0.0],
        [0.0, 0.0, PIPE_Z_POSITION],
        pipe_lv,
        f"{name}_pv",
        world_lv,
        pipe_lv.registry
    )


# ---------- Argon inner pipe ----------
def make_argon_pipe(reg, zero, twopi, name):
    argon_solid = _g4.solid.Tubs(
        f"{name}_solid",
        ARGON_INNER_RADIUS,
        ARGON_OUTER_RADIUS,
        ARGON_HALF_LENGTH,
        0,
        twopi,
        reg,
        "mm",
        "rad"
    )
    argon_material = _g4.MaterialPredefined(ARGON_MATERIAL)
    argon_lv = _g4.LogicalVolume(argon_solid, argon_material, f"{name}_lv", reg)
    return argon_lv

def place_argon_pipe(world_lv, argon_lv, name):
    _g4.PhysicalVolume(
        [0.0, 0.0, 0.0],
        [0.0, 0.0, ARGON_Z_POSITION],
        argon_lv,
        f"{name}_pv",
        world_lv,
        argon_lv.registry
    )

# ---------- Lead glass bars ----------
def make_lead_glass_bar(reg, half_cross=BAR_CROSS_HALF, half_length=BAR_LENGTH_HALF, name="lg_bar"):
    bar_solid = _g4.solid.Box(f"{name}_solid", half_cross, half_cross, half_length, reg, "mm")
    tf1 = _g4.MaterialCompound("TF1", 3.86, 2, reg)
    tf1.add_material(_g4.MaterialPredefined("G4_Pb"), 0.51)
    tf1.add_material(_g4.MaterialPredefined("G4_SILICON_DIOXIDE"), 0.49)
    bar_lv = _g4.LogicalVolume(bar_solid, tf1, f"{name}_lv", reg)
    return bar_lv

def place_calorimeter_bars(world_lv, reg, distance=DISTANCE_FROM_PIPE_RADIUS, n_bars=8, z_pos=DISTANCE_FROM_PIPE_Z_BARS):
    bar_lv = make_lead_glass_bar(reg)
    angle_step = 2.0 * _np.pi / n_bars
    for i in range(n_bars):
        angle = i * angle_step
        x = distance * _np.cos(angle)
        y = distance * _np.sin(angle)
        z = z_pos
        rot = [0.0, 0.0, -angle]
        _g4.PhysicalVolume(rot, [x, y, z], bar_lv, f"lg_bar_pv_{i}", world_lv, reg)

def make_lead_cube_dump(reg, half_cross=LEAD_CUBE_DIMENSION, name="lead_cube_dump"):
    cube_solid = _g4.solid.Box(
        f"{name}_solid",
        half_cross,
        half_cross,
        half_cross,
        reg,
        "mm"
    )

    cube_material = _g4.MaterialPredefined("G4_Pb")

    cube_lv = _g4.LogicalVolume(
        cube_solid,
        cube_material,
        f"{name}_lv",
        reg
    )

    return cube_lv

def place_lead_cube_dump(world_lv, cube_lv, z_pos, name="lead_cube_dump"):
    _g4.PhysicalVolume(
        [0.0, 0.0, 0.0],
        [0.0, 0.0, z_pos],
        cube_lv,
        f"{name}_pv",
        world_lv,
        cube_lv.registry
    )

def visualize(reg):
    viewer = _vi.VtkViewer()
    viewer.addAxes(1000)
    viewer.addLogicalVolume(reg.getWorldVolume())
    viewer.view(interactive=True)

# ---------- Main ----------
if __name__ == "__main__":
    # Configuration
    config = GeometryConfig(
        build_world=True,
        build_leading_cylinder=True
    )

    # Registry
    reg, zero, twopi = setup_registry()

    # World
    if config.build_world:
        world_lv = make_world(reg)

    # Cylinders
    if config.build_leading_cylinder:
        lead_cyl_lv = make_cylinder(reg, zero, twopi, "lead_cyl")
        place_cylinder(world_lv, lead_cyl_lv, LEADING_CYLINDER_Z_POSITION, "lead_cyl")

    if config.build_sec_cylinder:
        sec_cyl_lv = make_cylinder(reg, zero, twopi, "sec_cyl")
        place_cylinder(world_lv, sec_cyl_lv, SECOND_CYLINDER_Z_POSITION, "sec_cyl")

    if config.build_pipe:
        pipe_lv = make_pipe(reg, zero, twopi, "window_pipe")
        place_pipe(world_lv, pipe_lv, "window_pipe")

    if config.build_argon_pipe:
        argon_lv = make_argon_pipe(reg, zero, twopi, "argon_pipe")
        place_argon_pipe(world_lv, argon_lv, "argon_pipe")

    if config.build_lead_glass_bars:
        place_calorimeter_bars(world_lv, reg, DISTANCE_FROM_PIPE_RADIUS, N_BARS)

    if config.build_lead_cube_dump:
        lead_cube_lv = make_lead_cube_dump(reg)
        place_lead_cube_dump(world_lv, lead_cube_lv, LEAD_CUBE_Z_POSITION, "lead_cube_dump")

    # Visualization
    visualize(reg)