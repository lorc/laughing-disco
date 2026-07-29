#include <stdbool.h>

typedef unsigned long u64;

void test_against_sizeof()
{
	u64 x = 12;
	char buf[64];

	if ( x > sizeof(u64))
		return;

	if ( x > sizeof(buf))
		return;
}

int main(int argc, char *argv[])
{

	test_against_sizeof();

        return 0;
}
