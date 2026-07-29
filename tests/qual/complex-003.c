/* Test for complex boolean expressions */
#include <stdbool.h>

int test_func(bool a, bool b, bool c, bool d)
{
        if (a || b || !c || !d)
                return 1;
        return 0;
}

int main(int argc, char *argv[])
{
        test_func(false, false, true, true);
        test_func(true, false, true, true);
        test_func(false, true, true, true);
        test_func(false, false, false, true);
        test_func(false, false, true, false);

        return 0;
}
