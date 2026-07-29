/* Test for const expressions */
#include <stdbool.h>

void test_const_expressions(void)
{
	if (2 < 3)
		return;

	if (!false)
		return;

	if (false || true)
		return;

	if (sizeof(int) == 2)
		return;

	while (sizeof(char) == 1)
		return;

	while (!(sizeof(char) != sizeof(int)))
		return;

	while ( (1 << sizeof(char)) > 8)
		return;

}

int main(int argc, char *argv[])
{
	test_const_expressions();

        return 0;
}

