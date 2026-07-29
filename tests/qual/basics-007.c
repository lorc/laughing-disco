/* Test for basic boolean expressions */
#include <stdbool.h>

int test_neq(bool a, bool b)
{
        if (a != b)
                return 1;
        return 0;
}

int main(int argc, char *argv[])
{
	test_neq(true, true);
	test_neq(true, false);

        return 0;
}
