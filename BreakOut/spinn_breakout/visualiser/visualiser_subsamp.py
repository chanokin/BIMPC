import socket
import enum
import numpy as np

import matplotlib.animation as animation
import matplotlib.colors as col
import matplotlib.pyplot as plt

BRIGHT_GREEN = (0.0, 0.9, 0.0)

# ----------------------------------------------------------------------------
# InputState
# ----------------------------------------------------------------------------
# Input states
class InputState(enum.IntEnum):
    idle = -1
    right = 0
    left = 1


# ----------------------------------------------------------------------------
# Visualiser
# ----------------------------------------------------------------------------
class Visualiser_subsamp(object):
    # How many bits are used to represent colour
    colour_bits = 0

    def __init__(self, key_input_connection,
                 # spike_output_connection,
                 on_pop_port, off_pop_port, key_pop_name,
                 x_res=160, y_res=128, x_bits=8, y_bits=8):
        print("---------------------------------------------------------")
        print("---------------------------------------------------------")
        print("---------------------- VISUALISER -----------------------")
        print("---------------------------------------------------------")
        print("---------------------------------------------------------")
        # Reset input state
        self.input_state = InputState.idle

        # Cache reference to key input connection
        self.key_input_connection = key_input_connection
        # self.spike_output_connection=spike_output_connection
        
        #max neuron ID
        self.maxNeuronID = x_res*y_res

        #Build conversion vals
        self.x_res=x_res
        self.y_res=y_res
        
        self.key_pop_name = key_pop_name
        # print("#setup output spikes connection callbacks")
        # self.on_pop_name = on_pop_name
        # self.spike_output_connection.add_receive_callback(on_pop_name, 
                                                          # self.receive_spikes)

        # self.off_pop_name = off_pop_name
        # self.spike_output_connection.add_receive_callback(off_pop_name, 
                                                          # self.receive_spikes)

        #setup neuron_ids list
        self.neuron_ids_on=[]
        self.neuron_ids_off=[]

        # Make awesome CRT palette
        cmap = col.ListedColormap(["black", BRIGHT_GREEN])

        # Create image plot to display game screen
        self.fig, self.axis = plt.subplots()
        self.image_data = np.zeros((y_res, x_res,3), dtype=np.uint8)
        self.image = self.axis.imshow(self.image_data, interpolation="nearest",
                                      #cmap=cmap, 
                                      vmin=0.0, vmax=100.0)
        # Hook key listeners
        self.fig.canvas.mpl_connect("key_press_event", self._on_key_press)
        self.fig.canvas.mpl_connect("key_release_event", self._on_key_release)
        # Hide grid
        self.axis.grid(False)
        self.axis.set_xticklabels([])
        self.axis.set_yticklabels([])
        self.axis.axes.get_xaxis().set_visible(False)
        
        #Sockets to read signals from Spinnaker over UDP
        self.socket_on = socket.socket(socket.AF_INET, # Internet
                                       socket.SOCK_DGRAM) # UDP
        self.socket_on.bind(("0.0.0.0", on_pop_port))
        self.socket_on.setblocking(False)
        
        self.socket_off = socket.socket(socket.AF_INET, # Internet
                                        socket.SOCK_DGRAM) # UDP
        self.socket_off.bind(("0.0.0.0", off_pop_port))
        self.socket_off.setblocking(False)

    # ------------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------------
    def show(self):
        # Play animation
        self.animation = animation.FuncAnimation(self.fig, self._update,
                                                 interval=20.0, blit=False)#interval=20.0
        # Show animated plot (blocking)
        plt.show()      
        # Show animated plot (non-blocking)
#        plt.ion()
#        plt.show()
#        plt.pause(0.001)
        
    #spike receiver callback
    def receive_spikes(self, label, time, neuron_ids):
        #add received spike IDs to list
        
        if label==self.on_pop_name:
            for id in neuron_ids:
                self.neuron_ids_on.append(np.uint32(id))

        elif label==self.off_pop_name:
            for id in neuron_ids:
                self.neuron_ids_off.append(np.uint32(id))
              
   # ------------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------------
    def _update(self, frame):
        self.image_data[:] = np.uint8(self.image_data*0.7)
        x_res = self.x_res
        y_res = self.y_res
        # If state isn't idle, send spike to key input
        if self.input_state != InputState.idle:
            self.key_input_connection.send_spike(self.key_pop_name, 
                                                 self.input_state)
        
        while True:
            try:
                raw_data = self.socket_on.recv(512)
            except socket.error:
                # If error isn't just a non-blocking read fail, print it
                # if e != "[Errno 11] Resource temporarily unavailable":
                #    print "Error '%s'" % e
                # Stop reading datagrams
                break
            else:
                payload = np.fromstring(raw_data[6:], dtype="uint32")
                y = payload//x_res
                x = payload%x_res
                xc = np.where(np.logical_and(0 <= x, x < x_res))
                yc = np.where(np.logical_and(0 <= y, y < y_res))
                
                try:
                    self.image_data[y[yc], x[xc], 1] = 100
                except:
                    pass
            
        while True:
            try:
                raw_data = self.socket_off.recv(512)
            except socket.error:
                # If error isn't just a non-blocking read fail, print it
                # if e != "[Errno 11] Resource temporarily unavailable":
                #    print "Error '%s'" % e
                # Stop reading datagrams
                break
            else:
                payload = np.fromstring(raw_data[6:], dtype="uint32")
                y = payload//x_res
                x = payload%x_res
                xc = np.where(np.logical_and(0 <= x, x < x_res))
                yc = np.where(np.logical_and(0 <= y, y < y_res))
                
                try:
                    self.image_data[y[yc], x[xc], 0] = 100
                except:
                    pass

        # Set image data
        self.image.set_array(self.image_data)

        # Return list of artists which we have updated
        # **YUCK** order of these dictates sort order
        # **YUCK** score_text must be returned whether it has
        # been updated or not to prevent overdraw
        return [self.image]

    def _on_key_press(self, event):
        # Send appropriate bits
        if event.key == "left":
            self.input_state = InputState.left
        elif event.key == "right":
            self.input_state = InputState.right

    def _on_key_release(self, event):
        # If either key is released set state to idle
        if event.key == "left" or event.key == "right":
            self.input_state = InputState.idle
