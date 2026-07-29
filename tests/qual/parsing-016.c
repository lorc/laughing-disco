/* Test for variables assigning by boolean expressions */
#include <stdbool.h>

bool test_complex_assign(int a, int b, int c)
{

        bool d =    (!a && !b &&  c) ||
                    (!a &&  b && !c) ||
                    ( a &&  b &&  c) ||
                    ( a && !b && !c);

        return d;
}

int main(int argc, char *argv[])
{
	test_complex_assign(false, false, false);
	test_complex_assign(true, false, false);

	return 0;
}
