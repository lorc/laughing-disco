/* Test for basic boolean operations */
#include <stdbool.h>

int test_gte(int a)
{
        if (a >= 65538)
                return 1;
        if (a >= 65536)
                return 1;
        if (a >= 1024)
                return 1;
        if (a >= 256)
                return 1;
        if (a >= 1)
                return 1;
        if (a >= 0)
                return 1;
        if (a >= -1)
                return 1;
        if (a >= -255)
                return 1;

        return 0;
}

int main(int argc, char *argv[])
{
	test_gte(65536);
	test_gte(1024);
	test_gte(256);
	test_gte(1);
	test_gte(0);
	test_gte(-1);
	test_gte(-255);
	test_gte(-256);

        return 0;
}
