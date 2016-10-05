import matplotlib.colors as col
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import spynnaker.pyNN as sim
from spynnaker_external_devices_plugin.pyNN.connections.\
    spynnaker_live_spikes_connection import SpynnakerLiveSpikesConnection
import spynnaker_external_devices_plugin.pyNN as ex
import spinn_breakout
import socket
import enum

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

class State(enum.IntEnum):
    idle = -1
    right = 0
    left = 1

class SpecialEvent(enum.IntEnum):
    score_up = 0
    score_down = 1
    max = 2

state = State.idle

# Open socket to receive datagrams
spike_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
spike_socket.bind(("0.0.0.0", 17893))
spike_socket.setblocking(False)

# Make awesome CRT palette
cmap = col.ListedColormap(["black", "green"])

# Create image plot to display game screen
fig, axis = plt.subplots()
image_data = np.zeros((128, 160))
image = axis.imshow(image_data, interpolation="nearest", cmap=cmap,
                    vmin=0.0, vmax=1.0)

# Draw score using textbox
score_text = axis.text(0.5, 1.0, "0", color="green", transform=axis.transAxes,
                       horizontalalignment="right", verticalalignment="top")
score = 0

def update_fig(frame):
    global image_data, image, spike_socket, key_input_connection, state, score, score_text

    # If state isn't idle, send spike to key input
    if state != State.idle:
        key_input_connection.send_spike("key_input", state)

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
            payload = np.fromstring(raw_data[6:], dtype="uint32")

            # Create mask to select vision (rather than special event) packets
            vision_event_mask = payload >= SpecialEvent.max

            # Extract coordinates
            vision_payload = payload[vision_event_mask] - SpecialEvent.max
            x = (vision_payload >> X_SHIFT) & X_MASK
            y = (vision_payload >> Y_SHIFT) & Y_MASK
            c = (vision_payload & COLOUR_MASK)

            # Set valid pixels
            try:
                image_data[y, x] = c
            except IndexError as e:
                print "Packet contains invalid pixels:", vision_payload, x, y, c

            # Create masks to select score events and count them
            num_score_up_events = np.sum(payload == SpecialEvent.score_up)
            num_score_down_events = np.sum(payload == SpecialEvent.score_down)

            # If any score events occurred
            if num_score_up_events > 0 or num_score_down_events > 0:
                # Apply to score count
                score += num_score_up_events
                score -= num_score_down_events

                # Update displayed score count
                score_text.set_text("%u" % score)

    # Set image data
    image.set_array(image_data)

    # Return list of artists which we have updated
    # **YUCK** order of these dictates sort order
    # **YUCK** score_text must be returned whether it has
    # been updated or not to prevent overdraw
    return [image, score_text]


# Play animation
ani = animation.FuncAnimation(fig, update_fig, interval=20.0,
                              blit=True)

# Setup pyNN simulation
sim.setup(timestep=1.0)

# Create breakout population and activate live output for it
breakout_pop = sim.Population(1, spinn_breakout.Breakout, {}, label="breakout")
ex.activate_live_output_for(breakout_pop, host="0.0.0.0", port=17893)

# Create spike injector to inject keyboard input into simulation
key_input = sim.Population(2, ex.SpikeInjector, {"port": 12367}, label="key_input")
key_input_connection = SpynnakerLiveSpikesConnection(send_labels=["key_input"])

# Connect key spike injector to breakout population
sim.Projection(key_input, breakout_pop, sim.OneToOneConnector(weights=2))

def on_key_press(event):
    global state

    # Send appropriate bits
    if event.key == "left":
        state = State.left
    elif event.key == "right":
        state = State.right

def on_key_release(event):
    global state

    # If either key is released set state to idle
    if event.key == "left" or event.key == "right":
        state = State.idle

# Hook key listeners
fig.canvas.mpl_connect("key_press_event", on_key_press)
fig.canvas.mpl_connect("key_release_event", on_key_release)

# Run simulation (non-blocking)
sim.run(None)

# Show animated plot (blocking)
plt.show()

# End simulation
sim.end()