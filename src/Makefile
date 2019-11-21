CC=g++
CFLAGS=-O3 -Wall
LDFLAGS=-L/home/kiliakis/install/lib
SOURCES=main.cpp
OBJECTS=$(SOURCES:.cpp=.o)
EXECUTABLE=exe/main
LIB=lib/libmypapi.so

all: $(LIB) $(SOURCES) $(EXECUTABLE)

$(EXECUTABLE): $(OBJECTS)
	$(CC) $(LDFLAGS) -Llib -lmypapi $(OBJECTS) -o $@ -lpapi

$(LIB): libpapi.cpp
	mkdir -p lib
	$(CC) $(LDFLAGS) $(CFLAGS) -shared -fPIC $< -o $@ -lpapi

.cpp.o:
	$(CC) -c $(CFLAGS) $< -o $@

clean:
	rm *.o $(EXECUTABLE) $(LIB)
