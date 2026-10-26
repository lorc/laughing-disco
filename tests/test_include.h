
/* Decisions in a header get instantiated in every translation unit that
 * uses them, so each CU ends up with its own copy of the same source
 * expression. */
#include <stdbool.h>

static bool __attribute__((__always_inline__)) hdr_and(int a, int b)
{
	return a > 0 && b > 0;
}

static bool hdr_simple(int a)
{
	return a > 0;
}
