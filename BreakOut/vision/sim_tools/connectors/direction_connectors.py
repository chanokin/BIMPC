import numpy as np
import sys

def unique_rows(a):
    print(len(a), len(a[0]))
    a = np.ascontiguousarray(a)
    print(a.shape, a.dtype)
    unique_a = np.unique(a.view([('', a.dtype)]*a.shape[1]))
    shape = (unique_a.shape[0], a.shape[1])
    return unique_a.view(a.dtype).reshape(shape)


def direction_connection_angle(direction, max_angle, max_dist, 
                               width, height, mapfunc,
                               exc_delay, inh_delay,
                               dfunc=lambda x: x, weight=2.):
    # print("direction_connection_angle")
    dcah = direction_connection_angle_helper
    exc_conns_on  = []
    inh_conns_on  = []
    exc_conns_off = []
    inh_conns_off = []
    exc = []
    inh = []
    # sys.stdout.write("\t\tPercent %03d"%0)
    on_chan = True
    for y in range(height):
        # sys.stdout.write( "\r\t\tPercent %03d"%( (r*100.)/height ) ) 
        # sys.stdout.flush() 
        for x in range(width):
            on_chan = True
            exc[:], inh[:] = dcah(direction, max_angle, max_dist, x, y, 
                                  width, height, mapfunc, on_chan, 
                                  exc_delay, inh_delay,
                                  dfunc=dfunc, weight=weight)  
            if exc:
                exc_conns_on += exc
                inh_conns_on += inh
                
            on_chan = False
            exc[:], inh[:] = dcah(direction, max_angle, max_dist, x, y, 
                                  width, height, mapfunc, on_chan,
                                  exc_delay, inh_delay, 
                                  dfunc=dfunc, weight=weight)  
            if exc:
                exc_conns_off += exc
                inh_conns_off += inh
    # print(" - Done!")
    return [[exc_conns_on,  inh_conns_on], \
            [exc_conns_off, inh_conns_off]]


def direction_connection_angle_helper(direction, max_angle, max_dist, 
                                      start_x, start_y, width, height,
                                      mapfunc, is_on_channel,
                                      exc_delay, inh_delay,
                                      dfunc=lambda x: x, weight=2.,
                                      inh_width_mult=6.
                                     ):
    deg2rad = np.pi/180.
    dang = 0
    if   direction == 'right2left':
        dang = 0
    elif direction == 'bl2tr':
        dang = 45
    elif direction == 'bottom2top':
        dang = 90
    elif direction == 'br2tl':
        dang = 135
    elif direction == 'left2right':
        dang = 180
    elif direction == 'tl2br':
        dang = 225
    elif direction == 'top2bottom':
        dang = 270
    elif direction == 'tr2bl':
        dang = 315
    else:
        raise Exception("Not a valid direction - %s -"%(direction))
    
    chan = int(is_on_channel)
    coord = {}
    e = []; i = []
    dst = start_y*width + start_x
    for a in range(-max_angle, max_angle + 1):
        for d in range(1, max_dist+1):
            new_c = True
            delay = dfunc(d)
            xd = int(np.round( d*np.cos((a+dang)*deg2rad) ))
            yd = int(np.round( d*np.sin((a+dang)*deg2rad) ))
            if xd in coord:
                if yd in coord[xd]:
                    new_c = False
                coord[xd][yd] = 0
            else:
                coord[xd] = {yd: 0}

            if new_c:
                xe, ye = start_x + xd, start_y + yd
                src = mapfunc(ye, xe, chan)
                if 0 <= xe < width and 0 <= ye < height:
                    e.append( (src, dst, weight, delay+exc_delay) )
                
                xd = int(np.round( d*np.cos((a+dang+180)*deg2rad) ))
                yd = int(np.round( d*np.sin((a+dang+180)*deg2rad) ))
                xi, yi = start_x + xd, start_y + yd
                src = mapfunc(yi, xi, chan)
                
                if 0 <= xi < width and 0 <= yi < height:
                    i.append( (src, dst, -weight*inh_width_mult, inh_delay) )
            

    # return [unique_rows(e), unique_rows(i)]
    return [e, i]




