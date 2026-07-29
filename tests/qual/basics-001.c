/* Test for basic boolean expressions */
#include <stdbool.h>

int test_simple_or(bool a, bool b)
{
        if (a || b)
                return 1;
        return 0;
}

int main(int argc, char *argv[])
{

        test_simple_or(false, false);
        test_simple_or(true, false);
        test_simple_or(false, true);
        test_simple_or(true, true);

        return 0;
}
