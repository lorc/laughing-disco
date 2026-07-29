/* Test for complex boolean expressions */
#include <stdbool.h>

int test_func(bool a, bool b, bool c, bool d)
{
        if (a && b && !c && !d)
                return 1;
        return 0;
}

int main(int argc, char *argv[])
{

        test_func(true, true, false, false);
        test_func(false, true, false, false);
        test_func(true, false, false, false);
        test_func(true, true, true, false);
        test_func(true, true, false, true);

        return 0;
}
