import spynnaker.pyNN as sim
from spynnaker_external_devices_plugin.pyNN.connections.\
    spynnaker_live_spikes_connection import SpynnakerLiveSpikesConnection
import spynnaker_external_devices_plugin.pyNN as ex
import spinn_breakout
import numpy as np
from vision.sim_tools.connectors.direction_connectors import direction_connection, subsample_connection
from vision.sim_tools.connectors.mapping_funcs import row_col_to_input_breakout
import pylab as plt
from vision.spike_tools.vis import plot_output_spikes
 
def init_pop(label, n_neurons, run_time_ms, machine_timestep_ms):
    print "{} has {} neurons".format(label, n_neurons)
    print "Simulation will run for {}ms at {}ms timesteps".format(
        run_time_ms, machine_timestep_ms)
        
def send_input(label, sender):
    sender.send_spike(label, 0)

cell_params_lif = {'cm'        : 0.25,  # nF
                   'i_offset'  : 0.0,
                   'tau_m'     : 20.0,
                   'tau_refrac': 2.0,
                   'tau_syn_E' : 5.0,
                   'tau_syn_I' : 5.0,
                   'v_reset'   : -70.0,
                   'v_rest'    : -65.0,
                   'v_thresh'  : -50.0
                   }

ON_POP_NAME = "subsample channel on"
OFF_POP_NAME = "subsample channel off"
KEY_POP_NAME = "key_input"
 # Game resolution
X_RESOLUTION = 160
Y_RESOLUTION = 128

# Layout of pixels
X_BITS = 8#int(np.ceil(np.log2(X_RESOLUTION)))
Y_BITS =  8#hard coded to match breakout C implementation

subsamp_factor=4
breakout_size=  2**(X_BITS+Y_BITS+1)+2
subsamp_size=(X_RESOLUTION/subsamp_factor)*(Y_RESOLUTION/subsamp_factor)

print "breakout population size: ", breakout_size
print "subsampled (factor of", subsamp_factor,") population size: ", subsamp_size

subX_BITS= int(np.ceil(np.log2(X_RESOLUTION/subsamp_factor)))
subY_BITS=int(np.ceil(np.log2(Y_RESOLUTION/subsamp_factor)))

#pixel speed 
pps=70#
#movement timestep
pt=1./pps 
#number of pixels to calculate speed across
div=2

# UDP ports to read spikes from
# breakout_port = 17893 #
subsamp_port_on = 19993
subsamp_port_off = 19994
subsamp_port_db = 19995

# UDP port to send keyboard events
keyboard_port = 12367 #on spinnaker/spalloc machine

# Setup pyNN simulation
timestep=1.
sim.setup(timestep=timestep)
simulationTime=3000

#setup speed delays
delaysList=range(div-1,-1,-1)
Delays_medium=np.round(np.array(delaysList)*pt*subsamp_factor*1000)#factoring in subsampling
Delays_medium[div-1]=timestep
print "Delays used=",Delays_medium

#restrict number of neurons on each core
#sim.set_number_of_neurons_per_core(sim.IF_curr_exp, 50)

# Create breakout population and activate live output for it
breakout_pop = sim.Population(1, spinn_breakout.Breakout, {}, label="breakout")
# ex.activate_live_output_for(breakout_pop, host="0.0.0.0", port=breakout_port)

#Create subsampled pop

subsamp_on_pop=sim.Population(subsamp_size, sim.IF_curr_exp, cell_params_lif, 
                              label=ON_POP_NAME)
subsamp_off_pop=sim.Population(subsamp_size, sim.IF_curr_exp, cell_params_lif, 
                               label=OFF_POP_NAME)

#activate live outputs
ex.activate_live_output_for(subsamp_on_pop, 
                            # host="0.0.0.0",
                            # database_notify_host="localhost",
                            # database_notify_port_num=subsamp_port_db,
                            port=subsamp_port_on
                            )
ex.activate_live_output_for(subsamp_off_pop, 
                            # host="0.0.0.0",
                            # database_notify_host="localhost",
                            # database_notify_port_num=subsamp_port_db,
                            port=subsamp_port_off
                            )
    
 #Create spike injector to inject keyboard input into simulation
key_input = sim.Population(2, ex.SpikeInjector, {"port": keyboard_port}, 
                           label=KEY_POP_NAME)
                           
#declare projection weights 
#breakout--> subsample
subweight=3.#2.7
#subsample-->direction connections -- needs to take into account div
weight=3.#2.5
key_weight = 5.
print "Weights used=",weight
         
#generate connection lists
subsamp_on_off = subsample_connection(X_RESOLUTION, Y_RESOLUTION, 
                                      subsamp_factor, subweight,
                                      row_col_to_input_breakout)

Connections_subsamp_on, Connections_subsamp_off = subsamp_on_off
                                                
#      
# Connect key spike injector to breakout population
sim.Projection(key_input, breakout_pop, 
               sim.OneToOneConnector(weights=key_weight))

#Connect breakout population to subsample population
projectionSub = sim.Projection(breakout_pop, subsamp_on_pop,
                               sim.FromListConnector(Connections_subsamp_on))
projectionSub = sim.Projection(breakout_pop, subsamp_off_pop,
                               sim.FromListConnector(Connections_subsamp_off))

#Create Live spikes Connections
rec_labels = [ON_POP_NAME, OFF_POP_NAME]
# sub_output_connection=SpynnakerLiveSpikesConnection(receive_labels=rec_labels,
                                                    # local_port=subsamp_port,
                                                    # local_host='0.0.0.0', 
                                                    # )
                                                    
key_input_connection = SpynnakerLiveSpikesConnection(send_labels=[KEY_POP_NAME],
                                                    # local_port=keyboard_port,
                                                    )
# key_input_connection.add_init_callback(KEY_POP_NAME, init_pop)
# key_input_connection.add_start_callback(KEY_POP_NAME, send_input)

#Create visualisers
#visualiser_full = spinn_breakout.Visualiser(
#    breakout_port, key_input_connection,
#    x_res=X_RESOLUTION, y_res=Y_RESOLUTION,
#    x_bits=X_BITS, y_bits=Y_BITS)
#
visualiser_sub = spinn_breakout.Visualiser_subsamp(
                                    key_input_connection, 
                                    # sub_output_connection, 
                                    subsamp_port_on, subsamp_port_off, 
                                    KEY_POP_NAME,
                                    x_res=X_RESOLUTION//subsamp_factor, 
                                    y_res=Y_RESOLUTION//subsamp_factor,
                                    x_bits=subX_BITS, y_bits=subY_BITS)


#subsamp_pop.record('spikes')


# print("# ------------------------------------------------------------------- #")
# print(sub_output_connection._live_event_callbacks)
# print(sub_output_connection._receivers)
# print("# ------------------------------------------------------------------- #")

# Run simulation (non-blocking)
sim.run(None)
#sim.run(simulationTime)
#subsamp_spks=subsamp_pop.getSpikes()


# Show visualiser (blocking)

#visualiser_full.show()
visualiser_sub.show()

# End simulation
sim.end()

#plt.figure()               
#plot_output_spikes(subsamp_spks,plotter=plt)
#plt.xlim([0,simulationTime])
#plt.figure()       
#plot_output_spikes(se_spks,plotter=plt)
#plt.xlim([0,simulationTime])
#plot_output_spikes(right_spks,plotter=plt)
#plt.xlim([0,simulationTime])
#plt.show()
