"""Module that provides phonon flight characteristics"""

from math import cos , sin
import numpy as np


class Path:
    """Phonon path coordinates"""

    def __init__(self, x_init, y_init, z_init):
        """Initialize a path"""
        self.x = np.array([x_init])
        self.y = np.array([y_init])
        self.z = np.array([z_init])

    def add_point(self, x_new, y_new, z_new):
        """Add a point to the phonon path"""
        self.x = np.append(self.x, x_new)
        self.y = np.append(self.y, y_new)
        self.z = np.append(self.z, z_new)

    @property
    def number_of_path_points(self):
        """Calculate number of points in the path"""
        return len(self.x)


class Flight:
    """Phonon flight characteristics"""

    def __init__(self, phonon):
        """Initialize a phonon flight"""
        self.phonon = phonon
        self.initial_frequency = self.phonon.f
        self.initial_theta = self.phonon.theta
        self.path = Path(self.phonon.x, self.phonon.y, self.phonon.z)
        self.exit_theta = 0.0
        self.detected_frequency = 0.0
        self.detected_frequency_2 = 0.0
        self.detected_frequency_3 = 0.0
        self.free_path = 0.0
        self.free_path_along_x = 0.0
        self.free_path_along_y = 0.0
        self.travel_time = 0.0
        self.time_since_previous_scattering = 0.0
        self.free_paths = []
        self.free_paths_along_x = []
        self.free_paths_along_y = []

    @property
    def mean_free_path(self):
        """Mean value of all free flights"""
        try:
            mfp = sum(self.free_paths)/len(self.free_paths)
        except:
            mfp = 0
        return mfp
    
    @property
    def mean_free_path_x(self):
        """Mean value of all free flights"""
        try:
            mfp = sum(self.free_paths_along_x)/len(self.free_paths_along_x)
        except:
            mfp = 0
        return mfp
    
    @property
    def mean_free_path_y(self):
        """Mean value of all free flights"""
        try:
            mfp = sum(self.free_paths_along_y)/len(self.free_paths_along_y)
        except:
            mfp = 0
        return mfp

    def add_point_to_path(self):
        """Add a scattering point to the path"""
        self.path.add_point(self.phonon.x, self.phonon.y, self.phonon.z)

    def save_free_paths(self):
        """Save current free path to the list of free paths"""
        self.free_paths.append(self.free_path)
        self.free_paths_along_x.append(self.free_path_along_x)
        self.free_paths_along_y.append(self.free_path_along_y)

    def restart(self):
        """Restart the flight after a scattering event"""
        self.time_since_previous_scattering = 0.0
        self.free_path = 0.0
        self.free_path_along_x = 0.0
        self.free_path_along_y = 0.0

    def finish(self, step, timestep, detector_size, detector_center, detector_size_2, detector_center_2, detector_size_3, detector_center_3):
        """Finish the flight and record final state"""
        self.exit_theta = self.phonon.theta
        self.travel_time = step * timestep
        if abs(self.phonon.x- detector_center) < detector_size / 2.0:
            self.detected_frequency = self.phonon.f
        if abs(self.phonon.x- detector_center_2) < detector_size_2 / 2.0:
            self.detected_frequency_2 = self.phonon.f
        if abs(self.phonon.x- detector_center_3) < detector_size_3 / 2.0:
            self.detected_frequency_3 = self.phonon.f

    def add_step(self, timestep):
        """Increase parameters of the flight by length of one step"""
        step_length = self.phonon.speed * timestep
        self.free_path += step_length
        self.free_path_along_x += step_length * abs(cos(self.phonon.phi)) * abs(sin(self.phonon.theta))
        self.free_path_along_y += step_length * abs(cos(self.phonon.phi)) * abs(cos(self.phonon.theta))
        self.time_since_previous_scattering += timestep
