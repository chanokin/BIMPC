//
//  bkout.c
//  BreakOut
//
//  Created by Steve Furber on 26/08/2016.
//  Copyright © 2016 Steve Furber. All rights reserved.
//

#include <spin1_api.h>
#include <stdint.h>

#define GAME_WIDTH  160                         // Game dimension constants
#define GAME_HEIGHT 128

const int FRAME_DELAY   = 20;                   // Frame delay (ms)
const int OUT_OF_PLAY   = 100;                  // Ball outof play time (frames)

#define FACT 16                                 // ball position and velocity scale factor

int x = (GAME_WIDTH/4)*FACT;                    // initial ball coordinates in fixed-point
int y = (GAME_HEIGHT/2)*FACT;

int u = 1*FACT;                                 // initial ball velocity in fixed-point
int v = -1*FACT;

int x_bat   = 0;                                // bat LHS x position
int bat_len = 8;                                // bat length in pixels

int frame_buff[GAME_WIDTH/8][GAME_HEIGHT];      // frame buffer: 160 x 128 x 4 bits: [hard/soft, R, G, B]

const int background = 0x1;                     // background colour - blue & soft
const int bat_col    = 0xE;                     // bat colour - yellow & hard
const int ball_col   = 0xF;                     // ball colour - white & hard
const int score_col  = 0x6;                     // score colour - yellow & soft

int out_of_play      = 0;                       // control pause when ball out of play
int score            = 0;                       // game score

int keystate         = 2;                       // state of left/right keys
int events[60];                                 // display update events

const uint16_t digit[10] = {0x7B6F,0x1249,0x73E7,0x73CF,0x4979,0x79CF,0x79EF,0x7249,0x7BEF,0x7BCF};     // digits 0-9 in 3 x 5 format for score

void init_frame () {                                                                                    // initialise frame buffer to blue
    for (int i=0; i<(GAME_WIDTH/8); i++) {
        for (int j=0; j<GAME_HEIGHT; j++) {
            frame_buff[i][j] = 0x11111111 * background;
        }
    }
}

void add_event (int i, int j, int col) {
    events[0]++;
    events[events[0]] = (i<<16) + (j<<8) + col;
}

int get_pixel_col (int i, int j) {                                                                      // gets pixel colour from within word
    return (frame_buff[i/8][j] >> ((i%8)*4) & 0xF);
}

void set_pixel_col (int i, int j, int col) {                                                            // inserts pixel colour within word
    if (col != get_pixel_col(i, j)) {
        frame_buff[i/8][j] = (frame_buff[i/8][j] & ~(0xF << ((i%8)*4))) | (col << ((i%8)*4));
        add_event (i, j, col);
    }
}

void update_frame () {

// draw bat
    int old_xbat = x_bat;
    if (keystate & 1) if (--x_bat < 0) x_bat = 0;                                                       // move bat
    if (keystate & 2) if (++x_bat > GAME_WIDTH-bat_len) x_bat = GAME_WIDTH-bat_len;
    if (old_xbat != x_bat) {
        for (int i=x_bat; i<(x_bat+bat_len); i++) set_pixel_col(i, GAME_HEIGHT-1, bat_col);             // draw yellow bat
        if (x_bat > old_xbat)                     set_pixel_col(old_xbat, GAME_HEIGHT-1, background);
        else if (x_bat < old_xbat)                set_pixel_col(old_xbat+bat_len, GAME_HEIGHT-1, background);
    }
    
// draw 3-digit score
    int s = score;
    for (int k=0; k<3; k++) {
        int s_x = GAME_WIDTH/2 + 3 - 4*k;
        for (int i=0; i<3; i++) {
            for (int j=0; j<5; j++) {
                if (digit[s%10] & (1<<(14-(i+3*j)))) set_pixel_col(s_x + i, 5 + j, score_col);
                else                                 set_pixel_col(s_x + i, 5 + j, background);
            }
        }
        s = s/10;
    }
    
// draw ball
    if (out_of_play == 0) {
        set_pixel_col(x/FACT, y/FACT, background);                                                      // clear pixel to background
        x += u;                                                                                         // move ball
        if ((x < -u) || (x >= ((GAME_WIDTH*FACT)-u)))  u = -u;                                          // bounce off sides
        y += v;
        if (y < -v) v = -v;                                                                             // bounce off top
    
//detect collision
        if (get_pixel_col(x/FACT, y/FACT) & 0x8) {                                                      // hit something hard!
            if (x/FACT < (x_bat+bat_len/4))        u = -FACT;
            else if (x/FACT < (x_bat+bat_len/2))   u = -FACT/2;
            else if (x/FACT < (x_bat+3*bat_len/4)) u = FACT/2;
            else                                   u = FACT;
            v = -FACT;
            y -= FACT;
            if (score < 999) ++score;
        }
    
// lost ball
        if (y >= (GAME_HEIGHT*FACT-v)) {
            v = -1*FACT;
            y = (GAME_HEIGHT/2)*FACT;
            out_of_play = OUT_OF_PLAY;
            if (score > 0) --score;
        } else {
            set_pixel_col(x/FACT, y/FACT, ball_col);                                                    // draw ball
        }
    } else --out_of_play;
}

void process_sdp (uint m, uint port)   {                                                                // incoming SDP message
    sdp_msg_t *msg = (sdp_msg_t *) m;
    
    io_printf (IO_BUF, "SDP len %d, port %d - %s\n", msg->length, port, msg->data);
    
    if (port == 1) spin1_memcpy(&keystate, msg->data, 4);                                               // Port 1 - key data
    spin1_msg_free (msg);
    if (port == 7) spin1_exit (0);
}

void send_events() {                                                                                    // send events to host display
    sdp_msg_t *msg = spin1_msg_get();
    if (msg == NULL) rt_error(RTE_MALLOC);
    msg->tag       = 1;                                                                                 // IPTag 1
    msg->dest_port = PORT_ETH;                                                                          // Ethernet
    msg->dest_addr = sv->dbg_addr;                                                                      // Root chip
    msg->flags     = 0x07;                                                                              // Flags = 7
    msg->srce_port = spin1_get_core_id ();                                                              // Source port
    msg->srce_addr = spin1_get_chip_id ();                                                              // Source addr
    int len        = 4*(events[0] + 1);
    msg->length    = sizeof (sdp_hdr_t) + sizeof (cmd_hdr_t) + len;                                     // Length
    spin1_memcpy(msg->data, (void *)events, len);                                                       // Data
        
    (void) spin1_send_sdp_msg (msg, 10);
    
    spin1_msg_free (msg);
}

void tick_callback (uint ticks, uint dummy) {
    events[0] = 0;                                                                                      // events[0] = number of events to process
    update_frame();                                                                                     // next game timestep
    send_events();
}

void c_main(void) {
    uint chip = spin1_get_chip_id ();                                                                   // get chip ID
    uint core = spin1_get_core_id ();                                                                   // ...& core ID
    
    io_printf (IO_BUF, "Started core %d %d %d\n", chip >> 8, chip & 255, core);                         // signal core running

    init_frame();
    keystate = 2;
    
    spin1_set_timer_tick (1000*FRAME_DELAY);                                                            // frame rate timer tick
    spin1_callback_on (TIMER_TICK, tick_callback, 1);                                                   // timer callback
    spin1_callback_on (SDP_PACKET_RX, process_sdp, 2);                                                  // SDP callback
    
    spin1_start (SYNC_NOWAIT);                                                                          // start event-driven operation
    
    io_printf (IO_BUF, "Terminated core %d %d %d\n", chip >> 8, chip & 255, core);                      // print if event_exit used...
}
