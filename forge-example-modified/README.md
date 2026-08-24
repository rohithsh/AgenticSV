<!--
This file is part of HarnessForge:
https://gitlab.com/sosy-lab/software/harnessforge

SPDX-FileCopyrightText: 2025 Dirk Beyer <https://www.sosy-lab.org>

SPDX-License-Identifier: CC-BY-ND-4.0
-->

# Counter Example Project

This tutorial project is adapted from `https://gitlab.com/sosy-lab/software/harnessforge`.

## Overview

We have a simple counter application that tracks state changes through random value additions. The counter maintains two values:
- `numberOfIncreases`: How many times the counter has been modified  
- `currentValue`: The current accumulated value

The main operation is `addRandom()`, which adds a random short integer within a given range to the counter,
while checking for overflow conditions.
If an overflow would occur, the counter is not increased further and an overflow error is reported.
The maximum size of the random integer is controlled by the `RANGE` macro. We use value 10.

## Project Structure

The project we consider is a small C application with the following source files:

- `includes/counter.h` - The declarations of the types and methods of the counter
- `includes/rng.h` - The random number generator interface that we use to get a random number
- `src/common/types.h` - Shared type definitions: the counter state and the status of the counter (to signal overflows)
- `src/counter.c` - The counter implementation with the `addRandom()` function
- `src/random/rng.c` - The random number generator implementation
- `src/main.c` - A main method that demonstrates the counter operations
- `utils/helper.c` - Utility functions that we use to print the counter state and status in the main method; this file is not required by the counter methods themselves.

A `Makefile` defines how to build the project.

