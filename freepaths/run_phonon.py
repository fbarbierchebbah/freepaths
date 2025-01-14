"""Module that runs one phonon through the structure"""


from freepaths.config import cf
from freepaths.scattering import internal_scattering, surface_scattering, reinitialization
from freepaths.scattering_types import ScatteringTypes


def run_phonon(phonon, flight, scatter_stats, segment_stats, thermal_maps, scatter_maps, material):
    """Run one phonon through the system and record parameters of this run"""

    scattering_types = ScatteringTypes()

    # Run the phonon step-by-step:
    for step_number in range(cf.number_of_timesteps):
        if phonon.is_in_system:

            # Check if different scattering events happened during current time step:
            if cf.include_internal_scattering:
                internal_scattering(phonon, flight, scattering_types)
            reinitialization(phonon, scattering_types)
            surface_scattering(phonon, scattering_types)
            

            # If any scattering has occurred, record it:
            if scattering_types.is_scattered:
                flight.add_point_to_path()
                scatter_stats.save_scattering_events(phonon.y, scattering_types)
                if cf.output_scattering_map:
                    scatter_maps.add_scattering_to_map(phonon, scattering_types)

            # Otherwise, record only if animation is requested:
            else:
                if cf.output_path_animation:
                    flight.add_point_to_path()

            # If diffuse scattering has occurred, reset phonon free path:
            if scattering_types.is_diffuse or scattering_types.is_internal:
                flight.save_free_paths()
                flight.restart()
                phonon.assign_internal_scattering_time(material)
            else:
                flight.add_step(cf.timestep)

            # Record presence of the phonon at this timestep and move on:
            thermal_maps.add_energy_to_maps(phonon, step_number, material)
            segment_stats.record_time_in_segment(phonon.y)
            scattering_types.reset()
            phonon.move()

        # If the phonon reached cold side, record it and break the loop:
        else:
            flight.add_point_to_path()
            flight.save_free_paths()
            flight.finish(step_number, cf.timestep, cf.frequency_detector_size,cf.frequency_detector_center,cf.frequency_detector_size_2,cf.frequency_detector_center_2,cf.frequency_detector_size_3,cf.frequency_detector_center_3)
            break
