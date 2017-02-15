import numpy as np
import pylab as plt
import pickle
import os

out_dir = './burst_behaviour'
stats = pickle.load(open("burst_stats.pickle", "r"))
# print(stats)
c = np.array(stats['dt'])
max_dt = c.max()
# c /= max_dt
s = 20*np.array(stats['nspk'])
 
fig = plt.figure()
sc = plt.scatter(stats['tau_e'], stats['w'], s=s, c=c, alpha=0.5, 
                 vmin=0, vmax=max_dt)
plt.xlabel("tau_syn_e (ms)")
plt.ylabel("synaptic efficacy")
plt.title("size~num spikes   |   color~t(spk0)-t(spkN)")
plt.colorbar(sc)
plt.draw()
plt.figtext(0.4, 0.2,'spikes max=%d , min=%d'%(np.max(stats['nspk']), np.min(stats['nspk'])), 
            fontsize=18, ha='center', color='k')

plt.savefig(os.path.join(out_dir, 
                         'all_burst_relay_behaviour.png'), 
            dpi=300)
# plt.show()
plt.close()


