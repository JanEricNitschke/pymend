"""Test reference file for ExceptionGroup and try/except* raise handling."""


def exc_group_all_caught():
    try:
        raise ExceptionGroup("g", [ValueError(), TypeError()])
    except* ValueError:
        pass
    except* TypeError:
        pass


def exc_group_partial_catch():
    try:
        raise ExceptionGroup("g", [ValueError(), TypeError()])
    except* ValueError:
        pass


def exc_group_nothing_caught():
    try:
        raise ExceptionGroup("g", [ValueError(), TypeError()])
    except* KeyError:
        pass


def exc_group_baseexception():
    try:
        raise ExceptionGroup("g", [ValueError()])
    except* BaseException:
        pass


def exc_group_tuple_arg():
    try:
        raise ExceptionGroup("g", (ValueError(), TypeError()))
    except* ValueError:
        pass
    except* TypeError:
        pass


def exc_group_runtime_var():
    try:
        raise ExceptionGroup("g", errors)
    except* ValueError:
        pass


def exc_group_tuple_handler():
    try:
        raise ExceptionGroup("g", [ValueError(), TypeError()])
    except* (ValueError, TypeError):
        pass


def exc_group_exception_catches_builtin():
    try:
        raise ExceptionGroup("g", [ValueError()])
    except* Exception:
        pass


def exc_group_exception_does_not_catch_custom():
    try:
        raise ExceptionGroup("g", [CustomError()])
    except* Exception:
        pass


def exc_group_bare_name_members():
    try:
        raise ExceptionGroup("g", [ValueError, TypeError])
    except* ValueError:
        pass
    except* TypeError:
        pass


def exc_group_hierarchy_catch():
    try:
        raise ExceptionGroup("g", [FileNotFoundError()])
    except* OSError:
        pass


def exc_group_custom_group():
    try:
        raise CustomGroup("g", [ValueError()])
    except* ValueError:
        pass


def single_exc_caught_by_except_star():
    try:
        raise ValueError
    except* ValueError:
        pass
