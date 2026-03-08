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

        attributes, methods, _issues = analyzer.handle_class_body(class_node)

        expected_attributes = [
            Parameter("test1", None, None),
            Parameter("test2", "Optional[int]", None),
            Parameter("test3", None, None),
            Parameter("test4", None, None),
            Parameter("test5", None, None),
            Parameter("test6", None, None),
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

    # ---- dataclass / BaseModel attribute extraction ----

    def test_handle_class_body_dataclass(self) -> None:
        """Dataclass class-level annotations are extracted as attributes."""
        src = """\
from dataclasses import dataclass

@dataclass
class Foo:
    x: int
    y: str = "hello"
"""
        class_node = ast.parse(src).body[1]
        analyzer = AstAnalyzer(src, settings=FixerSettings())
        attributes, methods, _issues = analyzer.handle_class_body(class_node)
        assert attributes == [
            Parameter("x", "int", None),
            Parameter("y", "str", None),
        ]
        assert methods == []

    def test_handle_class_body_dataclass_frozen(self) -> None:
        """@dataclass(frozen=True) is also detected."""
        src = """\
from dataclasses import dataclass

@dataclass(frozen=True)
class Foo:
    x: int
"""
        class_node = ast.parse(src).body[1]
        analyzer = AstAnalyzer(src, settings=FixerSettings())
        attributes, _methods, _issues = analyzer.handle_class_body(class_node)
        assert attributes == [Parameter("x", "int", None)]

    def test_handle_class_body_basemodel(self) -> None:
        """BaseModel subclass annotations are extracted as attributes."""
        src = """\
class Foo(BaseModel):
    x: int
    y: str = "hello"
"""
        class_node = ast.parse(src).body[0]
        analyzer = AstAnalyzer(src, settings=FixerSettings())
        attributes, methods, _issues = analyzer.handle_class_body(class_node)
        assert attributes == [
            Parameter("x", "int", None),
            Parameter("y", "str", None),
        ]
        assert methods == []

    def test_handle_class_body_basemodel_dotted(self) -> None:
        """module.BaseModel is also detected."""
        src = """\
class Foo(pydantic.BaseModel):
    x: int
"""
        class_node = ast.parse(src).body[0]
        analyzer = AstAnalyzer(src, settings=FixerSettings())
        attributes, _methods, _issues = analyzer.handle_class_body(class_node)
        assert attributes == [Parameter("x", "int", None)]

    def test_handle_class_body_dataclass_with_init(self) -> None:
        """Class-vars from dataclass are merged with init-only attrs."""
        src = """\
from dataclasses import dataclass

@dataclass
class Foo:
    x: int
    def __init__(self):
        self.z = "extra"
"""
        class_node = ast.parse(src).body[1]
        analyzer = AstAnalyzer(src, settings=FixerSettings())
        attributes, _methods, _issues = analyzer.handle_class_body(class_node)
        assert attributes == [
            Parameter("x", "int", None),
            Parameter("z", None, None),
        ]

    def test_classvar_skipped(self) -> None:
        """ClassVar annotations are not extracted as attributes."""
        src = """\
from dataclasses import dataclass
from typing import ClassVar

@dataclass
class Foo:
    x: int
    y: ClassVar[str] = "shared"
"""
        class_node = ast.parse(src).body[2]
        analyzer = AstAnalyzer(src, settings=FixerSettings())
        attributes, _methods, _issues = analyzer.handle_class_body(class_node)
        assert attributes == [Parameter("x", "int", None)]

    # ---- __init__ type extraction ----

    def test_init_type_extraction_annotation(self) -> None:
        """Annotated self assignments extract type from annotation."""
        src = """\
class Foo:
    def __init__(self):
        self.x: int = 5
"""
        class_node = ast.parse(src).body[0]
        analyzer = AstAnalyzer(src, settings=FixerSettings())
        attributes, _methods, _issues = analyzer.handle_class_body(class_node)
        assert attributes == [Parameter("x", "int", None)]

    def test_init_type_extraction_param_mapping(self) -> None:
        """self.x = x infers type from __init__ param annotation."""
        src = """\
class Foo:
    def __init__(self, x: int, y: str):
        self.x = x
        self.y = y
"""
        class_node = ast.parse(src).body[0]
        analyzer = AstAnalyzer(src, settings=FixerSettings())
        attributes, _methods, _issues = analyzer.handle_class_body(class_node)
        assert attributes == [
            Parameter("x", "int", None),
            Parameter("y", "str", None),
        ]

    def test_init_type_extraction_no_type(self) -> None:
        """Untyped self assignments produce None type."""
        src = """\
class Foo:
    def __init__(self, x):
        self.x = x
        self.y = 42
"""
        class_node = ast.parse(src).body[0]
        analyzer = AstAnalyzer(src, settings=FixerSettings())
        attributes, _methods, _issues = analyzer.handle_class_body(class_node)
        assert attributes == [
            Parameter("x", None, None),
            Parameter("y", None, None),
        ]

    # ---- is_attribute_class detection ----

    def test_non_attribute_class_ignored(self) -> None:
        """Regular class does not extract class-level annotations."""
        src = """\
class Foo:
    x: int
    y: str = "hello"
"""
        class_node = ast.parse(src).body[0]
        analyzer = AstAnalyzer(src, settings=FixerSettings())
        attributes, _methods, _issues = analyzer.handle_class_body(class_node)
        # No __init__, no property, no dataclass/BaseModel → no attributes
        assert attributes == []

    def test_custom_attribute_class_decorator(self) -> None:
        """Custom attribute_class_decorators setting is respected."""
        src = """\
@attrs
class Foo:
    x: int
"""
        class_node = ast.parse(src).body[0]
        settings = FixerSettings(attribute_class_decorators=["attrs"])
        analyzer = AstAnalyzer(src, settings=settings)
        attributes, _methods, _issues = analyzer.handle_class_body(class_node)
        assert attributes == [Parameter("x", "int", None)]

    def test_custom_attribute_base_class(self) -> None:
        """Custom attribute_base_classes setting is respected."""
        src = """\
class Foo(MyBase):
    x: int
"""
        class_node = ast.parse(src).body[0]
        settings = FixerSettings(attribute_base_classes=["MyBase"])
        analyzer = AstAnalyzer(src, settings=settings)
        attributes, _methods, _issues = analyzer.handle_class_body(class_node)
        assert attributes == [Parameter("x", "int", None)]

    # ---- property decorator configurability ----

    def test_property_decorators_configurable(self) -> None:
        """Custom property_decorators are used for attribute extraction."""
        src = """\
class Foo:
    @cached_property
    def x(self) -> int:
        return 42
"""
        class_node = ast.parse(src).body[0]
        settings = FixerSettings(property_decorators=["property", "cached_property"])
        analyzer = AstAnalyzer(src, settings=settings)
        attributes, methods, _issues = analyzer.handle_class_body(class_node)
        assert attributes == [Parameter("x", "int", None)]
        assert methods == []


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
