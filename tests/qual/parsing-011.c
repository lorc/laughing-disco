/* Test for conditional expressions with function calls */
#include <stdbool.h>

bool get_xor(bool a, bool b) {
        return a != b;
}

int test_or_call(bool a, bool b, bool c)
{
        bool d = get_xor(a, b) || get_xor(b, c);

        return d;
}

int main(int argc, char *argv[])
{
        test_or_call(false, false, true);
        test_or_call(true, false, true);
        test_or_call(false, true, true);

        return 0;
}
