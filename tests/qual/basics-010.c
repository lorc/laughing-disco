/* Test for basic boolean operations */
#include <stdbool.h>

int test_lte(int a)
{
        if (a <= -255)
                return 1;
        if (a <= -1)
                return 1;
        if (a <= 0)
                return 1;
        if (a <= 1)
                return 1;
        if (a <= 256)
                return 1;
        if (a <= 1024)
                return 1;
        if (a <= 65536)
                return 1;
        if (a <= 65538)
                return 1;

        return 0;
}

int main(int argc, char *argv[])
{

        test_lte(65537);
        test_lte(65536);
        test_lte(1024);
        test_lte(256);
        test_lte(1);
        test_lte(0);
        test_lte(-1);
        test_lte(-255);

        return 0;
}
