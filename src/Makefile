CC=g++
CFLAGS=-O3 -Wall
LDFLAGS=-L/afs/cern.ch/work/k/kiliakis/install/lib -lpapi
SOURCES=main.cpp
OBJECTS=$(SOURCES:.cpp=.o)
EXECUTABLE=main
LIB=libpapi.so

all: $(SOURCES) $(EXECUTABLE) $(LIB)

$(EXECUTABLE): $(OBJECTS) 
	$(CC) $(LDFLAGS) $(OBJECTS) -o $@

$(LIB): libpapi.cpp
	$(CC) $(LDFLAGS) $(CFLAGS) -shared -fPIC $< -o $@

.cpp.o:
	$(CC) -c $(CFLAGS) $< -o $@

clean:
	rm *.o $(EXECUTABLE) $(LIB)
