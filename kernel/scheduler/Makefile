obj-m += aimos_scheduler.o

KDIR  := /lib/modules/$(shell uname -r)/build
PWD   := $(shell pwd)

all:
	make -C $(KDIR) M=$(PWD) modules

clean:
	make -C $(KDIR) M=$(PWD) clean

install:
	sudo insmod aimos_scheduler.ko

uninstall:
	sudo rmmod aimos_scheduler
