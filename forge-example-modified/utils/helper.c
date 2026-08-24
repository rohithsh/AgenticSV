/*
 * This file is part of HarnessForge:
 * https://gitlab.com/sosy-lab/software/harnessforge
 *
 * SPDX-FileCopyrightText: 2025 Dirk Beyer <https://www.sosy-lab.org>
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include "types.h"
#include <stdio.h>

void printStatus(counter_status_t status) {
    switch (status) {
        case COUNTER_SUCCESS:
            printf("Status: Success\n");
            break;
        case COUNTER_ERROR:
            printf("Status: Error\n");
            break;
        case COUNTER_OVERFLOW:
            printf("Status: Overflow detected\n");
            break;
        default:
            printf("Status: Unknown\n");
            break;
    }
}