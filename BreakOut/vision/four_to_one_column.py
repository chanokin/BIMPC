from sim_tools.common import *
from sim_tools.connectors import kernel_connectors as conn_krn, \
                                 standard_connectors as conn_std

from default_config import defaults_v1 as defaults

column_conn = {'l2': {'inh': 0.2, 'exc': 0.8,
                      'exc2inh': 0.21, 'inh2exc': 0.16,
                      'exc2exc': 0.26, 'inh2inh': 0.25,
                      'exc2l5e': 0.55, 'inh2l5e': 0.20,
                      'exc2l4i': 0.8,
                     },
               'l4': {'inh': 0.2, 'exc': 0.8,
                      'exc2inh': 0.19, 'inh2exc': 0.10,
                      'exc2exc': 0.17, 'inh2inh': 0.50,
                      'exc2l2e': 0.28, 'inh2l2e': 0.50,
                     },
               'l5': {'inh': 0.2, 'exc': 0.8,
                      'exc2inh': 0.10, 'inh2exc': 0.12,
                      'exc2exc': 0.09, 'inh2inh': 0.60,
                      'exc2l2e': 0.03,
                     },
              }
input_conn = {'main':  {'l2e': 0.20,
                        'l4e': 0.80, 'l4i': 0.50,
                        'l5e': 0.10,
                       },
              'extra': {'l2e': 0.20,
                       }
             }
neurons_in_column = {'l2': 10,
                     'l4': 100,
                     'l6': 40}

class V1FourToOneColumn():
    
    def __init__(self, row, col, width, height, lgn, cfg=defaults):
        print("Building Four-to-One column (%d, %d)"%(row, col))
        
        for k in defaults.keys():
            if k not in cfg.keys():
                cfg[k] = defaults[k]

        self.cfg = cfg
        
        self.neuron_count    = cfg['neurons_in_column']
        self.input_conn_prob = cfg['neurons_in_column']
        self.
