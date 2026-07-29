/* Test for basic boolean operations */
#include <stdbool.h>

int test_neq(int a, int b)
{
	if (a!=b)
		return 1;
        return 0;
}

int main(int argc, char *argv[])
{
	test_neq(0, 1);
	test_neq(1, 1);

        return 0;
}
