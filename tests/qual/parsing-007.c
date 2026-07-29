/* Test for const expressions */
#include <stdbool.h>

void test_simple_const(void)
{
        if (1)
                return;
        if (0)
                test_simple_const();

        do
        {
                return;
        } while (0);

        for (; 1 ; )
                return;

        while (true)
                return;

}

int main(int argc, char *argv[])
{
        test_simple_const();

        return 0;
}

