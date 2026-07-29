/* Test for expressions that does not provide a result */
#include <stdbool.h>

#if !defined(__STDC_VERSION__) || __STDC_VERSION__ < 202311L
#define auto __auto_type
#endif

/*
 * min()/max() macros that also do strict type-checking..
 */
#define min(x, y)                               \
    ({                                          \
        const auto _x = (x);                    \
        const auto _y = (y);                    \
        (void)(&_x == &_y); /* typecheck */     \
        _x < _y ? _x : _y;                      \
    })


int test_min_func(void)
{
	int x = 3;
	int y = 2;
	int z = 1;

	z = min(x, y);

	if (min(x, y) > 4)
		return 0;

	if (min(x, 3))
		return 0;

	if (min(1, 3))
		return 0;

	if (min(x, y))
		return 0;
}

int main(int argc, char *argv[])
{
	test_min_func();

	return 0;
}
