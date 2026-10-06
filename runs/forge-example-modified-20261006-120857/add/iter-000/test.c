/* generated unit test - do not edit by hand */
#include <stdio.h>
#include "counter.h"

int main(void) {
    int guarded = 0;
    for (int i = 0; i < 1000; i++) {
        global_counter.noi = -1;
        global_counter.cv = -1;
        counter_status_t s = add(0);
        if (s == -2) guarded++;
        (void)s;
    }
    if (guarded == 1000) {
        printf("VERDICT: GUARDED\n");
    } else {
        printf("VERDICT: CLEAN (guarded %d/1000)\n", guarded);
    }
    return 0;
}
