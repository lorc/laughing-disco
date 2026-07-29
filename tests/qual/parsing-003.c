#include <stdbool.h>

#define NULL ((void*)0)

void test_against_ptr()
{
	int x;
	void *ptr = &x;

	if (ptr != NULL)
		return;
}


int main(int argc, char *argv[])
{

	test_against_ptr();

        return 0;
}
