/* generated contract check - do not edit by hand */
#include <limits.h>
#include "../../../src/random/rng.c"
#include <assert.h>

short __VERIFIER_nondet_short(void);

int main(void) {
    short __cex_in_value = __VERIFIER_nondet_short();
    short value = __cex_in_value;
    short r = valueToBeAdded(value);
    assert(value >= 0 ==> (r >= 0 && r <= RANGE));
    return 0;
}
