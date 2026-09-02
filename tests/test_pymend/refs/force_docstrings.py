"""Module docs."""

def _private_function()->None:
    pass


def public_function()->None:
    pass

def _private_incorrect_function(arg: int)->None:
    """Incorrect docstring

    """

def public_incorrect_docstring(arg: int)->None:
    """Incorrect docstring

    """

class _PrivateClass:
    pass

class PublicClass:
    def __init__():
        pass

    def _private_method()->None:
        pass

    def _private_method_with_incorrect_doc()->None:
        """Incorrect docstring

        """

    def public_method()->None:
        pass
