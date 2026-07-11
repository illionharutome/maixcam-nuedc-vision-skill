#ifndef PROTOCOL_TRACK1_H
#define PROTOCOL_TRACK1_H
#include <stddef.h>
#include <stdint.h>
#define TRACK1_FRAME_MAX 192u
#define TRACK1_TEXT_MAX 20u
typedef struct { uint8_t ok; int32_t target_cx,target_cy,aim_cx,aim_cy,error_x,error_y; float score,fps; char status[TRACK1_TEXT_MAX]; } Track1Packet;
typedef struct { char buffer[TRACK1_FRAME_MAX]; size_t length; uint8_t collecting,overflow; } Track1Stream;
typedef enum { TRACK1_NONE=0, TRACK1_PACKET=1, TRACK1_REJECTED=-1 } Track1StreamResult;
void track1_stream_init(Track1Stream *stream);
Track1StreamResult track1_stream_push(Track1Stream *stream, char byte, Track1Packet *out);
/* WARNING: modifies frame in-place; pass a writable buffer. */
int track1_parse_frame(char *frame, Track1Packet *out);
#endif
