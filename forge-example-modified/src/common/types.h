#ifndef TYPES_H
#define TYPES_H

typedef struct {
    short noi;  /* number of increases */
    short cv;   /* current value */
} counter_state_t;

typedef enum {
    COUNTER_OK       =  0,
    COUNTER_ERROR    = -1,
    COUNTER_OVERFLOW = -2
} counter_status_t;

#endif /* TYPES_H */