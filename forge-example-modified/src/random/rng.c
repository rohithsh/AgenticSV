#include "rng.h"

short valueToBeAdded(short value) {
#if VAL_POS
    if (value < 0) {
        value = -value;
    }
#endif
    if (value < -RANGE) {
        return -RANGE;
    } else if (value > RANGE) {
        return RANGE;
    }
    return value;
}