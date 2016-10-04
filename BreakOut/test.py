import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import spynnaker.pyNN as sim
from spynnaker_external_devices_plugin.pyNN.connections.\
    spynnaker_live_spikes_connection import SpynnakerLiveSpikesConnection
import spynnaker_external_devices_plugin.pyNN as ex
import spinn_breakout
import socket

# Layout of pixels
X_BITS = 8
Y_BITS = 8
COLOUR_BITS = 1

# UDP port to read spikes from
PORT = 17893

# Build masks
X_MASK = (1 << X_BITS) - 1
X_SHIFT = COLOUR_BITS + Y_BITS

Y_MASK = (1 << Y_BITS) - 1
Y_SHIFT = COLOUR_BITS

COLOUR_MASK = (1 << COLOUR_BITS) - 1

# Open socket to receive datagrams
spike_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
spike_socket.bind(("0.0.0.0", 17893))
spike_socket.setblocking(False)

# Create image plot of retina output
fig = plt.figure()
image_data = np.zeros((128, 160))
image = plt.imshow(image_data,
                   interpolation="nearest", cmap="jet",
                   vmin=0.0, vmax=1.0)

def updatefig(frame):
    global image_data, image, spike_socket

    # Read all datagrams received during last frame
    while True:
        try:
            raw_data = spike_socket.recv(512)
        except socket.error:
            # If error isn't just a non-blocking read fail, print it
            # if e != "[Errno 11] Resource temporarily unavailable":
            #    print "Error '%s'" % e
            # Stop reading datagrams
            break
        else:
            # Slice off EIEIO header and convert to numpy array of uint32
            payload = np.fromstring(raw_data[2:], dtype="uint32")

            # Extract coordinates
            x = (payload >> X_SHIFT) & X_MASK
            y = (payload >> Y_SHIFT) & Y_MASK
            c = (payload & COLOUR_MASK)

            # **YUCK** mask valid pixels
            valid = (x < 160) & (y < 128) & (c < 2)

            # Set valid pixels
            image_data[y[valid],x[valid]] = c[valid]

    # Set image data
    image.set_array(image_data)
    return [image]

# Play animation
ani = animation.FuncAnimation(fig, updatefig, interval=20.0,
                              blit=True)

# Setup pyNN simulation
sim.setup(timestep=1.0)

# Create breakout population and activate live output for it
breakout_pop = sim.Population(1, spinn_breakout.Breakout, {}, label="breakout")
ex.activate_live_output_for(breakout_pop, host="0.0.0.0", port=17893)

sim.run(None)

# Show animated plot (blocking)
plt.show()

# End simulation
sim.end()