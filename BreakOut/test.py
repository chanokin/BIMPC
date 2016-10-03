import spynnaker.pyNN as sim
from spynnaker_external_devices_plugin.pyNN.connections.\
    spynnaker_live_spikes_connection import SpynnakerLiveSpikesConnection
import spynnaker_external_devices_plugin.pyNN as ex
import spinn_breakout

# Spike callback
def receive_spikes(label, t, neuron_ids):
    for n in neuron_ids:
        print "Received spike at time {} from {}{}".format(t, label, n)

# Set up python live spike connection
rx_conn = SpynnakerLiveSpikesConnection(receive_labels=["breakout"])

# Register python receiver with live spike connection
rx_conn.add_receive_callback("breakout", receive_spikes)

# Setup pyNN simulation
sim.setup(timestep=1.0)

# Create breakout population and activate live output for it
breakout_pop = sim.Population(1, spinn_breakout.Breakout, {}, label="breakout")
ex.activate_live_output_for(breakout_pop)

sim.run(1000)