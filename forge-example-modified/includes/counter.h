#ifndef COUNTER_H
#define COUNTER_H

#include "types.h"

extern counter_state_t global_counter;

/** Adds a value to the counter and updates state. */
counter_status_t add(short some_value);

#endif /* COUNTER_H */