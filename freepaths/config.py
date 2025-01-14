"""Module that reads the user input file, provides default values, and converts the variables into enums"""

import sys
import argparse

from freepaths.options import Materials, Distributions

# Import a default input file:
from freepaths.default_config import *


# Parse user arguments:
WEBSITE = 'https://anufrievroman.gitbook.io/freepaths'
parser = argparse.ArgumentParser(prog='FreePATHS', description='Monte Carlo simulator',
                                 epilog=f'For more information, visit: {WEBSITE}')
parser.add_argument('input_file', nargs='?', default=None, help='The input file')
parser.add_argument("-s", "--sampling", help="Run in MFP sampling mode", action="store_true")
args = parser.parse_args()


# If a file is provided, overwrite the default values:
if args.input_file:
    exec(open(args.input_file, encoding='utf-8').read(), globals())
else:
    print("You didn't provide any input file, so let's run a demo simulation!\n")


class Config:
    """Class that contains all the settings for the simulation"""

    def __init__(self):
        """Initiate all the parameters from global variables"""

        # General parameters:
        self.output_folder_name = OUTPUT_FOLDER_NAME
        self.number_of_phonons = NUMBER_OF_PHONONS
        self.number_of_timesteps = NUMBER_OF_TIMESTEPS
        self.number_of_nodes = NUMBER_OF_NODES
        self.timestep = TIMESTEP
        self.temp = T
        self.plots_in_terminal = PLOTS_IN_TERMINAL
        self.output_scattering_map = OUTPUT_SCATTERING_MAP
        self.output_raw_thermal_map = OUTPUT_RAW_THERMAL_MAP
        self.output_trajectories_of_first = OUTPUT_TRAJECTORIES_OF_FIRST
        self.output_structure_color = OUTPUT_STRUCTURE_COLOR
        self.number_of_length_segments = NUMBER_OF_LENGTH_SEGMENTS
        self.phonon_source_angle_distribution = PHONON_SOURCE_ANGLE_DISTRIBUTION

        # Animation:
        self.output_path_animation = OUTPUT_PATH_ANIMATION
        self.output_animation_fps = OUTPUT_ANIMATION_FPS

        # Map & profiles parameters:
        self.number_of_pixels_x = NUMBER_OF_PIXELS_X
        self.number_of_pixels_y = NUMBER_OF_PIXELS_Y
        self.number_of_timeframes = NUMBER_OF_TIMEFRAMES

        # Material parameters:
        self.media = MEDIA
        self.specific_heat_capacity = SPECIFIC_HEAT_CAPACITY

        # Internal scattering:
        self.include_internal_scattering = INCLUDE_INTERNAL_SCATTERING
        self.use_gray_approximation_mfp = USE_GRAY_APPROXIMATION_MFP
        self.gray_approximation_mfp = GRAY_APPROXIMATION_MFP

        # System dimensions:
        self.thickness = THICKNESS
        self.width = WIDTH
        self.length = LENGTH
        self.include_right_sidewall = INCLUDE_RIGHT_SIDEWALL
        self.include_left_sidewall = INCLUDE_LEFT_SIDEWALL
        self.include_top_sidewall = INCLUDE_TOP_SIDEWALL
        self.include_bottom_sidewall = INCLUDE_BOTTOM_SIDEWALL

        # Hot side positions:
        self.hot_side_position_top = HOT_SIDE_POSITION_TOP
        self.hot_side_position_bottom = HOT_SIDE_POSITION_BOTTOM
        self.hot_side_position_right = HOT_SIDE_POSITION_RIGHT
        self.hot_side_position_left = HOT_SIDE_POSITION_LEFT

        self.frequency_detector_size = FREQUENCY_DETECTOR_SIZE
        self.frequency_detector_center = FREQUENCY_DETECTOR_CENTER
        self.frequency_detector_size_2 = FREQUENCY_DETECTOR_2_SIZE
        self.frequency_detector_center_2 = FREQUENCY_DETECTOR_2_CENTER 
        self.frequency_detector_size_3 = FREQUENCY_DETECTOR_3_SIZE
        self.frequency_detector_center_3 = FREQUENCY_DETECTOR_3_CENTER
        self.phonon_source_x = PHONON_SOURCE_X
        self.phonon_source_y = PHONON_SOURCE_Y
        self.phonon_source_width_x = PHONON_SOURCE_WIDTH_X
        self.phonon_source_width_y = PHONON_SOURCE_WIDTH_Y

        # Cold side positions:
        self.cold_side_position_top = COLD_SIDE_POSITION_TOP
        self.cold_side_position_bottom = COLD_SIDE_POSITION_BOTTOM
        self.cold_side_position_right = COLD_SIDE_POSITION_RIGHT
        self.cold_side_position_left = COLD_SIDE_POSITION_LEFT

        # Roughness:
        self.side_wall_roughness = SIDE_WALL_ROUGHNESS
        self.hole_roughness = HOLE_ROUGHNESS
        self.pillar_roughness = PILLAR_ROUGHNESS
        self.top_roughness = TOP_ROUGHNESS
        self.bottom_roughness = BOTTOM_ROUGHNESS
        self.pillar_top_roughness = PILLAR_TOP_ROUGHNESS

        # Parabolic boundary:
        self.include_top_parabola = INCLUDE_TOP_PARABOLA
        self.top_parabola_tip = TOP_PARABOLA_TIP
        self.top_parabola_focus = TOP_PARABOLA_FOCUS
        self.include_bottom_parabola = INCLUDE_BOTTOM_PARABOLA
        self.bottom_parabola_tip = BOTTOM_PARABOLA_TIP
        self.bottom_parabola_focus = BOTTOM_PARABOLA_FOCUS

        # Hole array parameters:
        self.include_holes = INCLUDE_HOLES
        self.circular_hole_diameter = CIRCULAR_HOLE_DIAMETER
        self.rectangular_hole_side_x = RECTANGULAR_HOLE_SIDE_X
        self.rectangular_hole_side_y = RECTANGULAR_HOLE_SIDE_Y
        self.period_x = PERIOD_X
        self.period_y = PERIOD_Y
        
        # New parameter:
        self.inner_circular_hole_diameter = INNER_CIRCULAR_HOLE_DIAMETER
        self.alphaARC = ALPHA_ARC
        self.angle0 = ANGLE0 
        
        # New parameters: factor of scaling to the original parameter
        self.scale_angle_v= SCALE_ANGLE_V
        self.scale_angle_h = SCALE_ANGLE_H
        self.scale_angle_h_reverse = SCALE_ANGLE_H_REVERSE
        self.scaling_factor_radius = SCALING_FACTOR_RADIUS 
        self.scaling_factor_inner_radius = SCALING_FACTOR_INNER_RADIUS
        self.scale_angle_m = SCALE_ANGLE
        

        # Lattice of holes:
        self.hole_coordinates = HOLE_COORDINATES
        self.hole_shapes = HOLE_SHAPES

        # Pillar array parameters [m]
        self.include_pillars = INCLUDE_PILLARS
        self.pillar_coordinates = PILLAR_COORDINATES
        self.pillar_height = PILLAR_HEIGHT
        self.pillar_wall_angle = PILLAR_WALL_ANGLE


    def convert_to_enums(self):
        """Convert some user generated parameters into enums"""

        # Distributions:
        valid_distributions =[member.name.lower() for member in Distributions]
        if self.phonon_source_angle_distribution in valid_distributions:
            self.phonon_source_angle_distribution = Distributions[self.phonon_source_angle_distribution.upper()]
        else:
            print("ERROR: Parameter phonon_source_ANGLE_DISTRIBUTION is not set correctly.")
            print("phonon_source_ANGLE_DISTRIBUTION should be one of the following:")
            print(*valid_distributions, sep = ", ")
            sys.exit()

        # Materials:
        valid_materials = [member.name for member in Materials]
        if self.media in valid_materials:
            self.media = Materials[self.media]
        else:
            print(f"ERROR: Material {self.media} is not in the database.")
            print("MEDIA should be one of the following:")
            print(*valid_materials, sep = ", ")
            sys.exit()


    def check_parameter_validity(self):
        """Check if various parameters are valid"""
        if self.number_of_phonons < self.output_trajectories_of_first:
            self.output_trajectories_of_first = self.number_of_phonons
            print("WARNING: Parameter OUTPUT_TRAJECTORIES_OF_FIRST exceeded NUMBER_OF_PHONONS.\n")

        if self.phonon_source_y > self.length:
            self.phonon_source_y = self.length
            print("WARNING: Parameter phonon_source_Y exceeded LENGHT.\n")

        if self.phonon_source_y < 0:
            self.phonon_source_y = 0
            print("WARNING: Parameter PHONON_SOURCE_Y was negative.\n")

        if self.phonon_source_y - self.phonon_source_width_y / 2 < 0:
            self.phonon_source_width_y = self.phonon_source_y * 2
            print("WARNING: Parameter PHONON_SOURCE_WIDTH_Y was too large.\n")

        if self.phonon_source_x > self.width/2:
            self.phonon_source_x = 0
            print("WARNING: Parameter PHONON_SOURCE_X was larger than WIDTH.\n")

        if self.phonon_source_width_x > self.width:
            self.phonon_source_width_x = self.width
            print("WARNING: Parameter PHONON_SOURCE_WIDTH_X exceeds WIDTH.\n")

        if self.output_path_animation and self.number_of_timesteps > 5000:
            print("WARNING: NUMBER_OF_TIMESTEPS is rather large for animation.\n")

        if (self.cold_side_position_top and self.include_top_sidewall or
            self.hot_side_position_top and self.include_top_sidewall or
            self.cold_side_position_top and self.hot_side_position_top):
            print("ERROR: Top side is assigned multiple functions.\n")
            sys.exit()

        if (self.cold_side_position_bottom and self.include_bottom_sidewall or
            self.hot_side_position_bottom and self.include_bottom_sidewall or
            self.cold_side_position_bottom and self.hot_side_position_bottom):
            print("ERROR: Bottom side is assigned multiple functions.\n")
            sys.exit()

        if (self.cold_side_position_right and self.include_right_sidewall or
            self.hot_side_position_right and self.include_right_sidewall or
            self.cold_side_position_right and self.hot_side_position_right):
            print("ERROR: Right side is assigned multiple functions.\n")
            sys.exit()

        if (self.cold_side_position_left and self.include_left_sidewall or
            self.hot_side_position_left and self.include_left_sidewall or
            self.cold_side_position_left and self.hot_side_position_left):
            print("ERROR: Left side is assigned multiple functions.\n")
            sys.exit()


    def check_depricated_parameters(self):
        """Check for depricated parameters and warn about them"""

        if 'COLD_SIDE_POSITION' in globals():
            print("WARNING: parameter COLD_SIDE_POSITION is depricated. ")
            print("Use specific boolean parameters like COLD_SIDE_POSITION_TOP = True.\n")

        if 'HOT_SIDE_POSITION' in globals():
            print("WARNING: parameter HOT_SIDE_POSITION is depricated. ")
            print("Use specific boolean parameters like HOT_SIDE_POSITION_BOTTOM = True.\n")

        if 'HOT_SIDE_X' in globals():
            print("WARNING: parameter HOT_SIDE_X was renamed to PHONON_SOURCE_X.\n")

        if 'HOT_SIDE_Y' in globals():
            print("WARNING: parameter HOT_SIDE_Y was renamed to PHONON_SOURCE_Y.\n")

        if 'HOT_SIDE_WIDTH_X' in globals():
            print("WARNING: parameter HOT_SIDE_WIDTH_X was renamed to PHONON_SOURCE_WIDTH_X.\n")

        if 'HOT_SIDE_WIDTH_Y' in globals():
            print("WARNING: parameter HOT_SIDE_WIDTH_Y was renamed to PHONON_SOURCE_WIDTH_Y.\n")

        if 'HOT_SIDE_ANGLE_DISTRIBUTION' in globals():
            print("WARNING: parameter HOT_SIDE_ANGLE_DISTRIBUTION was renamed to PHONON_SOURCE_ANGLE_DISTRIBUTION.\n")

cf = Config()
cf.convert_to_enums()
cf.check_parameter_validity()
cf.check_depricated_parameters()
