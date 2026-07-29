#include <stdbool.h>

#define MIN(x, y) ((x) < (y) ? (x) : (y))

int main(void)
{
	int a, b=1, c=2;

	a = MIN(b, c);

	return 0;
}
