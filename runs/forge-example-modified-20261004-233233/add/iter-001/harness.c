/* generated harness */
#include "../../../src/counter.c"

short __VERIFIER_nondet_short(void);
void __CPROVER_assume(_Bool);

short valueToBeAdded(short value) {
    short __cex_mockin_valueToBeAdded_value = value;
    short r = __VERIFIER_nondet_short();
    __CPROVER_assume(-RANGE <= r && r <= RANGE);
    return r;
}

int main(void) {
    short __cex_global_counter_noi = __VERIFIER_nondet_short();
    short __cex_global_counter_cv = __VERIFIER_nondet_short();
    global_counter.noi = __cex_global_counter_noi;
    global_counter.cv = __cex_global_counter_cv;
    short __cex_arg_some_value = __VERIFIER_nondet_short();
    add(__cex_arg_some_value);
#ifdef HV_REACH
    __CPROVER_assert(0, "hv_reach");
#endif
    return 0;
}