def direction_connection(direction, x_res, y_res, div, delays, weight,
                          mapfunc):
    
    # subY_BITS=int(np.ceil(np.log2(y_res)))
    connection_list_on  = []
    connection_list_off = []
    connection_list_inh_on = []
    connection_list_inh_off = []
    add_exc = False
    src_on = 0
    src_off = 0
    #direction connections
    for j in range(y_res):
        for i in range(x_res):
            for k in range(div):
                Delay=delays[k]
                dst = j*x_res + i
                if direction=="south east":
                     #south east connections  
                    #check targets are within range
                    if( ((i+k) < x_res) and ((j+k) < y_res) ):
                        add_exc = True
                        src_on  = mapfunc((j+k), i+k, 1)
                        src_off = mapfunc((j+k), i+k, 0)
                
                elif direction=="south west":
                    #south west connections
                    #check targets are within range
                    if((i-k)>=0 and ((j+k)<=(y_res-1))):   
                        add_exc = True
                        src = (j+k)*x_res + i-k
                
                elif direction=="north east":
                    #north east connections
                    #check targets are within range
                    if(((i+k)<=(x_res-1)) and ((j-k)>=0)):  
                        add_exc = True 
                        src_on  = mapfunc((j-k), i+k, 1)
                        src_off = mapfunc((j-k), i+k, 0)
                                        
                elif direction=="north west":
                    #north east connections
                    #check targets are within range
                    if((i-k)>=0 and ((j-k)>=0)):   
                        add_exc = True
                        src_on  = mapfunc((j-k), i-k, 1)
                        src_off = mapfunc((j-k), i-k, 0)
                                        
                elif direction=="north":
                    #north connections
                    #check targets are within range
                    if((j-k)>=0):   
                        add_exc = True
                        src_on  = mapfunc((j-k), i, 1)
                        src_off = mapfunc((j-k), i, 0)
                
                elif direction=="south":
                    #north connections
                    #check targets are within range
                    if((j+k)<=(y_res-1)):   
                        add_exc = True
                        src_on  = mapfunc((j+k), i, 1)
                        src_off = mapfunc((j+k), i, 0)
                        
                elif direction=="east":
                    #north connections
                    #check targets are within range
                    if((i+k)<=(x_res-1)):   
                        add_exc = True
                        src_on  = mapfunc(j, i+k, 1)
                        src_off = mapfunc(j, i+k, 0)
                        
                elif direction=="west":
                    #north connections
                    #check targets are within range
                    if((i-k)>=0):   
                        add_exc = True
                        src_on  = mapfunc(j, i-k, 1)
                        src_off = mapfunc(j, i-k, 0)
                        
                else:
                    raise Exception( "Not a valid direction: %s"%direction )

                #ON channels
                connection_list_on.append((src_on, dst, weight, Delay))
                #OFF channels
                connection_list_off.append((src_off, dst, weight, Delay))
                add_exc = False

    return [connection_list_on, connection_list_inh_on], \
            [connection_list_off, connection_list_inh_off]


def subsample_connection(x_res, y_res, subsamp_factor, weight, 
                         row_col_to_input):
    
    # subY_BITS=int(np.ceil(np.log2(y_res/subsamp_factor)))
    connection_list_on=[]
    connection_list_off=[]
    
    sx_res = int(x_res)//int(subsamp_factor)
    
    for j in range(int(y_res)):
        for i in range(int(x_res)):
            si = i//subsamp_factor
            sj = j//subsamp_factor
            #ON channels
            subsampidx = sj*sx_res + si
            connection_list_on.append((row_col_to_input(j, i,1), 
                                       subsampidx, weight, 1.))
            #OFF channels
            connection_list_off.append((row_col_to_input(j, i,0), 
                                        subsampidx, weight, 1.))    
            
    return connection_list_on, connection_list_off
    

