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
