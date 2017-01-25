exc_cell = "IF_curr_exp"
exc_cell_params = { 'cm': 0.3,  # nF
                    'i_offset': 0.0,
                    'tau_m': 10.0,
                    'tau_refrac': 2.0,
                    'tau_syn_E': 2.,
                    'tau_syn_I': 2.,
                    'v_reset': -70.0,
                    'v_rest': -65.0,
                    'v_thresh': -55.4
                  }

inh_cell = "IF_curr_exp"
inh_cell_params = { 'cm': 0.3,  # nF
                    'i_offset': 0.0,
                    'tau_m': 10.0,
                    'tau_refrac': 1.0,
                    'tau_syn_E': 2.,
                    'tau_syn_I': 6.,
                    'v_reset': -70.0,
                    'v_rest': -65.0,
                    'v_thresh': -58.
                  }

w2s = 2.
inh_w2s = 2.
dir_w2s = 1.1 #0.5
ssamp_w2s = 3.

defaults_retina = {'kernel_width': 3,
                   'kernel_exc_delay': 2.,
                   'kernel_inh_delay': 1.,
                   'corr_self_delay': 4.,
                   'row_step': 1, 'col_step': 1,
                   'start_row': 0, 'start_col': 0,
                  #  'gabor': {'num_divs': 4., 'freq': 5., 'std_dev': 5., 'width': 3},
                   'gabor': False,
                   
                   'ctr_srr': {'std_dev': 0.8, 'sd_mult': 6.7, 'width': 3, 
                               'step': 1, 'start':0, 'w2s_mult':1.},
                   'ctr_srr_half': {'std_dev': 1.8664, 'sd_mult': 6.7, 'width': 7,
                                    'step': 3, 'start':0, 'w2s_mult': 4.},
                   'ctr_srr_quarter': {'std_dev': 4., 'sd_mult': 6.7, 
                                       'width': 15,
                                       'step': 6, 'start': 0, 'w2s_mult': 8.},
                    #retina receives 1 spike per change, needs huge weights
                   'w2s': w2s*1.5, 
                   'inhw': inh_w2s,
                   'inh_cell': {'cell': inh_cell,
                               'params': inh_cell_params,
                               }, 
                   'exc_cell': {'cell': exc_cell,
                                'params': exc_cell_params,
                                },
                   'record': {'voltages': False, 
                              'spikes': False,
                             },
                   'direction': {'keys': [
                                          'left2right', 'right2left',
                                          'bottom2top', 'top2bottom',
                                          'bl2tr', 'tl2br', 'br2tl', 'tr2bl',
                                          # 'east', 'south', 'west', 'north',
                                          # 'south east', 'south west', 
                                          # 'north east', 'north west'
                                         ],
                                 'div': 4,#6,
                                 'weight': dir_w2s,
                                 'delays': [1, 4, 6, 8],#, 3, 4 ],
                                 'subsamp': 1,#2,
                                 'w2s': ssamp_w2s,
                                 'angle': 5,
                                 'dist': 4,
                                 'dfunc': lambda x: 33*(x-1) + 1, # 33ms = 1000/framerate
                                 
                                },
                  'row_bits': 8,
                  }


defaults_lgn = {'kernel_width': 3,
                'kernel_exc_delay': 2.,
                'kernel_inh_delay': 1.,
                'row_step': 1, 'col_step': 1,
                'start_row': 0, 'start_col': 0,
                'gabor': {'num_divs': 7., 'freq': 5., 'std_dev': 1.1},
                'ctr_srr': {'std_dev': 0.8, 'sd_mult': 6.7} ,
                'w2s': w2s*1.1,
                'inh_cell': {'cell': inh_cell,
                             'params': inh_cell_params
                            }, 
                'exc_cell': {'cell': exc_cell,
                             'params': exc_cell_params
                            },
                'record': {'voltages': False, 
                           'spikes': False,
                        },
                'lat_inh': False,
            }
