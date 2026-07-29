/* Test for basic boolean expressions */
#include <stdbool.h>

int test_not(bool a)
{
        if (!a)
                return 1;
        return 0;
}

int main(int argc, char *argv[])
{

        test_not(true);
        test_not(false);

        return 0;
}
