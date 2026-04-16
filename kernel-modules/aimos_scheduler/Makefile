obj-m += aimos_scheduler.o

KDIR := /lib/modules/6.19.11-arch1-1/build

all:
	make -C $(KDIR) M=$(PWD) modules

clean:
	make -C $(KDIR) M=$(PWD) clean
