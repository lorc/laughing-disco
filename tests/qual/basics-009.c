/* Test for basic boolean operations */
#include <stdbool.h>

int test_lt(int a)
{
        if (a < -255)
                return 1;
        if (a < -1)
                return 1;
        if (a < 0)
                return 1;
        if (a < 1)
                return 1;
        if (a < 256)
                return 1;
        if (a < 1024)
                return 1;
        if (a < 65536)
                return 1;
        if (a < 65538)
                return 1;

        return 0;
}

int main(int argc, char *argv[])
{

        test_lt(65537);
        test_lt(1025);
        test_lt(257);
        test_lt(2);
        test_lt(1);
        test_lt(0);
        test_lt(-1);
        test_lt(-2);
        test_lt(-256);

        return 0;
}
