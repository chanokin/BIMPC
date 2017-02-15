import numpy as np
import pylab as plt
from pyNN import spiNNaker as sim
import pickle
import os

stats = {'dt': [],
         'nspk': [],
         'tau_e': [],
         'w': []
        }
out_dir = "./burst_behaviour"
for tau_e in range(5, 11):
    for w in range(0, 11):
        sim.setup(timestep=1.)

        burst_params  = {'a': 0.02, 'b': 0.25, 'c': -55.0, 'd': 0.05, 
                         'v_init': -64., 'u_init': -64*0.25, 'tau_syn_E': tau_e}
        class2_params = {'a': 0.2, 'b': 0.26, 'c': -65.0, 'd': 0.0, 
                         'v_init': -64., 'u_init': -64*0.26}
        params = burst_params
        relay = sim.Population(1, sim.IZK_curr_exp, params, label='relay')
        relay.record()
        relay.record_v()

        in_t = 60
        stim = sim.Population(1, sim.SpikeSourceArray, {'spike_times': [in_t]})

        proj = sim.Projection(stim, relay, sim.OneToOneConnector(weights=w),
                              target='excitatory')

        sim.run(100+in_t)

        spikes  = relay.getSpikes(compatible_output=True)
        voltage = relay.get_v(compatible_output=True)

        sim.end()

        volts = [v for (n, t, v) in voltage]
        times = [t for (n, t, v) in voltage]

        dt, nspks = 0, 0
        nid = []
        spk_t = []
        if len(spikes):
            nid[:]   = [n + 5 for (n, t) in spikes]
            spk_t[:] = [t for (n, t) in spikes]
            dt = spk_t[-1] - spk_t[0]
            nspks = len(nid)
        
        stats['tau_e'].append(tau_e)
        stats['w'].append(w)
        stats['dt'].append(dt)
        stats['nspk'].append(nspks)
        
        plt.figure()
        plt.plot(times, volts, 'b')
        plt.plot([times[0], times[-1]], [params['c'], params['c']], 'k--')
        plt.plot(spk_t, nid, '^', markerfacecolor='none', label='output', 
                 markeredgewidth='2', markeredgecolor=(0.6, 0.0, 0.0))
        plt.plot(in_t, params['c'], '^', markerfacecolor='none', label='input', 
                 markeredgewidth='2', markeredgecolor=(0.0, 0.6, 0.0))
        plt.legend()
        plt.ylabel("membrane potential (mv)")
        plt.xlabel("time (ms)")
        plt.title("Burst Izhikevich neuron | tau_E %d | w %d | %d spikes, during %s ms"%\
                  (tau_e, w, nspks, dt))
        plt.draw()
        plt.savefig(os.path.join(out_dir, 
                                 'burst_relay_behaviour_taue_%d_w_%d.png'%\
                                 (tau_e, w)), 
                    dpi=300)
        plt.close()

pickle.dump(stats, open("burst_stats.pickle", "w"))
c = np.array(stats['dt'])
max_dt = c.max()
c /= max_dt
s = 2**np.array(stats['nspk'])
 
plt.figure()
plt.scatter(stats['tau_e'], stats['w'], s=s, c=c, alpha=0.5)
plt.xlabel("tau_syn_e (ms)")
plt.ylabel("synaptic efficacy")
plt.title("size~num spikes   |   color~t(spk0)-t(spkN)")
plt.draw()
plt.savefig(os.path.join(out_dir, 
                         'burst_relay_behaviour_taue_%d_w_%d.png'%(tau_e, w)), 
            dpi=300)

# plt.show()
plt.close()

