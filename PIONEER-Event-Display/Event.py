'''This class stores the following event data for ease of use:
t - time data.
x - x-coordinate data.
y - y-coordinate data.
z - z-coordinate data; i.e., the number of planes deep into the ATAR
E - energy deposited at the given read time
E_per_plane - energy deposited per plane. Should be of length 50 since there are 50 planes.
pixel_pdgs - particle IDs (as ints) to distinguish different decay products.
max_E - maximum energy deposited over all planes.
gap_times - any large time gaps in the data, which signal a decay at rest.
thetas - from calorimeter, represents theta values at which energy is deposited.
phis - from calorimeter, represents phi values at which energy is deposited.
crystal ids - a list of 6-digit numbers, the means by which we identify in which crystals energy is deposited.
calo_edep - energy deposited at each Calo ID location.
r_theta_phis - coordinate pairs (theta, phi) that we will plot later.
'''

import numpy as np

class Event:

    def __init__(self):
        self.t_data = []
        self.x_data = []
        self.y_data = []
        self.z_data = []
        self.E_data = []
        self.E_per_plane = np.zeros(50)
        self.pixel_pdgs = []
        self.max_E = []
        self.gap_times = []
        self.thetas = []
        self.phis = []
        self.sipm_ids = []
        self.sipm_edeps = []
        self.r_theta_phis = []