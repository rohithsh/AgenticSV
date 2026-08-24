#include "counter.h"
#include "rng.h"
#include <limits.h>
#include <assert.h>

counter_state_t global_counter = {
    .noi = 0,
    .cv  = 0,
};

counter_status_t add(short some_value) {
    short value = valueToBeAdded(some_value);

    if (global_counter.noi >= SHRT_MAX
            || (value > 0 && global_counter.cv > SHRT_MAX - value)
            || (value < 0 && global_counter.cv < SHRT_MIN - value)) {
        return COUNTER_OVERFLOW;
    }

    short noi_old = global_counter.noi;
    short cv_old  = global_counter.cv;

    global_counter.noi++;
    global_counter.cv += value;

    assert(global_counter.noi >= noi_old);

    short diff = global_counter.cv - cv_old;
#if VAL_POS
    assert(0 <= diff && diff <= RANGE);
#else
    assert(-RANGE <= diff && diff <= 0);
#endif

    return COUNTER_OK;
}