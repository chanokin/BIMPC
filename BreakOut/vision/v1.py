from sim_tools.common import *
from column import *
from default_config import defaults_v1 as defaults
import sys



class V1():
    
    def __init__(self, sim, lgn, learning_on,
                 cfg=defaults):
        
        for k in defaults.keys():
            if k not in cfg.keys():
                cfg[k] = defaults[k]

        self.sim = sim
        self.cfg = cfg
        self.lgn = lgn
        self.retina = lgn.retina
        self.learn_on = learning_on
        self.width   = lgn.width
        self.height  = lgn.height
        self.complex_recp_width = cfg['complex_recp_width']
        self.unit_type = cfg['unit_type']
        self.column = self.unit_object()
        
        # 3x3 -> [[o o o][o o(r,c) o][o o o]]
        print("Building V1...")
        self.build_units()
        self.connect_units()

    def unit_object(self):
        if self.unit_type == 'autoencoder':
            return V1AutoEncoderColumn
        elif self.unit_type == 'liquid_state':
            return V1MultiColumn
        else:
            return V1FourToOneColumn
        
    def build_units(self):
        cfg = self.cfg
        in_start = cfg['in_receptive_start']
        in_step  = cfg['in_receptive_step']
        cols = []
        total_cols = subsamp_size(in_start, self.width,  in_step)*\
                     subsamp_size(in_start, self.height, in_step)
        num_steps = 60
        cols_to_steps = float(num_steps)/total_cols
        
        print("\t%d Columns..."%(total_cols))
        ### COLUMNS (input interface)  ---------------------------------
        prev_step = 0
        curr_col = 0
        simple = {}
        sys.stdout.write("\t\tSimple layer")
        sys.stdout.flush()

        for r in range(in_start, self.width, in_step):
            simple[r] = {}
            for c in range(in_start, self.height, in_step):
                coords = [r, c]

                mc = self.column(self.sim, self.lgn, 
                                 self.width, self.height, 
                                 coords, self.learn_on, cfg=cfg)
                simple[r][c] = mc
                
                curr_col += 1
                curr_step = int(curr_col*cols_to_steps)
                if curr_step > prev_step:
                    prev_step = curr_step
                    sys.stdout.write(".")
                    sys.stdout.flush()
                
        sys.stdout.write("\n")
        self.simple = simple
        self.num_simple = cfg['num_input_wta']*self.width*self.height

    def build_complex(self):
        pass

    def connect_units(self):
        pass

    def liquid_in_units(self, r, c, keys_r, keys_c):
        return [self.simple[keys_r[in_r]][keys_c[in_c]] \
                            for in_r in range(r-1, r+1) \
                            for in_c in range(c-1, c+1)]
