/* Test for const expressions */
#include <stdbool.h>

void test_half_const_expressions(void)
{
	int x = 0;
	int y = 5;

	if (0 && y < x)
		return;

	if (false && y > x)
		return;

	if (1 || y < x)
		return;

	if (true || y < x)
		return;
}

int main(int argc, char *argv[])
{
	test_half_const_expressions();

        return 0;
}
