"""Module docs."""

def _private_function(arg: int)->None:
    """This is an incorrect docstring."""
    pass


def public_function()->None:
    """Do nothing.

    This docstring is correct.
    """
    pass

def undocumented_function()->None:
    pass
