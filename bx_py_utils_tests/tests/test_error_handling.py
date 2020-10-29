from bx_py_utils.error_handling import print_exc_plus


def test_print_exc_plus(capsys):
    test_message = 'Only a Test'
    try:
        raise AssertionError(test_message)
    except BaseException:
        print_exc_plus()

    captured = capsys.readouterr()
    assert captured.out == ''

    output = captured.err

    assert 'Locals by frame, most recent call first:' in output
    assert '/bx_py_utils_tests/tests/test_error_handling.py", line' in output
    assert "test_message = 'Only a Test'" in output


def test_print_exc_plus_max_chars(capsys):
    try:
        x = '12345678901234567890'
        raise AssertionError(x)
    except BaseException:
        print_exc_plus(max_chars=15)

    captured = capsys.readouterr()
    assert captured.out == ''

    output = captured.err

    assert 'Locals by frame, most recent call first:' in output
    assert '/bx_py_utils_tests/tests/test_error_handling.py", line' in output
    assert "x = '12345678901..." in output
