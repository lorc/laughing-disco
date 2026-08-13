#include <stdbool.h>

static inline __attribute__((__always_inline__)) int inline_func(int x)
{
	if (x==1)
		return 2;
	if (x==2)
		return 4;
	if (x==3)
		return 6;
	if (x==4)
		return 8;
	if (x==5)
		return 10;
	if (x==6)
		return 12;
	if (x==7)
		return 14;
	return -1;
}

#define complex_macro(y)				\
	({						\
	union { typeof((y)) val; long yy; } x_;		\
        x_.yy = y;					\
	x_.val = inline_func(x_.yy);			\
	x_.val;						\
	})

#define complex_macro_with_bool_expr(y)			\
	({						\
	union { typeof((y)) val; long yy; } x_;		\
        x_.yy = y;					\
	x_.val = inline_func(x_.yy);			\
	(void)(x_.val == y);				\
	x_.val;						\
	})


int global_var1 = 16;
int global_var2 = 32;

#define complex_macro_with_bool_expr3(p)				\
	({													\
		char __p = (p);									\
		(__p >= global_var1) && (__p < global_var2); 	\
	})


int test_func()
{
	int z = 0;

	if (complex_macro(4) == 8)
		return 1;
	complex_macro_with_bool_expr(z);
	return 0;
}

static bool test(unsigned int nr, unsigned int var)
{
	return (var >> nr) & 1;
}

#define test_bit(nr, addr) ({		\
	test((nr), *(addr));			\
})

int test_func2(unsigned int nr, unsigned int var)
{
	if (nr >= 32 || !test_bit(nr, &var))
		return 1;

	return 1;
}

int test_func3()
{
	int a = 23;
	int b = 35;

	if (complex_macro_with_bool_expr3(a) && complex_macro_with_bool_expr3(b))
		return 1;

	return 0;
}

int main(void)
{
	test_func();

	test_func2(1, 0x2);
	test_func2(64, 0x0);

	test_func3();

	return 0;
}
