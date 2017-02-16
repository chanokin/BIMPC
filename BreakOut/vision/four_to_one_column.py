from base_column import *
def debug(txt):
    print("------------------------------------------------------------")
    print(txt)
    print("------------------------------------------------------------")

class V1FourToOneColumn(BaseColumn):
    
    def __init__(self, sim, lgn, width, height, location, learning_on, cfg):
        # print("Building Four-to-One column (%d, %d)"%(row, col))
        BaseColumn.__init__(self, lgn, width, height, location, 
                            learning_on, cfg)
        self.sim = sim
        self.neuron_count     = cfg['neurons_in_column']
        self.input_conn_prob  = cfg['input_conn_prob']
        self.column_conn_prob = cfg['column_conn_prob']
        self.column_conn_wgt  = cfg['column_conn_wgt']
        self.pop_ratio        = cfg['pop_ratio']

        # print("\t\t\tbuilding population sizes...")
        self.build_pop_sizes()
        # print("\t\t\tdone!")
        
        # print("\t\t\tbuilding input indices...")
        self.build_input_indices_weights()
        # print("\t\t\tdone!")
        
        # print("\t\t\tbuilding connectors...")
        self.build_connectors()
        # print("\t\t\tdone!")
        
        # print("\t\t\tbuilding populations...")
        self.build_populations()
        # print("\t\t\tdone!")
        
        # print("\t\t\tbuilding projections...")
        self.build_projections()
        # print("\t\t\tdone!")


    def build_pop_sizes(self):
        sizes = {}
        for lyr in self.column_conn_prob:
            sizes[lyr] = {}
            exc_rat = self.pop_ratio[lyr]['exc']
            sizes[lyr]['exc'] = self.neuron_count[lyr]*exc_rat
            sizes[lyr]['inh'] = self.neuron_count[lyr] - sizes[lyr]['exc']
        self.pop_sizes = sizes


    def decode_conn_key(self, layer, key):
        debug(key)
        key_split = key.split('2')
        src = key_split[0]
        if len(key_split) == 3:
            dst_lyr = 'l2'
            dst = 'exc' if key_split[-1] == 'e' else 'inh'
        else:
            if 'l' in key_split[-1]:
                dst_lyr = key_split[-1][0:2]
                dst = 'exc' if key_split[-1][-1] == 'e' else 'inh'
            else:
                dst_lyr = layer
                dst = key_split[-1]
                
        return src, dst, dst_lyr


    def decode_in_conn_key(self, key):
        dst = 'exc' if key[2] == 'e' else 'inh'
        return key[0:2], dst
        
    def build_intra_conns(self):
        cfg = self.cfg
        prob_conn = conn_std.probability_connector
        inner_conns = {}
        for lyr in self.column_conn_prob:
            inner_conns[lyr] = {}
            for conn in self.column_conn_prob[lyr]:
                if '2' not in conn:
                    continue
                
                src, dst, dst_lyr = self.decode_conn_key(lyr, conn)
                weight = self.column_conn_wgt[lyr][conn]
                prob = self.column_conn_prob[lyr][conn]
                delay = cfg['min_delay']
                conns = prob_conn(self.pop_sizes[lyr][src],
                                  self.pop_sizes[dst_lyr][dst],
                                  prob, weight, delay,
                                  weight_std_dev=1.)

                inner_conns[lyr][conn] = conns
                
        return inner_conns
    
    def build_input_conns(self):
        cfg = self.cfg
        list_prob_conn = conn_std.list_probability_connector
        key_to_pop = {'l4e': self.lgn.css, 'l2e': ['gabor', 'dir'],
                      'l4i': self.lgn.css, }
        input_conns = {}
        dst_indices = []
        for ch in lgn.channels:
            for pop in lgn.output_keys():
                for conn_key in self.input_conn_prob:
                    if pop in key_to_pop[conn_key]:
                        dst_lyr, dst_pop = self.decode_in_conn_key(conn_key)
                        sign = 1 if dst_pop == 'exc' else -1
                        weights = sign*self.in_weights[pop]
                        dst_size = self.pop_sizes[dst_lyr][dst_pop]
                        dst_indices[:] = [i for i in range(dst_size)]
                        prob = self.input_conn_prob['main'][conn_key]
                        conns = list_prob_conn(self.in_indices[pop],
                                               dst_indices, 
                                               weights,
                                               prob)
        
    def build_connectors(self):
        self.intra_conns = self.build_intra_conns()
        
        input_conns = self.build_input_conns()
        # centre-surround to layer 4
        # direction to layer 2
        # gabor to layer 2
    
