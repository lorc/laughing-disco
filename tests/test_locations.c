#include <stdbool.h>
#include "likely.h"

struct dt_device_match {
    const char *path;
    const char *type;
    const char *compatible;
    const bool not_available;
    int num;
    /*
     * Property name to search for. We only search for the property's
     * existence.
     */
    const char *prop;
    const void *data;
} g_matches;

#define macro1(x) (((x)->data == 0))
#define macro2(x) (!!x)
#define macro3 (g_matches.num == 2)
#define macro4 (g_matches.num >= 1)

#define MIN(x, y) ((x) < (y) ? (x) : (y))

int test_func(int a)
{
	if (a)
		return 1;

	return 0;
}

int main(void)
{
	int x = 0;
	volatile int a, b = 1, c = 2;
	const struct dt_device_match *matches = &g_matches;

	while ( matches->path || matches->type ||
		matches->compatible || matches->not_available || matches->prop ) {
		x++;
		if (x>3)
			break;
	}

	if (macro2(macro1(matches)) && x == 0)
	    return 0;

	if (likely(macro1(matches)))
	    return 0;

	a = MIN(b, c);

	test_func(macro3 ? 23 : macro4 ? 123 : 1234);

	return 0;
}
