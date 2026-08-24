#include "counter.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    short val = (argc > 1) ? (short)atoi(argv[1]) : 3;

    global_counter.noi = 0;
    global_counter.cv  = 0;

    for (short i = 0; i < 10; i++) {
        counter_status_t status = add((short)(val - i));
        if (status == COUNTER_OVERFLOW) {
            printf("Counter overflow at iteration %d.\n", i);
            break;
        }
    }
    printf("noi=%d cv=%d\n", global_counter.noi, global_counter.cv);
    return 0;
}