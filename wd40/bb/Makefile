
all:
	gcc -c bb.c ../cetara/diag/gdb.c -fPIC -I ../.. -DDEBUG
	ar cr linux-x64/libbb.a bb.o gdb.o
