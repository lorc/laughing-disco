
/* Second translation unit: exercises only the true side of the header
 * decisions. */
#include "test_include.h"

bool second_and(int x)
{
	return hdr_and(x, 1);
}

bool second_simple(int x)
{
	return hdr_simple(x);
}

int test_second_local(int a)
{
	if (a > 0)
		return 1;
	return 0;
}
