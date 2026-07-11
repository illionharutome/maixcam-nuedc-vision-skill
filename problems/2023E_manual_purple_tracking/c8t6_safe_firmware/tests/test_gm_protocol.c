#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../Core/Inc/gm_protocol.h"

static GmStream s;
static GmCommand c;
static GmParseResult r;

static void feed(const char *text) { while (*text) r = gm_stream_feed(&s, *text++, &c); }

int main(void) {
    /* valid TRACK */
    gm_stream_init(&s); feed("$GM,CMD,-300,220,TRACK#");
    assert(r == GM_PARSE_OK && c.pan == -300 && c.tilt == 220 && !strcmp(c.mode, "TRACK"));

    /* valid STOP */
    gm_stream_init(&s); feed("$GM,CMD,0,0,STOP#");
    assert(r == GM_PARSE_OK && c.pan == 0 && c.tilt == 0 && !strcmp(c.mode, "STOP"));

    /* PAN out of range */
    gm_stream_init(&s); feed("$GM,CMD,-1500,0,TRACK#");
    assert(r == GM_PARSE_PAN_RANGE);

    /* TILT out of range */
    gm_stream_init(&s); feed("$GM,CMD,0,2000,TRACK#");
    assert(r == GM_PARSE_TILT_RANGE);

    /* bad MODE */
    gm_stream_init(&s); feed("$GM,CMD,100,200,FAST#");
    assert(r == GM_PARSE_MODE_INVALID);

    /* missing # */
    gm_stream_init(&s); feed("$GM,CMD,0,0,STOP");
    assert(r == GM_PARSE_SHORT);

    /* bad prefix */
    gm_stream_init(&s); feed("$XX,CMD,0,0,STOP#");
    assert(r == GM_PARSE_PREFIX);

    /* field count wrong */
    gm_stream_init(&s); feed("$GM,CMD,0,0#");
    assert(r == GM_PARSE_FIELD_COUNT);

    /* glued frames */
    gm_stream_init(&s);
    feed("$GM,CMD,-10,20,TRACK#$GM,CMD,0,0,STOP#");
    assert(r == GM_PARSE_OK && c.pan == 0 && c.tilt == 0 && !strcmp(c.mode, "STOP"));

    puts("gm_protocol tests passed");
    return 0;
}
