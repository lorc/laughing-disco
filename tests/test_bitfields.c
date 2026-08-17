

struct test_st {
    union {
        struct {
            unsigned long f1:8;
            unsigned long f2:8;
            unsigned long f3:8;
            unsigned long f4:1;
            unsigned long f5:5;
            unsigned long f6:1;
            unsigned long f7:1;
            unsigned long f8:8;
            unsigned long f9:24;
        };
    } bits;
} g_test_st;

int test_func(struct test_st *st)
{
    if (st->bits.f4 == 0)
        return 1;

    if (st->bits.f4 != 0)
        return 2;

    if (st->bits.f4 == 1)
        return 3;

    if (st->bits.f4 != 1)
        return 4;

    return 0;
}


int main()
{
    test_func(&g_test_st);

    g_test_st.bits.f4 = 1;

    test_func(&g_test_st);


    return 0;
}