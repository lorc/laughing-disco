#include <stdbool.h>

bool test_mult_cond(bool a, bool b, bool c, bool d)
{
        if ( a ) {
                if (a && b) {
                        if (a && b && c) {
                                if (a && b && c && d) {
                                        return true;
                                }
                        }
                }
        }

        return false;
}

int main(int argc, char *argv[])
{
	test_mult_cond(true, false, false, false);
	test_mult_cond(true, true , false, false);
	test_mult_cond(true, true , true , false);
	test_mult_cond(true, true , true , true );

        return 0;
}
