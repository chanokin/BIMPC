//
//  bkout.c
//  BreakOut
//
//  Created by Steve Furber on 26/08/2016.
//  Copyright © 2016 Steve Furber. All rights reserved.
//
// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Spin 1 API includes
#include <spin1_api.h>

// Common includes
#include <debug.h>

// Front end common includes
#include <data_specification.h>
#include <simulation.h>

//----------------------------------------------------------------------------
// Macros
//----------------------------------------------------------------------------
// **TODO** many of these magic numbers should be passed from Python
#define GAME_WIDTH  160                         // Game dimension constants
#define GAME_HEIGHT 128

#define OUT_OF_PLAY 100                         // Ball outof play time (frames)
#define FRAME_DELAY 20                          // Frame delay (ms)

#define FACT 16                                 // ball position and velocity scale factor

//----------------------------------------------------------------------------
// Enumerations
//----------------------------------------------------------------------------
typedef enum
{
  REGION_SYSTEM,
  REGION_BREAKOUT,
  REGION_PROVENANCE,
} region_t;

typedef enum
{
  COLOUR_BACKGROUND = 0x1,
  COLOUR_BAT        = 0xE,
  COLOUR_BALL       = 0xF,
  COLOUR_SCORE      = 0x6,
} colour_t;

//----------------------------------------------------------------------------
// Globals
//----------------------------------------------------------------------------
static int x = (GAME_WIDTH/4)*FACT;                    // initial ball coordinates in fixed-point
static int y = (GAME_HEIGHT/2)*FACT;

static int u = 1*FACT;                                 // initial ball velocity in fixed-point
static int v = -1*FACT;

static int x_bat   = 0;                                // bat LHS x position
static int bat_len = 8;                                // bat length in pixels

static int frame_buff[GAME_WIDTH/8][GAME_HEIGHT];      // frame buffer: 160 x 128 x 4 bits: [hard/soft, R, G, B]

static int out_of_play      = 0;                       // control pause when ball out of play
static int score            = 0;                       // game score

static int keystate         = 2;                       // state of left/right keys

static const uint16_t digit[10] = {0x7B6F,0x1249,0x73E7,0x73CF,0x4979,0x79CF,0x79EF,0x7249,0x7BEF,0x7BCF};     // digits 0-9 in 3 x 5 format for score

//! The upper bits of the key value that model should transmit with
static uint32_t key;

//! Should simulation run for ever? 0 if not
static uint32_t infinite_run;

//! the number of timer ticks that this model should run for before exiting.
static uint32_t simulation_ticks = 0;

//! How many ticks until next frame
static uint32_t tick_in_frame = 0;

//----------------------------------------------------------------------------
// Inline functions
//----------------------------------------------------------------------------
static inline void add_event (int i, int j, colour_t col)
{
    const uint32_t colour_bit = (col == COLOUR_BACKGROUND) ? 0 : 1;
    const uint32_t spike_key = key | (i << 9) | (j << 1) | colour_bit;

    spin1_send_mc_packet(spike_key, 0, NO_PAYLOAD);
    log_debug("%d, %d, %u, %08x\n", i, j, col, spike_key);
}

// gets pixel colour from within word
static inline colour_t get_pixel_col (int i, int j)
{
    return (colour_t)(frame_buff[i/8][j] >> ((i%8)*4) & 0xF);
}

// inserts pixel colour within word
static inline void set_pixel_col (int i, int j, colour_t col)
{
    if (col != get_pixel_col(i, j))
    {
        frame_buff[i/8][j] = (frame_buff[i/8][j] & ~(0xF << ((i%8)*4))) | ((int)col << ((i%8)*4));
        add_event (i, j, col);
    }
}

//----------------------------------------------------------------------------
// Static functions
//----------------------------------------------------------------------------
// initialise frame buffer to blue
static void init_frame ()
{
    for (int i=0; i<(GAME_WIDTH/8); i++)
    {
        for (int j=0; j<GAME_HEIGHT; j++)
        {
            frame_buff[i][j] = 0x11111111 * COLOUR_BACKGROUND;
        }
    }
}

