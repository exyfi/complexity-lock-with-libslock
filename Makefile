PLATFORM_NUMA=1

ifeq ($(DEBUG),1)
  DEBUG_FLAGS=-Wall -ggdb -DDEBUG
  COMPILE_FLAGS=-O0 -DADD_PADDING -fno-inline
else
  DEBUG_FLAGS=-Wall
  COMPILE_FLAGS=-O2 -DADD_PADDING
endif

ifndef PLATFORM
PLATFORM=-DDEFAULT
endif

ifndef OS
OS=-DLINUXOS
endif

ifeq ($(PLATFORM), -DOPTERON)	#allow OPTERON_OPTIMIZE only for OPTERON platform
OPTIMIZE=-DOPTERON_OPTIMIZE
else
OPTIMIZE=
endif

COMPILE_FLAGS += $(PLATFORM)
COMPILE_FLAGS += $(OPTIMIZE)
COMPILE_FLAGS += $(OS)
COMPILE_FLAGS += -DCORE_NUM=10

GCC := g++ -std=gnu++11
LIBS := -lrt -pthread -lnuma

INCLUDE_LIBSLOCK := ./libslock/include/
SRC_LIBSLOCK := ./libslock/src/
INCLUDE := ./src/common/

INCLUDES := -I $(INCLUDE_LIBSLOCK) -I $(SRC_LIBSLOCK) -I $(INCLUDE)

MAIN_PART := $(GCC)  $(COMPILE_FLAGS) $(INCLUDES)

#spinlock: src/locking_scheme.cpp
#	$(MAIN_PART) -DUSE_SPINLOCK_LOCKS ./libslock/src/spinlock.c src/locking_scheme.cpp -o locking_scheme.spin

#ttas: src/locking_scheme.cpp
#	$(MAIN_PART) -DUSE_TTAS_LOCKS ./libslock/src/ttas.c src/locking_scheme.cpp -o locking_scheme.ttas

#ticket: src/locking_scheme.cpp
#	$(MAIN_PART) -DUSE_TICKET_LOCKS ./libslock/src/ticket.c src/locking_scheme.cpp -o locking_scheme.ticket

#hticket: src/locking_scheme.cpp
#	$(MAIN_PART) -DUSE_HTICKET_LOCKS ./libslock/src/htlock.c src/locking_scheme.cpp -o locking_scheme.hticket

mcs: src/locking_scheme.cpp
	$(MAIN_PART) -DUSE_MCS_LOCKS ./libslock/src/mcs.c src/locking_scheme.cpp -o locking_scheme.mcs $(LIBS)

clh: src/locking_scheme.cpp
	$(MAIN_PART) -DUSE_CLH_LOCKS ./libslock/src/clh.c src/locking_scheme.cpp -o locking_scheme.clh $(LIBS)

#hclh: src/locking_scheme.cpp
#	$(MAIN_PART) -DUSE_HCLH_LOCKS ~/libslock/src/hclh.c src/locking_scheme.cpp -o locking_scheme.hclh

clean:
	rm locking_scheme.*