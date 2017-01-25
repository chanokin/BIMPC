import spynnaker.pyNN as sim
from spynnaker_external_devices_plugin.pyNN.connections.\
    spynnaker_live_spikes_connection import SpynnakerLiveSpikesConnection
import spynnaker_external_devices_plugin.pyNN as ex
import spinn_breakout


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

# Run simulation (non-blocking)
sim.run(None)

# Show visualiser (blocking)
visualiser.show()


# End simulation
sim.end()
