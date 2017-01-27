import spynnaker.pyNN as sim
from spynnaker_external_devices_plugin.pyNN.connections.\
    spynnaker_live_spikes_connection import SpynnakerLiveSpikesConnection
import spynnaker_external_devices_plugin.pyNN as ex
import spinn_breakout
from vision.sim_tools.connectors.standard_connectors import breakout_one2one
import pylab as plt
import pickle

RECORD = True
TESTING = True
# TESTING = False
# Game resolution, coords layout in packet
if TESTING:
    X_RESOLUTION = 40
    Y_RESOLUTION = 32
    X_BITS = 6
    Y_BITS = 6
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

# Create breakout population and activate live output for it
breakout_pop = sim.Population(N_NEURON, spinn_breakout.Breakout, {}, label="breakout")



if RECORD:
    # intermediate population to record breakout output (1ms delay)
    exc_cell_params = { 'cm': 0.3,         'i_offset': 0.0,
                        'tau_m': 10.0,     'tau_refrac': 2.0,
                        'tau_syn_E': 2.,   'tau_syn_I': 2.,
                        'v_reset': -70.0,  'v_rest': -65.0,
                        'v_thresh': -55.4
                      }
    inter_pop = sim.Population(X_RESOLUTION*Y_RESOLUTION*2, sim.IF_curr_exp, 
                               exc_cell_params, label='relay')
    inter_pop.record()
     
    o2o_bko = sim.FromListConnector(breakout_one2one(X_RESOLUTION, Y_RESOLUTION,
                                                     X_BITS, weights=2.25) )
    brk2intr = sim.Projection(breakout_pop, inter_pop, o2o_bko)
    
    # simulate key input to bat
    key_stim = [[  2,  33,  44,  65,  86, 107, 128, 149, 160, \
                 362, 383, 404, 425, 446, 467, 488, 509, 520], # move LEFT
                [182, 203, 224, 245, 266, 287, 308, 329, 340, \
                 542, 563, 584, 605, 626, 647, 668, 689, 700]] # move RIGHT
    key_stim = sim.Population(2, sim.SpikeSourceArray, 
                               {'spike_times': key_stim})
    conn_list = [(0, 0, 2., 1.), (1, 1, 2., 1.)]
    sim.Projection(key_stim, breakout_pop, sim.FromListConnector(conn_list))

else:
    # Live output from breakout population
    ex.activate_live_output_for(breakout_pop, host="0.0.0.0", port=UDP_PORT)
    
    # Create spike injector to inject keyboard input into simulation
    key_input = sim.Population(2, ex.SpikeInjector, {"port": 12367}, label="key_input")
    key_input_connection = SpynnakerLiveSpikesConnection(send_labels=["key_input"])

    # Connect key spike injector to breakout population
    conn_list = [(0, 0, 2., 1.), (1, 1, 2., 1.)]
    sim.Projection(key_input, breakout_pop, sim.FromListConnector(conn_list))

    # Create visualiser
    visualiser = spinn_breakout.Visualiser(UDP_PORT, key_input_connection,
                                           x_res=X_RESOLUTION, y_res=Y_RESOLUTION,
                                           x_bits=X_BITS, y_bits=Y_BITS)
                        

if RECORD:
    sim.run(16000) # ms
    spks = inter_pop.getSpikes(compatible_output=True)
    pickle.dump(spks, open('breakout_test_output_spikes.pickle', 'w'))

    fig = plt.figure()
    ax = plt.subplot(1, 1, 1)
    ts = [st for (nid, st) in spks]
    ni = [nid for (nid, st) in spks]
    plt.plot(ts, ni, '.')
    plt.show()
    
else:
    # Run simulation (non-blocking)
    sim.run(None)

    # Show visualiser (blocking)
    visualiser.show()
    
# End simulation
sim.end()



