/* Test for complex boolean expressions */
#include <stdbool.h>

int test_and(bool a, bool b, bool c, bool d)
{
        if (a && b && c && d)
                return 1;
        return 0;
}

int main(int argc, char *argv[])
{
        test_and(true, true, true, true);
        test_and(false, true, true, true);
        test_and(true, false, true, true);
        test_and(true, true, false, true);
        test_and(true, true, true, false);

        return 0;
}