static void update_frame ()
{
// draw bat
    int old_xbat = x_bat;
    if (keystate & 1) if (--x_bat < 0) x_bat = 0;                                                       // move bat
    if (keystate & 2) if (++x_bat > GAME_WIDTH-bat_len) x_bat = GAME_WIDTH-bat_len;
    if (old_xbat != x_bat) {
        for (int i=x_bat; i<(x_bat+bat_len); i++) set_pixel_col(i, GAME_HEIGHT-1, COLOUR_BAT);             // draw yellow bat
        if (x_bat > old_xbat)                     set_pixel_col(old_xbat, GAME_HEIGHT-1, COLOUR_BACKGROUND);
        else if (x_bat < old_xbat)                set_pixel_col(old_xbat+bat_len, GAME_HEIGHT-1, COLOUR_BACKGROUND);
    }

// draw 3-digit score
    int s = score;
    for (int k=0; k<3; k++) {
        int s_x = GAME_WIDTH/2 + 3 - 4*k;
        for (int i=0; i<3; i++) {
            for (int j=0; j<5; j++) {
                if (digit[s%10] & (1<<(14-(i+3*j)))) set_pixel_col(s_x + i, 5 + j, COLOUR_SCORE);
                else                                 set_pixel_col(s_x + i, 5 + j, COLOUR_BACKGROUND);
            }
        }
        s = s/10;
    }

// draw ball
    if (out_of_play == 0) {
        set_pixel_col(x/FACT, y/FACT, COLOUR_BACKGROUND);                                                      // clear pixel to background
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
            set_pixel_col(x/FACT, y/FACT, COLOUR_BALL);                                                    // draw ball
        }
    } else --out_of_play;
}

static bool initialize(uint32_t *timer_period)
{
    log_info("Initialise: started");

    // Get the address this core's DTCM data starts at from SRAM
    address_t address = data_specification_get_data_address();

    // Read the header
    if (!data_specification_read_header(address)) {
        return false;
    }

    // Get the timing details and set up the simulation interface
    if (!simulation_initialise(
            data_specification_get_region(REGION_SYSTEM, address),
            APPLICATION_NAME_HASH, timer_period, &simulation_ticks,
            &infinite_run, 1, NULL,
            data_specification_get_region(REGION_PROVENANCE, address))) {
        return false;
    }

    // Read breakout region
    address_t breakout_region = data_specification_get_region(REGION_BREAKOUT,
                                                              address);
    key = breakout_region[0];
    log_info("\tKey=%08x", key);

    log_info("Initialise: completed successfully");

    return true;
}

//----------------------------------------------------------------------------
// Callbacks
//----------------------------------------------------------------------------
/*void process_sdp (uint m, uint port)   {                                                                // incoming SDP message
    sdp_msg_t *msg = (sdp_msg_t *) m;

    io_printf (IO_BUF, "SDP len %d, port %d - %s\n", msg->length, port, msg->data);

    if (port == 1) spin1_memcpy(&keystate, msg->data, 4);                                               // Port 1 - key data
    spin1_msg_free (msg);
    if (port == 7) spin1_exit (0);
}*/

void timer_callback(uint ticks, uint dummy)
{
    // If a fixed number of simulation ticks are specified and these have passed
    // **NOTE** ticks starts at 1!
    if (infinite_run != TRUE && (ticks - 1) >= simulation_ticks)
    {
        return;
    }
    // Otherwise
    else
    {
      // Increment ticks in frame counter and if this has reached frame delay
      tick_in_frame++;
      if(tick_in_frame == FRAME_DELAY)
      {
        // If this is the first update, draw bat as
        // collision detection relies on this
        if(ticks == FRAME_DELAY)
        {
            for (int i=x_bat; i<(x_bat+bat_len); i++)
            {
                set_pixel_col(i, GAME_HEIGHT-1, COLOUR_BAT);
            }
        }

        // Reset ticks in frame and update frame
        tick_in_frame = 0;
        update_frame();
      }
    }
}

//----------------------------------------------------------------------------
// Entry point
//----------------------------------------------------------------------------
void c_main(void)
{
    // Load DTCM data
    uint32_t timer_period;
    if (!initialize(&timer_period))
    {
        log_error("Error in initialisation - exiting!");
        rt_error(RTE_SWERR);
    }

    init_frame();
    keystate = 0;
    tick_in_frame = 0;

    // Set timer tick (in microseconds)
    spin1_set_timer_tick(timer_period);

    // Register callback
    spin1_callback_on(TIMER_TICK, timer_callback, 2);

    simulation_run();
}