/* Test for expressions that does not provide a result */

int test_simple_nops(void)
{
	int x = 3;
	int y = 0;

	{(void)(x==1);};

	y = ({x==1, x==2, x==3;});

	return y;
}

int main(int argc, char *argv[])
{
	test_simple_nops();

	return 0;
}
