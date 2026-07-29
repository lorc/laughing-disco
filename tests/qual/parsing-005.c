/* Test for __builtin_stuff */
#include <stdbool.h>

#define likely(x)     __builtin_expect(!!(x),1)
#define unlikely(x)   __builtin_expect(!!(x),0)

int test_likely1(void)
{
	int x = 3;

	if (likely(x == 3))
		return 1;

	return 0;
}

int test_likely2(void)
{
	int x = 3;

	if (unlikely(x == 1))
		return 2;

	return 0;
}

int test_likely3(void)
{
	int x = 3;

	if (unlikely(!!(x == 1)) && x==17)
		return 3;

	return 0;
}

int main(int argc, char *argv[])
{
	test_likely1();
	test_likely2();
	test_likely3();

	return 0;
}
