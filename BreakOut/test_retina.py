import spynnaker.pyNN as sim
from spynnaker_external_devices_plugin.pyNN.connections.\
    spynnaker_live_spikes_connection import SpynnakerLiveSpikesConnection
import spynnaker_external_devices_plugin.pyNN as ex
import spinn_breakout
import pylab as plt

from vision.sim_tools.connectors.standard_connectors import breakout_one2one

from vision.retina import Retina, dvs_modes, MERGED
# from vision.lgn import LGN

burst_params = {'a': 0.02, 'b': 0.25, 'c': -55.0, 'd': 0.05, 
                'v_init': -64., 'u_init': -0.25*64}

TESTING = True
# TESTING = False

# Game resolution, coords layout in packet
if TESTING:
    X_RESOLUTION = 40
    Y_RESOLUTION = 32
    X_BITS = 8
    Y_BITS = 8
    N_NEURON = 2
else:
    X_RESOLUTION = 160
    Y_RESOLUTION = 128
    X_BITS = 8
    Y_BITS = 8
    N_NEURON = 1

# UDP port to read spikes from
UDP_PORT = 19993#17893

# Setup pyNN simulation
sim.setup(timestep=1.0)

#
#
########################################################################
# B R E A K O U T
########################################################################

# Create breakout population and activate live output for it
breakout_pop = sim.Population(N_NEURON, spinn_breakout.Breakout, {}, label="breakout")
ex.activate_live_output_for(breakout_pop, host="0.0.0.0", port=UDP_PORT)

# Create spike injector to inject keyboard input into simulation
key_input = sim.Population(2, ex.SpikeInjector, {"port": 12367}, label="key_input")
key_input_connection = SpynnakerLiveSpikesConnection(send_labels=["key_input"])

# Connect key spike injector to breakout population
sim.Projection(key_input, breakout_pop, sim.OneToOneConnector(weights=2))

# Create visualiser
visualiser = spinn_breakout.Visualiser(
    UDP_PORT, key_input_connection,
    x_res=X_RESOLUTION, y_res=Y_RESOLUTION,
    x_bits=X_BITS, y_bits=Y_BITS)

#
#
########################################################################
# I N T E R M E D I A T E    B U R S T I N G
########################################################################

inter_pop = sim.Population(X_RESOLUTION*Y_RESOLUTION, sim.IZK_curr_exp, 
                           burst_params, label='relay')
inter_pop.record()
 
o2o_bko = sim.FromListConnector( breakout_one2one(X_RESOLUTION, Y_RESOLUTION,
                                                  X_BITS, weights=10.) )
brk2intr = sim.Projection(breakout_pop, inter_pop, o2o_bko)

# ex.activate_live_output_for(inter_pop, host="0.0.0.0", port=UDP_PORT)
#
#
########################################################################
# R E T I N A
########################################################################


# retina = Retina(sim, breakout_pop, X_RESOLUTION, Y_RESOLUTION, 
                # dvs_modes[MERGED])

# Run simulation (non-blocking)
# sim.run(None)
sim.run(17000)

# Show visualiser (blocking)
# visualiser.show()
spks = inter_pop.getSpikes(compatible_output=True)
# print(spks)

# End simulation
sim.end()

fig = plt.figure()
ax = plt.subplot(1, 1, 1)
ts = [st for (nid, st) in spks]
ni = [nid for (nid, st) in spks]
plt.plot(ts, ni, '.')
plt.show()

