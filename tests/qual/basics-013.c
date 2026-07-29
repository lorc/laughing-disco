/* Test for basic boolean operations */
#include <stdbool.h>

int test_eq(int a, int b)
{
	if (a==b)
		return 1;
        return 0;
}

int main(int argc, char *argv[])
{
	test_eq(0, 1);
	test_eq(1, 1);

        return 0;
}
