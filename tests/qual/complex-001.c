/* Test for complex boolean expressions */
#include <stdbool.h>

int test_or(bool a, bool b, bool c, bool d)
{
        if (a || b || c || d)
                return 1;
        return 0;
}

int main(int argc, char *argv[])
{
        test_or(false, false, false, false);
        test_or(true, false, false, false);
        test_or(false, true, false, false);
        test_or(false, false, true, false);
        test_or(false, false, false, true);

        return 0;
}
