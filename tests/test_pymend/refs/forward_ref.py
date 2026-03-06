def simple_forward_ref_return() -> "MyClass":
    return MyClass()


def complex_forward_ref_return() -> "list[MyClass]":
    return [MyClass()]


def forward_ref_param_and_return(a: "MyClass", b: int) -> "MyClass":
    return a


def no_forward_ref(a: int, e="test") -> str:
    return str(a)
