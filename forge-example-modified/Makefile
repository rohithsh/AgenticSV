CC       = clang
CFLAGS   = -Wall -Wextra -std=c99
DEFINES  = -DRANGE=10 -DVAL_POS=1
INCLUDES = -I includes/ -I src/common/
SOURCES  = src/main.c src/counter.c src/random/rng.c
OBJECTS  = $(SOURCES:.c=.o)
TARGET   = counter2

all: $(TARGET)
$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) $(OBJECTS) -o $(TARGET)
%.o: %.c
	$(CC) $(CFLAGS) $(DEFINES) $(INCLUDES) -c $< -o $@
negative: DEFINES = -DRANGE=10 -DVAL_POS=0
negative: clean $(TARGET)
clean:
	rm -f $(OBJECTS) $(TARGET)
.PHONY: all clean negative