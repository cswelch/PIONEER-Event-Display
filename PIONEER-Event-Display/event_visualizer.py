'''
This class provides functionality for viewing characteristics of selected events in the active target (ATAR). The user can pass the .root file and the
indices of an event or a range of events that they want to analyze to the visualize_event() method, which will display a few plots of data that
succinctly summarize the event. Various options can be specified to give more detailed info about the events or display the raw data. If instead one
desires to search for events with certain qualities of interest, the _____ method can be used with various search parameters, subsequently displaying
a selected quantity of events that satisfy the given parameters. 5 different plots are shown for each event: particle x vs. z, particle y vs. z,
particle z vs. t, energy deposition per plane vs. z, and energy deposited in the calorimeter SiPMs by (theta, phi) coordinates.

-->A quick summary of the structure of the simulated ATAR:

The ATAR is comprised of a series of detection planes whose integer indices start at 10,000 by convention in the simulation code. We denote the plane
number, or depth that the particle penetrates into the ATAR, by "z." These planes are comprised of strips that alternate horizontal and vertical
orientation. Thus, the 1st plate measures "x," the 2nd measures "y," the third measures "x," and so on, alternating every plate. We operate under the
assumption that 100 strips comprise each plate in the simulation data supplied.
'''

from logging.config import IDENTIFIER
from typing import ChainMap, overload
import ROOT as r
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import StrMethodFormatter
from Event import Event
import calo_analysis


