#ifndef RNG_H
#define RNG_H

#ifndef RANGE
#error "RANGE macro is not defined"
#endif

#ifndef VAL_POS
#error "VAL_POS macro is not defined"
#endif

/** Clamps value into [-RANGE, RANGE]; if VAL_POS, into [0, RANGE]. */
short valueToBeAdded(short value);

#endif /* RNG_H */