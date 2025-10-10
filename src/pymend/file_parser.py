"""Module for parsing input file and walking ast."""

import ast
import re
from collections.abc import Iterator
from typing import TypeGuard, overload

from .const import DEFAULT_EXCEPTION
from .docstring_info import (
    TRY_NODES,
    BodyTypes,
    ClassDocstring,
    DocstringInfo,
    ElementDocstring,
    FixerSettings,
    FunctionBody,
    FunctionDocstring,
    FunctionSignature,
    ModuleDocstring,
    NodeOfInterest,
    Parameter,
    ReturnValue,
)

__author__ = "J-E. Nitschke"
__copyright__ = "Copyright 2023-2024"
__licence__ = "MIT"
__version__ = "1.1.0"
__maintainer__ = "J-E. Nitschke"


@overload
def ast_unparse(node: None) -> None: ...


@overload
def ast_unparse(node: ast.AST) -> str: ...


def ast_unparse(node: ast.AST | None) -> str | None:
    """Convert the AST node to source code as a string.

    Parameters
    ----------
    node : ast.AST | None
        Node to unparse.

    Returns
    -------
    str | None
        `None` if `node` was `None`.
        Otherwise the unparsed node.
    """
    if node is None:
        return None
    return ast.unparse(node)


class FunctionNodeVisitor:  # pylint: disable=too-few-public-methods
    """Visit all subnodes of the function."""

    def __init__(self, start_node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        """Visit all subnodes of the function.

        Collect returns, yields and raises.
        Discard returns and yields from nested functions.

        Parameters
        ----------
        start_node : ast.FunctionDef | ast.AsyncFunctionDef
            Node to start traversal from.
        """
        self.start_node = start_node
        self.returns: set[tuple[str, ...]] = set()
        self.returns_value = False
        self.yields: set[tuple[str, ...]] = set()
        self.yields_value = False
        self.raises: list[str] = []

        self._inside_nested_function = 0
        self._visit(start_node)

    def _visit(self, node: ast.AST) -> None:
        """Visit a node."""
        method = "_visit_" + node.__class__.__name__
        visitor = getattr(self, method, self._generic_visit)
        visitor(node)

    def _generic_visit(self, node: ast.AST) -> None:
        """Call if no explicit visitor function exists for a node."""
        for _, value in ast.iter_fields(node):
            if isinstance(value, list):
                for item in value:  # pyright: ignore[reportUnknownVariableType]
                    if isinstance(item, ast.AST):
                        self._visit(item)
            elif isinstance(value, ast.AST):
                self._visit(value)

    def _visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802  # pylint: disable=invalid-name
        """Keep track of nested function depth.

        Parameters
        ----------
        node : ast.FunctionDef
            Current node in the traversal.
        """
        self._inside_nested_function += 0 if node is self.start_node else 1
        self._generic_visit(node)
        self._inside_nested_function -= 0 if node is self.start_node else 1

    def _visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802  # pylint: disable=invalid-name
        """Keep track of nested function depth.

        Parameters
        ----------
        node : ast.AsyncFunctionDef
            Current node in the traversal.
        """
        self._inside_nested_function += 0 if node is self.start_node else 1
        self._generic_visit(node)
        self._inside_nested_function -= 0 if node is self.start_node else 1

    def _visit_Return(self, node: ast.Return) -> None:  # noqa: N802  # pylint: disable=invalid-name
        """Do not process returns from nested functions.

        Parameters
        ----------
        node : ast.Return
            Current node in the traversal.
        """
        if not self._inside_nested_function and node.value is not None:
            self.returns_value = True
            if isinstance(node.value, ast.Tuple) and all(
                isinstance(value, ast.Name) for value in node.value.elts
            ):
                self.returns.add(AstAnalyzer.get_ids_from_returns(node.value.elts))
        self._generic_visit(node)

    def _visit_Yield(self, node: ast.Yield) -> None:  # noqa: N802  # pylint: disable=invalid-name
        """Do not process yields from nested functions.

        Parameters
        ----------
        node : ast.Yield
            Current node in the traversal.
        """
        if not self._inside_nested_function:
            self.yields_value = True
            if isinstance(node.value, ast.Tuple) and all(
                isinstance(value, ast.Name) for value in node.value.elts
            ):
                self.yields.add(AstAnalyzer.get_ids_from_returns(node.value.elts))
        self._generic_visit(node)

    def _visit_YieldFrom(self, node: ast.YieldFrom) -> None:  # noqa: N802  # pylint: disable=invalid-name
        """Do not process yields from nested functions.

        Parameters
        ----------
        node : ast.YieldFrom
            Current node in the traversal.
        """
        if not self._inside_nested_function:
            self.yields_value = True
        self._generic_visit(node)

    def _visit_Raise(self, node: ast.Raise) -> None:  # noqa: N802  # pylint: disable=invalid-name
        """Do process raises from nested functions.

        Parameters
        ----------
        node : ast.Raise
            Current node in the traversal.
        """
        pascal_case_regex = r"^(?:[A-Z][a-z]+)+$"
        if not node.exc:
            self.raises.append(DEFAULT_EXCEPTION)
        elif isinstance(node.exc, ast.Name) and re.match(
            pascal_case_regex, node.exc.id
        ):
            self.raises.append(node.exc.id)
        elif (
            isinstance(node.exc, ast.Call)
            and isinstance(node.exc.func, ast.Name)
            and re.match(pascal_case_regex, node.exc.func.id)
        ):
            self.raises.append(node.exc.func.id)
        else:
            self.raises.append(DEFAULT_EXCEPTION)
        self._generic_visit(node)


class AstAnalyzer:
    """Walk ast and extract module, class and function information."""

    def __init__(self, file_content: str, *, settings: FixerSettings) -> None:
        """Initialize the Analyzer with the file contents.

        The only reason this is a class is to have the raw
        file_contents available at any point of the analysis to double check
        something. Currently used for the module docstring and docstring
        modifiers.

        Parameters
        ----------
        file_content : str
            File contents to store.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        self.file_content = file_content
        self.settings = settings

    @staticmethod
    def func_decorators(
        node: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> Iterator[str]:
        """Get the names of the decorators of a function node."""
        for name in node.decorator_list:
            if isinstance(name, ast.Name):
                yield name.id

    def parse_from_ast(
        self,
    ) -> list[ElementDocstring]:
        """Walk AST of the input file extract info about module, classes and functions.

        For the module and classes, the raw docstring
        and its line numbers are extracted.

        For functions the raw docstring and its line numbers are extracted.
        Additionally the signature is parsed for parameters and return value.

        Returns
        -------
        list[ElementDocstring]
            List of information about module, classes and functions.

        Raises
        ------
        AssertionError
            If the source file content could not be parsed into an ast.
        """
        nodes_of_interest: list[ElementDocstring] = []
        try:
            file_ast = ast.parse(self.file_content)
        except Exception as exc:
            msg = f"Failed to parse source file AST: {exc}\n"
            raise AssertionError(msg) from exc
        for node in ast.walk(file_ast):
            if isinstance(node, ast.Module):
                nodes_of_interest.append(self.handle_module(node))
            elif isinstance(node, ast.ClassDef):
                if node.name in self.settings.ignored_classes:
                    continue
                nodes_of_interest.append(self.handle_class(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if (
                    any(
                        name in self.settings.ignored_decorators
                        for name in self.func_decorators(node)
                    )
                    or node.name in self.settings.ignored_functions
                ):
                    continue
                nodes_of_interest.append(self.handle_function(node))
        return nodes_of_interest

    def handle_module(self, module: ast.Module) -> ModuleDocstring:
        """Extract information about module.

        Parameters
        ----------
        module : ast.Module
            Node representing the full module.

        Returns
        -------
        ModuleDocstring
            Docstring representation for the module.
        """
        docstring_info = self.get_docstring_info(module)
        if docstring_info is None:
            docstring_line = self._get_docstring_line()
            return ModuleDocstring(
                "Module",
                docstring="",
                lines=(docstring_line, docstring_line),
                modifier="",
                issues=[],
                had_docstring=False,
            )
        return ModuleDocstring(
            name=docstring_info.name,
            docstring=docstring_info.docstring,
            lines=docstring_info.lines,
            modifier=docstring_info.modifier,
            issues=docstring_info.issues,
            had_docstring=docstring_info.had_docstring,
        )

    def handle_class(self, cls: ast.ClassDef) -> ClassDocstring:
        """Extract information about class docstring.

        Parameters
        ----------
        cls : ast.ClassDef
            Node representing a class definition.

        Returns
        -------
        ClassDocstring
            Docstring representation for a class.
        """
        docstring = self.handle_elem_docstring(cls)
        attributes, methods = self.handle_class_body(cls)
        return ClassDocstring(
            name=docstring.name,
            docstring=docstring.docstring,
            lines=docstring.lines,
            modifier=docstring.modifier,
            issues=docstring.issues,
            attributes=attributes,
            methods=methods,
            had_docstring=docstring.had_docstring,
        )

    def handle_function(
        self,
        func: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> FunctionDocstring:
        """Extract information from signature and docstring.

        Parameters
        ----------
        func : ast.FunctionDef | ast.AsyncFunctionDef
            Node representing a function definition.

        Returns
        -------
        FunctionDocstring
            Docstring representation of a function.
        """
        docstring = self.handle_elem_docstring(func)
        signature = self.handle_function_signature(func)
        body = self.handle_function_body(func)
        # Minus one because the function counts the passed node itself
        # Which is correct for each nested node but not the main one.
        length = self._get_block_length(func) - 1
        return FunctionDocstring(
            name=docstring.name,
            docstring=docstring.docstring,
            lines=docstring.lines,
            modifier=docstring.modifier,
            issues=docstring.issues,
            signature=signature,
            body=body,
            length=length,
            had_docstring=docstring.had_docstring,
        )

    def handle_elem_docstring(
        self,
        elem: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
    ) -> DocstringInfo:
        """Extract information about the docstring of the function.

        Parameters
        ----------
        elem : ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
            Element representing a function or class definition.

        Returns
        -------
        DocstringInfo
            Return general information about the docstring of the element.

        Raises
        ------
        ValueError
            If the element did not have a body at all. This should not happen
            for valid functions or classes.
        ValueError
            If the indent of the function body is not
            one level deeper than the definition.
        """
        docstring_info = self.get_docstring_info(elem)
        if docstring_info is None:
            if not elem.body:
                msg = "Function body was unexpectedly completely empty."
                raise ValueError(msg)
            body_elem = elem.body[0]
            # Ideally we would use one line after the end of the actual function
            # definition. But this does not exist. So we need to use the body.
            # However that can start at the same line as the function definition.
            # In that case we cant place the docstring between definition and body.
            # The col offsets are unlikely to match so try to detect this with a
            # good error message.
            if body_elem.col_offset != (elem.col_offset + self.settings.indent):
                msg = (
                    "Function body did not start one indentation level"
                    " deeper than the function body. Can not properly place docstring."
                )
                raise ValueError(msg)
            lineno = body_elem.lineno
            if isinstance(
                body_elem, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                lineno -= len(body_elem.decorator_list)
            lines = (lineno, lineno)
            return DocstringInfo(
                name=elem.name,
                docstring="",
                lines=lines,
                modifier="",
                issues=[],
                had_docstring=False,
            )
        return docstring_info

    def get_docstring_info(self, node: NodeOfInterest) -> DocstringInfo | None:
        """Get docstring and line number if available.

        Parameters
        ----------
        node : NodeOfInterest
            Get general information about the docstring of any node
            if interest.

        Returns
        -------
        DocstringInfo | None
            Information about the docstring if the element contains one.
            Or `None` if there was no docstring at all.

        Raises
        ------
        ValueError
            If the first element of the body is not a docstring after
            `ast.get_docstring()` returned one.
        """
        if ast.get_docstring(node):
            if not (
                node.body
                and isinstance(first_element := node.body[0], ast.Expr)
                and isinstance(docnode := first_element.value, ast.Constant)
                and isinstance(docnode.value, str)
            ):
                msg = (
                    "Expected first entry in body to be the "
                    "docstring, but found nothing or something else."
                )
                raise ValueError(msg)
            modifier = self._get_modifier(
                self.file_content.splitlines()[docnode.lineno - 1]
            )
            return DocstringInfo(
                # Can not use DefinitionNodes in isinstance checks before 3.10
                name=(
                    node.name
                    if isinstance(
                        node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                    )
                    else "Module"
                ),
                docstring=str(docnode.value),
                lines=(docnode.lineno, docnode.end_lineno),
                modifier=modifier,
                issues=[],
                had_docstring=True,
            )
        return None

    def _get_modifier(self, line: str) -> str:
        """Get the string modifier from the start of a docstring.

        Parameters
        ----------
        line : str
            Line to check

        Returns
        -------
        str
            Modifier of the string.
        """
        line = line.strip()
        delimiters = ['"""', "'''"]
        modifiers = ["r", "u"]
        if not line:
            return ""
        if line[:3] in delimiters:
            return ""
        if line[0].lower() in modifiers and line[1:4] in delimiters:
            return line[0]
        return ""

    def _get_docstring_line(self) -> int:
        """Get the line where the module docstring should start.

        Returns
        -------
        int
            Starting line (starts at 1) of the docstring.
        """
        shebang_encoding_lines = 2
        lines_of_interest = self.file_content.splitlines()[:shebang_encoding_lines]
        if not lines_of_interest:
            return 1
        for index, line in enumerate(lines_of_interest):
            if not self.is_shebang_or_pragma(line):
                # List indices start at 0 but file lines are counted from 1
                return index + 1
        return shebang_encoding_lines + 1

    def _has_body(self, node: ast.AST) -> TypeGuard[BodyTypes]:
        """Check that the node is one of those that have a body."""
        return isinstance(node, BodyTypes) and hasattr(node, "body")

    def _get_block_length(self, node: ast.AST) -> int:
        """Get the number of statements in a block.

        Recursively count the number of statements in a blocks body.

        Parameters
        ----------
        node : ast.AST
            Node representing to count the number of statements for.

        Returns
        -------
        int
            Total number of (nested) statements in the block.
        """
        length = 1
        if self._has_body(node) and node.body:
            length += sum(self._get_block_length(child) for child in node.body)
        # Decorators add complexity, so lets count them for now
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            length += len(node.decorator_list)
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.While, ast.If, *TRY_NODES)):
            length += sum(self._get_block_length(child) for child in node.orelse)
            if isinstance(node, TRY_NODES):
                length += sum(self._get_block_length(child) for child in node.finalbody)
                length += sum(self._get_block_length(child) for child in node.handlers)
        elif isinstance(node, ast.Match):
            # Each case counts itself + its body.
            # This is intended for now as compared to if/else there is a lot
            # of logic actually still happening in the case matching.
            length += sum(self._get_block_length(child) for child in node.cases)

        # We do not want to count the docstring
        if (
            length
            and isinstance(
                node,
                (ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef, ast.Module),
            )
            and ast.get_docstring(node)
        ):
            length -= 1
        return length

    def handle_class_body(self, cls: ast.ClassDef) -> tuple[list[Parameter], list[str]]:
        """Extract attributes and methods from class body.

        Will walk the AST of the ClassDef node and add each function encountered
        as a method.

        If the `__init__` method is encountered walk its body for attribute
        definitions.

        Parameters
        ----------
        cls : ast.ClassDef
            Node representing a class definition.

        Returns
        -------
        attributes : list[Parameter]
            List of the parameters that make up the classes attributes.
        methods : list[str]
            List of the method names in the class.
        """
        attributes: list[Parameter] = []
        methods: list[str] = []
        for node in cls.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            # Extract attributes from init method.
            if node.name == "__init__":
                attributes.extend(self._get_attributes_from_init(node))
            # Skip dunder methods for method extraction
            if node.name.startswith("__") and node.name.endswith("__"):
                continue
            # Optionally skip private methods.
            if self.settings.ignore_privates and node.name.startswith("_"):
                continue
            # Handle properties as attributes
            if "property" in self.func_decorators(node):
                return_value = self.get_return_value_sig(node)
                attributes.append(Parameter(node.name, return_value.type_name, None))
            # Handle normal methods except for those with some specific decorators
            # Like statismethod, classmethod, property or getters/setters.
            elif not self._has_excluding_decorator(node):
                methods.append(self._get_method_signature(node))
            # Exclude some like staticmethods and properties

        # Remove duplicates from attributes while maintaining order
        return list(Parameter.uniquefy(attributes)), methods

    def handle_function_signature(
        self,
        func: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> FunctionSignature:
        """Extract information about the signature of the function.

        Parameters
        ----------
        func : ast.FunctionDef | ast.AsyncFunctionDef
            Node representing a function definition

        Returns
        -------
        FunctionSignature
            Information extracted from the function signature
        """
        parameters = self.get_parameters_sig(func)
        if parameters and (
            parameters[0].arg_name == "self"
            or (
                parameters[0].arg_name == "cls"
                and "classmethod" in self.func_decorators(func)
            )
        ):
            parameters.pop(0)
        return_value = self.get_return_value_sig(func)
        return FunctionSignature(parameters, return_value)

    def handle_function_body(
        self,
        func: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> FunctionBody:
        """Check the function body for yields, raises and value returns.

        Parameters
        ----------
        func : ast.FunctionDef | ast.AsyncFunctionDef
            Node representing a function definition

        Returns
        -------
        FunctionBody
            Information extracted from the function body.
        """
        visitor = FunctionNodeVisitor(func)
        return FunctionBody(
            returns_value=visitor.returns_value,
            returns=visitor.returns,
            yields_value=visitor.yields_value,
            yields=visitor.yields,
            raises=visitor.raises,
        )

    def get_return_value_sig(
        self, func: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> ReturnValue:
        """Get information about return value from signature.

        Parameters
        ----------
        func : ast.FunctionDef | ast.AsyncFunctionDef
            Node representing a function definition

        Returns
        -------
        ReturnValue
            Return information extracted from the function signature.
        """
        return ReturnValue(type_name=ast_unparse(func.returns))

    def get_parameters_sig(
        self, func: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> list[Parameter]:
        """Get information about function parameters.

        Parameters
        ----------
        func : ast.FunctionDef | ast.AsyncFunctionDef
            Node representing a function definition

        Returns
        -------
        list[Parameter]
            Parameter information from the function signature.
        """
        arguments: list[Parameter] = []
        pos_defaults = self.get_padded_args_defaults(func)

        pos_only_args = [
            Parameter(arg.arg, ast_unparse(arg.annotation), None)
            for arg in func.args.posonlyargs
        ]
        arguments += pos_only_args
        general_args = [
            Parameter(arg.arg, ast_unparse(arg.annotation), default)
            for arg, default in zip(func.args.args, pos_defaults, strict=False)
        ]
        arguments += general_args
        if vararg := func.args.vararg:
            arguments.append(
                Parameter(f"*{vararg.arg}", ast_unparse(vararg.annotation), None)
            )
        kw_only_args = [
            Parameter(
                arg.arg,
                ast_unparse(arg.annotation),
                ast_unparse(default),
            )
            for arg, default in zip(
                func.args.kwonlyargs, func.args.kw_defaults, strict=False
            )
        ]
        arguments += kw_only_args
        if kwarg := func.args.kwarg:
            arguments.append(
                Parameter(f"**{kwarg.arg}", ast_unparse(kwarg.annotation), None)
            )
        # Filter out unused arguments.
        return (
            [
                argument
                for argument in arguments
                if not argument.arg_name.startswith("_")
            ]
            if self.settings.ignore_unused_arguments
            else arguments
        )

    @staticmethod
    def is_shebang_or_pragma(line: str) -> bool:
        """Check if a given line contains encoding or shebang.

        Parameters
        ----------
        line : str
            Line to check

        Returns
        -------
        bool
            Whether the given line contains encoding or shebang
        """
        shebang_regex = r"^#!(.*)"
        if re.search(shebang_regex, line) is not None:
            return True
        pragma_regex = r"^#.*coding[=:]\s*([-\w.]+)"
        return re.search(pragma_regex, line) is not None

    def get_padded_args_defaults(
        self,
        func: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> list[str | None]:
        """Left-Pad the general args defaults to the length of the args.

        Parameters
        ----------
        func : ast.FunctionDef | ast.AsyncFunctionDef
            Node representing a function definition

        Returns
        -------
        list[str | None]
            Left padded (with `None`) list of function arguments.
        """
        pos_defaults = [ast_unparse(default) for default in func.args.defaults]
        return [None] * (len(func.args.args) - len(pos_defaults)) + pos_defaults

    def _has_excluding_decorator(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> bool:
        """Exclude function with some decorators.

        Currently excluded:
            staticmethod
            classmethod
            property (and related)

        Parameters
        ----------
        node : ast.FunctionDef | ast.AsyncFunctionDef
            Node representing a function definition

        Returns
        -------
        bool
            Whether the function as any decorators that exclude it from
            being recognized as a standard method.
        """
        decorators = node.decorator_list
        excluded_decorators = {"staticmethod", "classmethod", "property"}
        for decorator in decorators:
            if isinstance(decorator, ast.Name) and decorator.id in excluded_decorators:
                return True
            # Handle property related decorators like in
            # @x.setter
            # def x(self, value):
            #     self._x = value  # noqa: ERA001

            # @x.deleter
            # def x(self):
            #     del self._x
            if (
                isinstance(decorator, ast.Attribute)
                and isinstance(decorator.value, ast.Name)
                and decorator.value.id == node.name
            ):
                return True
        return False

    def _check_if_node_is_self_attributes(
        self, node: ast.expr
    ) -> TypeGuard[ast.Attribute]:
        """Check whether the node represents a public attribute of self (self.abc).

        Parameters
        ----------
        node : ast.expr
            Node representing the expression to be checked.

        Returns
        -------
        TypeGuard[ast.Attribute]
            True if the node represents a public attribute of self.
        """
        return (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
            and not (self.settings.ignore_privates and node.attr.startswith("_"))
        )

    def _check_and_handle_assign_node(
        self, target: ast.expr, attributes: list[Parameter]
    ) -> None:
        """Check if the assignment node contains assignments to self.X.

        Add it to the list of attributes if that is the case.

        Parameters
        ----------
        target : ast.expr
            Node representing an assignment
        attributes : list[Parameter]
            List of attributes the node attribute should be added to.
        """
        if isinstance(target, (ast.Tuple, ast.List)):
            for node in target.elts:
                if self._check_if_node_is_self_attributes(node):
                    attributes.append(Parameter(node.attr, "_type_", None))
        elif self._check_if_node_is_self_attributes(target):
            attributes.append(Parameter(target.attr, "_type_", None))

    def _get_attributes_from_init(
        self, init: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> list[Parameter]:
        """Iterate over body and grab every assignment `self.abc = XYZ`.

        Parameters
        ----------
        init : ast.FunctionDef | ast.AsyncFunctionDef
            Init function node to extract attributes from.

        Returns
        -------
        list[Parameter]
            List of attributes extracted from the init function.
        """
        attributes: list[Parameter] = []
        for node in init.body:
            if isinstance(node, ast.Assign):
                # Targets is a list in case of multiple assignment
                # a = b = 3  # noqa: ERA001
                for target in node.targets:
                    self._check_and_handle_assign_node(target, attributes)
            # Also handle annotated assignments
            # c: int = "Test"  # noqa: ERA001
            elif isinstance(node, ast.AnnAssign):
                self._check_and_handle_assign_node(node.target, attributes)
        return attributes

    def _get_method_signature(
        self, func: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> str:
        """Remove self from signature and return the unparsed string.

        Parameters
        ----------
        func : ast.FunctionDef | ast.AsyncFunctionDef
            Node representing a function definition.

        Returns
        -------
        str
            String of the method signature with `self` removed.
        """
        arguments = func.args
        if arguments.posonlyargs:
            arguments.posonlyargs = [
                arg for arg in arguments.posonlyargs if arg.arg != "self"
            ]
        elif arguments.args:
            arguments.args = [arg for arg in arguments.args if arg.arg != "self"]
        return f"{func.name}({ast.unparse(arguments)})"

    @staticmethod
    def get_ids_from_returns(values: list[ast.expr]) -> tuple[str, ...]:
        """Get the ids/names for all the expressions in the list.

        Parameters
        ----------
        values : list[ast.expr]
            List of expressions to extract the ids from.

        Returns
        -------
        tuple[str, ...]
            Tuple of ids of the original expressions.
        """
        return tuple(
            value.id
            for value in values
            # Needed again for type checker
            if isinstance(value, ast.Name)
        )