class Event_Visualizer:
    '''
    The primary method that this class is used for. Uses helper functions below to give a visualization of events satisfying the specified condition(s).
    input_file: The .root file that contains the data of interest. Should have been extracted as a TFile object before passing as a parameter.
    event_index: The index of the event we want to investigate. Should be a positive integer.
    is_event_DAR (optional): Value of 0 = decays in flight, 1 = decays at rest, 2 = all data used. 2 is the default value if nothing is specified.
    display_text_output (optional): Value of True / False, controls whether we do / do not have our event data displayed in text format. Defaults
                                    to False (no text displayed).
    '''
    def visualize_event(self, input_file, event_index, is_event_DAR = 2, display_text_output = False):
        #Get the tree from the input file. This tree is currently in a nested structure. The base of the tree is called "sim," with two branches that
        #are relevant here - calo and atar.  Each of these branches contains the data we are interested in.
        tree = input_file.Get("sim")
        # TODO <<< May implement TChain to get events from all 8 threads / files; currently just using hadd command to combine .root files together
        # after running sim. >>>
        # chain = r.TChain("sim")
        # chain.Add("pienu00000-0*.root")

        #Use max edep per plane as a heuristic to distinguish between DIFs and DARs.
        max_Es = []

        #Keep track of gap times.
        gap_times = []


        # TODO Need to reimplement:
        #   1) Selection of events (using select_events() method)
        #   2) Cuts on variables such as max_E, is_event_DAR
        # TODO <<< Debugging stuff for events being shown 1 at a time. >>>
        i = 0
        #Process each event in the tree and display the results sequentially.
        for entry in tree:
            # TODO <<< Debugging stuff for events being shown 1 at a time. >>>
            print("Event # ", i)
            i += 1

            e = self.process_event(tree, entry)

            if display_text_output:
                self.display_event(e)
        
            self.plot_event(e, 50)

            for gt in e.gap_times:
                gap_times.append(gt)

            max_Es.append(e.max_E)
            
        return (max_Es, gap_times)


    '''
    Returns the time vs. x and time vs. y data from the pixel_hits. The ATAR is made up of sheets that contain alternating horizontal or vertical strips with npixels_per_plane.
    If npixels_per_plane were 100, for instance, 100036 would represent plate 1, 36 / 100 in x, 100161 would represent plate 2, 61 / 100 in y, etc. The output for each of 
    x and y is an n x 2 matrix, where the first column contains the times corresponding to the coordinate values in the second column.
    Also extract the z (plane #) vs. time data. The third element of the tuples contained in this list and the x and y lists will contain corresponding colors to represent
    when particles have decayed.
    '''
    def process_event(self, tree, entry):
        #Arrays to store pixel information to be added.
        pixel_times = []
        pixel_IDs = []
        pixel_edep = []
        pixel_pdgs = []

        #Initialize lists for storing color (for labeling data points according to decay product), t, x, y, z, energy, and energy per plane using the Event class.
        npixels_per_plane = 100
        event = Event()

        #Init time value so 1st loop below works.
        cur_time = 0

        #Loop over the atar branch to get its relevant data.
        for atar in entry.atar:
            pixel_times.append(atar.GetTime())
            pixel_IDs.append(atar.GetPixelID())
            pixel_edep.append(atar.GetEdep())
            pixel_pdgs.append(atar.GetPDGID())

        #Loop over the sipm branch to get the IDs of the SiPMs that were hit.
        for sipm in entry.sipm:
            event.sipm_ids.append(sipm.GetID())
            event.sipm_edeps.append(sipm.GetNHits())

        # TODO <<< Printing temp SiPM ID for debugging; how do we correlate the SiPM IDs to the edep in each event? >>>
        #Loop over the calorimeter entries.
        """ for calo in entry.calo:
            print("Edep Size: ", calo.GetEdepSize())
            for i in range(calo.GetEdepSize()):
                event.sipm_edeps.append(calo.GetEdepAt(i))
                print("Next val: ", calo.GetEdepAt(i))

        entry.info.Print() """
        
        #Extract x vs. t, y vs. t, and z vs. t data. Also add indexed color coding to represent different particles.
        for i in range(len(pixel_IDs)):
            #We can get the plane number using some modular arithmetic on the pixel_hits values. Since these numbers start at 100,000, we must subtract
            #100,000. We also have to subtract 1 to deal with 100 wrapping around to 0 when it shouldn't (i.e., an "off by one" error).
            plane = int(np.floor((pixel_IDs[i] - 1 - 100_000) / npixels_per_plane))

            cur_val = (pixel_IDs[i] - 1) % npixels_per_plane
            last_time = cur_time    #Allows us to note any large time gaps for later analysis.
            cur_time = pixel_times[i]

            event.t_data.append(cur_time)

            #Even planes give us x-values while odd-numbered planes give us y-values. We can use some simple modular arithmetic to distinguish between
            #the two. We must also add NaNs to fill in the gaps in x_data and y_data to make sure the indices of actual data points correspond to the
            #timestamps recorded in t_data.
            if(plane % 2 == 0):
                event.x_data.append(cur_val)
                event.y_data.append(np.nan)
            else:
                event.y_data.append(cur_val)
                event.x_data.append(np.nan)

            event.z_data.append(plane)
            event.E_data.append(pixel_edep[i])

            #Keep track of any gaps in time between decays.
            if cur_time - last_time > 1.0:      #TODO: Adjust this time gap (in ns) as needed.
                event.gap_times.append(cur_time - last_time)

            #Keep track of sum of energies deposited in each plane.
            event.E_per_plane[plane] += pixel_edep[i]

        #Keep track of maximum energy deposited per plane in this event.
        event.max_E = max(event.E_per_plane)

        #Store particle IDs in event class.
        event.pixel_pdgs = pixel_pdgs


        #Extract all (theta, phi) locations of the SiPMs from the GDML file.
        global_crys_dict = calo_analysis.get_crystal_data()
        
        # Use the IDs of the SiPMs hit from the event to get the corresponding values from the dictionary of (ID: (r, theta, phi)) values (global_crys_dict).
        event.r_theta_phis
        for id in event.sipm_ids:
            event.r_theta_phis.append(global_crys_dict.get(id))

        # print("crystal IDs: ", event.sipm_ids)
        # print("edep: ", event.sipm_edeps)
        # print("r_theta_phis: ", event.r_theta_phis)

        return event


    #Show some useful data describing our event in textual form.
    def display_event(self, event):
        print("Length of pixel_pdgs: ", len(event.pixel_pdgs))
        print("Length of x_data: ", len(event.x_data))
        print("Length of y_data: ", len(event.y_data))
        print("Length of z_data: ", len(event.z_data))
        print("Length of t_data: ", len(event.t_data))
        print("Length of E_data: ", len(event.E_data))
        print("Length of E_per_plane: ", len(event.E_per_plane), "\n\n")

        print("pixel_pdgs: ", str(event.pixel_pdgs), "\n")
        print("x_data:", event.x_data, "\n")
        print("y_data:", event.y_data, "\n")
        print("z_data:", event.z_data, "\n")
        print("t_data:", event.t_data, "\n")
        print("E_data:", event.E_data)


    #Plot the following data from our event: x vs. t, y vs. t, z vs. t, E vs. z, and energy deposited in calorimeter by (theta, phi). The graphs 
    #will show the color-coding system used to represent different particles. Display 0 to num_planes on plots including the z variable.
    def plot_event(self, event, num_planes):

        # Create a 2x4 table of plots.
        fig, ((ax1, ax2, ax3, ax4), (ax5, ax6, ax7, ax8)) = plt.subplots(nrows=2, ncols=4, figsize=(30, 15))

        plt.rc('font', size=10) #controls default text size
        plt.rc('axes', titlesize=24) #fontsize of the title
        plt.rc('axes', labelsize=18) #fontsize of the x and y labels
        plt.rc('legend', fontsize=10) #fontsize of the legend

        self.plot_with_color_legend(ax1, event.z_data, event.x_data, event.pixel_pdgs)
        ax1.set_title("x vs. z")
        ax1.set_xlabel("z (plane number)")
        ax1.set_ylabel("x (pixels)")
        ax1.legend()
        ax1.set_xlim(0, num_planes)
        ax1.set_ylim(0, 100)

        self.plot_with_color_legend(ax2, event.z_data, event.y_data, event.pixel_pdgs)
        ax2.set_title("y vs. z")
        ax2.set_xlabel("z (plane number)")
        ax2.set_ylabel("y (pixels)")
        ax2.set_xlim(0, num_planes)
        ax2.set_ylim(0, 100)

        self.plot_with_color_legend(ax3, event.t_data, event.z_data, event.pixel_pdgs)
        ax3.set_title("z vs. t")
        ax3.set_xlabel("t (ns)")
        ax3.set_ylabel("z (plane number)")
        ax3.xaxis.set_major_formatter(StrMethodFormatter('{x:,.1f}'))     #Ensures only 1 decimal place is shown on x-axis, decreasing clutter.
        # ax3.set_xlim(0, 60)
        ax3.set_ylim(0, num_planes)

        ax4.scatter(event.z_data, event.E_data, 10, label = "Energy deposit from event")
        ax4.scatter(range(50), event.E_per_plane, 10, "black", label = "Total energy deposited per plane")
        ax4.set_title("ATAR Energy Deposition Per Plane vs. z")
        ax4.set_xlabel("z (plane number)")
        ax4.set_ylabel("Energy (MeV / plane)")
        ax4.legend()
        #ax4.set_xlim(0, num_planes)

        # Here, we plot the calo analysis data. Create a scatterplot of energy deposited in each SIPM "pixel" in the calorimeter. Also check to see if 
        # only 1 calo entry is present - in this case, the calo ID could be marked as a single volume and we just get 1000, which we don't want to count. 
        # The points are color-coded by energy deposition and surrounded by a black border to make faint colors easier to distinguish from the white 
        # background.
        color_range = event.sipm_edeps
        thetas = [coords[1] for coords in event.r_theta_phis]
        phis = [coords[2] for coords in event.r_theta_phis]

        # TODO <<< For debugging SiPM vs. Edep data shown in color range. >>>
        """ print("Thetas: ", thetas)
        print("Phis: ", phis)
        print("color_range: ", color_range) """

        plot5 = ax5.scatter(thetas, phis, c=color_range, cmap="YlOrRd")
        ax5.set_xlabel("Theta (rad)")
        ax5.set_ylabel("Phi (rad)")
        ax5.set_title("Energy Deposited in Calorimeter SiPMs \n by Theta vs. Phi")
        ax5.set_xlim(0, 3.2)
        ax5.set_ylim(-3.2, 3.2)
        cbar = fig.colorbar(plot5, ax=ax5)
        cbar.set_label('Amount of Energy Deposited (MeV)')

        plt.tight_layout(h_pad=5)
        plt.show()


    #For each color in a list of color labels for different particles, plot the corresponding data.
    def plot_with_color_legend(self, ax, x_coords, y_coords, pixel_pdgs):
        #Store colors and corresponding particle type labels in one place for ease of editing.
        colors = ["r", "b", "g", "y", "m"]
        labels = ["Pion", "Positron", "Electron", "Antimuon", "Muon"]
        particle_IDs = [211, -11, 11, -13, 13]
        
        #Store list of tuples of our data to be processed below.
        coords = list(zip(x_coords, y_coords, pixel_pdgs))

        #Keep track of known particles and other particles to plot.
        cur_data_to_plot = []
        other_to_plot = []
        other_IDs = []
        other_colors = ["k", "gray", "cyan", "indigo", "teal", "lime"]

        #For each color, extract all pdgs of that color and display them on a scatter plot.
        for i in range(0, len(particle_IDs)):
            for coord in coords:
                if coord[2] == particle_IDs[i]:
                    cur_data_to_plot.append(coord)
                elif coord[2] not in particle_IDs:
                    #Keep track of unidentified particles and their IDs so we can plot them separately after exiting this loop.
                    other_to_plot.append(coord)
                    if coord[2] not in other_IDs:
                        other_IDs.append(coord[2])
            
            #Plot data for corresponding color each loop, but only if the data for the corresponding color is not empty.
            if len(cur_data_to_plot) != 0:
                ax.scatter([coord[0] for coord in cur_data_to_plot], [coord[1] for coord in cur_data_to_plot], 10, colors[i], label = labels[i])

            #Reset data to plot every loop.
            cur_data_to_plot = []

        #Plot the unidentified particles in distinct colors with their pdgs for labels.
        for i in range(0, len(other_IDs)):
            ID = other_IDs[i]
            
            #Extract x and y coordinates to plot only if they are all of the particle ID that we are currently plotting.
            # [coord[0] for coord in other_to_plot if coord[2] == ID]
            x = []
            y = []
            for coord in other_to_plot:
                if coord[2] == ID:
                    x.append(coord[0])
                    y.append(coord[1])

            plot = ax.scatter(x, y, 10, other_colors[i], label = str(ID))


    # TODO This method needs to be adapted after first round of changes have been made.
    #Use cuts to select the events we want from the tree. Returns an integer list of the indices of the events that we want from the tree.
    #is_event_DAR: Value of 0 = decays in flight, 1 = decays at rest, 2 = all data used.
    #num_events:  Controls how many events we want to select.
    def select_events(self, tree, is_event_DAR, num_events):
        #Apply logical cut to select whether we want DARs and to exclude empty data. n stores the number of entries that satisfy this cut.
        if is_event_DAR == 0:
            cut = "!pion_dar && Sum$(pixel_edep) > 0"
        elif is_event_DAR == 1:
            cut = "pion_dar && Sum$(pixel_edep) > 0"
        else:
            cut = "Sum$(pixel_edep) > 0"
        n = tree.Draw("Entry$", cut, "goff")
        
        #Get all indices that satisfy the cut.
        events = []
        for i in range(n):
            events.append(tree.GetV1()[i])

        selected_events = events[0:num_events]
        print("Indices of selected events: " + str(selected_events))

        return [int(i) for i in selected_events]


    '''
    Compare the maximum energy deposition of decays in flight and decays at rest. Show mean, median, and standard deviation for both sets of maximum energies, then plot them in
    histogram form. One should notice that the DARs have a higher median energy deposited, though the means may be closer due to large outliers present in some DIF data.
    max_Es_DIF:  Data for maximum energies from decays in flight.
    max_Es_DAR:  Data for maximum energies from decays at rest.
    num_bins:  Controls the number of bins used when plotting data on histograms.
    '''
    def compare_max_edep(self, max_Es_DIF, max_Es_DAR, num_bins):
        max_Es_DIF_mean = np.mean(max_Es_DIF)
        max_Es_DIF_median = np.median(max_Es_DIF)
        max_Es_DIF_std = np.std(max_Es_DIF)

        max_Es_DAR_mean = np.mean(max_Es_DAR)
        max_Es_DAR_median = np.median(max_Es_DAR)
        max_Es_DAR_std = np.std(max_Es_DAR)

        print("\nmax_Es_DIF_mean: " + str(max_Es_DIF_mean))
        print("max_Es_DIF_median: " + str(max_Es_DIF_median))
        print("max_Es_DIF_std: " + str(max_Es_DIF_std))

        print("\nmax_Es_DAR_mean: " + str(max_Es_DAR_mean))
        print("max_Es_DAR_median: " + str(max_Es_DAR_median))
        print("max_Es_DAR_std: " + str(max_Es_DAR_std))


        plt.figure(figsize = (20, 6))

        #Plot histograms. Saving bins parameter from first plot ensures that both histograms have the same number of bins.
        _, bins, _ = plt.hist(max_Es_DIF, bins = num_bins, color = "blue", alpha = 0.5, label = "DIF")
        plt.hist(max_Es_DAR, bins = bins, color = "orange", alpha = 0.5, label = "DAR")
        plt.title("Max Energy by Group for Decays in Flight and Decays at Rest")
        plt.xlabel("Max Energy by Group (MeV)")
        plt.ylabel("Count")
        plt.legend()
        plt.show()


    '''
    Plots gap times given and visualizes how these correlate with DIFs / DARs.
    gap_times: A list of times in ns.
    gap_times_DIF:  Data for times between decays for DIFs in ns.
    gap_times_DAR:  Data for times between decays for DARs in ns.
    num_bins:  Controls the number of bins used when plotting data on histograms.
    '''
    def compare_gap_times(self, gap_times_DIF, gap_times_DAR, num_bins):
        gap_times_DIF_mean = np.mean(gap_times_DIF)
        gap_times_DIF_median = np.median(gap_times_DIF)
        gap_times_DIF_std = np.std(gap_times_DIF)

        gap_times_DAR_mean = np.mean(gap_times_DAR)
        gap_times_DAR_median = np.median(gap_times_DAR)
        gap_times_DAR_std = np.std(gap_times_DAR)

        print("\ngap_times_DIF_mean: " + str(gap_times_DIF_mean))
        print("gap_times_DIF_median: " + str(gap_times_DIF_median))
        print("gap_times_DIF_std: " + str(gap_times_DIF_std))

        print("\ngap_times_DAR_mean: " + str(gap_times_DAR_mean))
        print("gap_times_DAR_median: " + str(gap_times_DAR_median))
        print("gap_times_DAR_std: " + str(gap_times_DAR_std))


        plt.figure(figsize = (20, 6))

        #Plot histograms. Saving bins parameter from first plot ensures that both histograms have the same number of bins.
        _, bins, _ = plt.hist(gap_times_DIF, bins = num_bins, color = "green", alpha = 0.5, label = "DIF")
        plt.hist(gap_times_DAR, bins = bins, color = "brown", alpha = 0.5, label = "DAR")
        plt.title("Gap Times for Decays in Flight and Decays at Rest")
        plt.xlabel("Time (ns)")
        plt.ylabel("Count")
        plt.legend()
        plt.show()