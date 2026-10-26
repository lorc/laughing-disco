
/* Test for decisions defined in a header and used from several
 * translation units */
#include "test_include.h"

bool second_and(int x);
bool second_simple(int x);
int test_second_local(int a);

/* First translation unit: exercises only the false side of the header
 * decisions. */
bool first_and(int x)
{
	return hdr_and(x, 1);
}

bool first_simple(int x)
{
	return hdr_simple(x);
}

/* Same shape as hdr_and(), but local to this CU */
int test_first_local(int a)
{
	if (a > 0 && a < 10)
		return 1;
	return 0;
}

int main()
{
	second_and(1);
	second_simple(1);

	first_and(-1);
	first_simple(-1);

	test_second_local(1);

	test_first_local(5);
	test_first_local(-1);

	return 0;
}
