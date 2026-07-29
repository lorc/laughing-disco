/* Test for basic boolean expressions */
#include <stdbool.h>

int test_simple_and(bool a, bool b)
{
        if (a && b)
                return 1;
        return 0;
}

int main(int argc, char *argv[])
{

	test_simple_and(false, false);
	test_simple_and(true, false);

        return 0;
}
