/* Test for basic boolean operations */
#include <stdbool.h>

int test_gt(int a)
{
        if (a > 65538)
                return 1;
        if (a > 65536)
                return 1;
        if (a > 1024)
                return 1;
        if (a > 256)
                return 1;
        if (a > 1)
                return 1;
        if (a > 0)
                return 1;
        if (a > -1)
                return 1;
        if (a > -255)
                return 1;

        return 0;
}

int main(int argc, char *argv[])
{

        test_gt(65537);
        test_gt(1025);
        test_gt(257);
        test_gt(2);
        test_gt(1);
        test_gt(0);
        test_gt(-1);
        test_gt(-2);
        test_gt(-256);

        return 0;
}
