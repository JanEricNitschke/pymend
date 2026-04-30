"""Test reference file for try/except raise handling."""


def caught_raise():
    try:
        raise ValueError
    except ValueError:
        pass


def uncaught_raise():
    try:
        raise ValueError
    except TypeError:
        pass


def bare_except():
    try:
        raise ValueError
    except:
        pass


def baseexception_catches_all():
    try:
        raise ValueError
    except BaseException:
        pass


def exception_catches_builtin():
    try:
        raise ValueError
    except Exception:
        pass


def exception_does_not_catch_custom():
    try:
        raise CustomError
    except Exception:
        pass


def baseexception_catches_custom():
    try:
        raise CustomError
    except BaseException:
        pass


def hierarchy_oserror_catches_filenotfound():
    try:
        raise FileNotFoundError
    except OSError:
        pass


def tuple_handler_catches():
    try:
        raise ValueError
    except (ValueError, TypeError):
        pass


def tuple_handler_partial():
    try:
        raise KeyError
    except (ValueError, TypeError):
        pass
