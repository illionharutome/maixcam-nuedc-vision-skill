#ifndef VISION_PARSER_H
#define VISION_PARSER_H

#include <stdbool.h>
#include <stdint.h>
#include "vision_command.h"

void vision_parser_init(void);
bool vision_parser_feed(uint8_t byte, VisionCommand_t *command);

#endif

