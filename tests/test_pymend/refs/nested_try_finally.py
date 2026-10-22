"""Test reference file for try/finally raise handling."""


def inner_try_finally_does_not_clear_outer_caught():
    try:
        try:
            pass
        finally:
            pass

        raise ValueError
    except ValueError:
        pass
