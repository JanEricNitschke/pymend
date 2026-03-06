"""Unit tests for pymend.file_parser.py."""

import ast

import pytest

from pymend.docstring_info import (
    ClassDocstring,
    FixerSettings,
    FunctionDocstring,
    Parameter,
)
from pymend.file_parser import AstAnalyzer, ast_unparse


class TestAstAnalyzer:
    """Test ast analyzer."""

    def test_handle_class_body(self) -> None:
        """Handle class body parsing."""
        class_definition = '''\
class C:
    def __init__(self):
        self._x = None
        self.test1 = "test"
        self.test2: Optional[int] = None
        self.test1 = "a"
        self.test3 = self.test4 = None
        self.test5, self.test6 = 1, 2

    @property
    def x(self) -> str | None:
        """I'm the 'x' property."""
        return self._x

    @x.setter
    def x(self, value):
        self._x = value

    @staticmethod
    def a(self, a):
        pass

    @classmethod
    def b(self, b):
        pass

    def c(self, c):
        pass
'''
        class_node = ast.parse(class_definition).body[0]
        analyzer = AstAnalyzer(class_definition, settings=FixerSettings())

        attributes, methods = analyzer.handle_class_body(class_node)

        expected_attributes = [
            Parameter("test1", "_type_", None),
            Parameter("test2", "_type_", None),
            Parameter("test3", "_type_", None),
            Parameter("test4", "_type_", None),
            Parameter("test5", "_type_", None),
            Parameter("test6", "_type_", None),
            Parameter("x", "str | None", None),
        ]
        expected_methods = ["c(c)"]
        assert attributes == expected_attributes
        assert methods == expected_methods

    def test_handle_skipped_class_body(self) -> None:
        """Ensure that classes are skipped as desired."""
        class_definitions = """\
class C:
    def __init__(self):
        self._x = None
        self.test1 = "test"

class Skipped:
    def __init__(self):
        self._x = None
"""
        analyzer = AstAnalyzer(
            class_definitions, settings=FixerSettings(ignored_classes=["Skipped"])
        )
        nodes = [
            node
            for node in analyzer.parse_from_ast()
            if isinstance(node, ClassDocstring)
        ]
        assert len(nodes) == 1
        assert nodes[0].name == "C"

    def test_shebang_pragma_handling(self) -> None:
        """Ensure that shebang pragma is handled correctly."""
        shebang_pragma = """\
#!/usr/bin/env python
# -*- coding: big5 -*-
"""
        analyzer = AstAnalyzer(shebang_pragma, settings=FixerSettings())
        nodes = analyzer.parse_from_ast()
        assert len(nodes) == 1
        assert nodes[0].lines == (3, 3)

    def test_invalid_syntax(self) -> None:
        """Ensure that invalid syntax raises an exception."""
        invalid_syntax = """\
class C:
    def __init__(self):
        self._x =
        self.test1 = "test"
"""
        analyzer = AstAnalyzer(invalid_syntax, settings=FixerSettings())
        with pytest.raises(AssertionError, match="Failed to parse source file AST"):
            analyzer.parse_from_ast()

    def test_handle_docstring_modifiers(self) -> None:
        """Test that docstring modifiers are handled correctly."""
        function_definitions = '''\
def test_function_1():
    """No modifier."""

def test_function_2():
    r"""Raw string."""

def test_function_3():
    u"""Unicode string."""

def test_function_4():
    R"""Raw string."""

def test_function_5():
    U"""Unicode string."""
'''
        analyzer = AstAnalyzer(function_definitions, settings=FixerSettings())
        nodes = [
            node
            for node in analyzer.parse_from_ast()
            if isinstance(node, FunctionDocstring)
        ]
        assert len(nodes) == 5
        assert nodes[0].modifier == ""
        assert nodes[1].modifier == "r"
        assert nodes[2].modifier == "u"
        assert nodes[3].modifier == "R"
        assert nodes[4].modifier == "U"

    def test_skip_private_methods(self) -> None:
        """Ensure that private methods are skipped when requested."""
        function_definitions = """\
class C:
    def func1(self):
        pass

    def _func2(self):
        pass
"""
        analyzer = AstAnalyzer(
            function_definitions, settings=FixerSettings(ignore_privates=True)
        )
        nodes = [
            node
            for node in analyzer.parse_from_ast()
            if isinstance(node, ClassDocstring)
        ]
        assert len(nodes) == 1
        assert len(nodes[0].methods) == 1
        assert nodes[0].methods[0] == "func1()"

    def test_calculate_function_length(self) -> None:
        """Test that nested function statement length is calculated correctly."""
        function_definition = '''\
def test_function():
    """My docstring, dont count"""
    if 1:
        print(a)
        print(b)
    else:
        for i in range(10):
            print(i)
    with test:
        try:
            something()
        except Exception:
            pass
    return None
'''
        func_node = ast.parse(function_definition).body[0]
        analyzer = AstAnalyzer(function_definition, settings=FixerSettings())
        func_docstring = analyzer.handle_function(func_node)
        assert func_docstring.length == 11


class TestAstUnparse:
    """Test ast_unparse function."""

    def test_none_input(self) -> None:
        """None input returns None."""
        assert ast_unparse(None) is None

    def test_none_input_with_strip(self) -> None:
        """None input returns None even with strip_string_quotes."""
        assert ast_unparse(None, strip_string_quotes=True) is None

    def test_name_node(self) -> None:
        """Regular Name node is unparsed normally."""
        node = ast.parse("MyClass", mode="eval").body
        assert ast_unparse(node) == "MyClass"

    def test_string_constant_without_strip(self) -> None:
        """String constant without strip keeps quotes."""
        node = ast.parse("'MyClass'", mode="eval").body
        assert ast_unparse(node) == "'MyClass'"

    def test_string_constant_with_strip(self) -> None:
        """String constant with strip returns unquoted value."""
        node = ast.parse("'MyClass'", mode="eval").body
        assert ast_unparse(node, strip_string_quotes=True) == "MyClass"

    def test_complex_forward_ref_with_strip(self) -> None:
        """Complex forward ref like 'list[MyClass]' is stripped correctly."""
        node = ast.parse("'list[MyClass]'", mode="eval").body
        assert ast_unparse(node, strip_string_quotes=True) == "list[MyClass]"

    def test_int_constant_with_strip(self) -> None:
        """Non-string constant is not affected by strip."""
        node = ast.parse("42", mode="eval").body
        assert ast_unparse(node, strip_string_quotes=True) == "42"

    def test_subscript_node_with_strip(self) -> None:
        """Complex type like list[int] is not affected by strip."""
        node = ast.parse("list[int]", mode="eval").body
        assert ast_unparse(node, strip_string_quotes=True) == "list[int]"
