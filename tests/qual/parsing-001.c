#include <stdbool.h>

int global_var = 2;

int test_global_var()
{
        if (global_var == 2)
                return 2;
        return 0;
}

int main(int argc, char *argv[])
{

        test_global_var();

        global_var = 1;

        test_global_var();

        return 0;
}
