"""Module for defining commonly used types."""

import ast
import re
import sys
from collections import Counter
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import TypeAlias

from typing_extensions import override

import pymend.docstring_parser as dsp

from .const import (
    ARG_TYPE_SET,
    ATTRIBUTE_TYPE_SET,
    DEFAULT_DESCRIPTION,
    DEFAULT_EXCEPTION,
    DEFAULT_SUMMARY,
    DEFAULT_TYPE,
    RETURN_TYPE_SET,
)

__author__ = "J-E. Nitschke"
__copyright__ = "Copyright 2023-2026"
__licence__ = "MIT"
__version__ = "3.1.0"
__maintainer__ = "J-E. Nitschke"


class ForceOption(Enum):
    """Three-valued option for type-hint enforcement.

    Attributes
    ----------
    FORCE : str
        Actively enforce the existence of type information.
    UNFORCE : str
        Actively enforce the lack of type information (strip).
    NOFORCE : str
        Don't enforce either way (preserve as-is).
    """

    FORCE = "force"
    UNFORCE = "unforce"
    NOFORCE = "noforce"


class RaisesForceMode(Enum):
    """Three-valued option for raises section enforcement.

    Attributes
    ----------
    OFF : str
        Don't enforce raises section.
    PER_TYPE : str
        Each exception type must be documented at least once.
    PER_SITE : str
        Each raise site must be documented (one entry per raise).
    """

    OFF = "off"
    PER_TYPE = "per-type"
    PER_SITE = "per-site"


def resolve_type_name(
    force_option: ForceOption,
    *,
    doc_type: str | None = None,
    improved_types: Sequence[str | None] = (),
    default: str = DEFAULT_TYPE,
) -> str | None:
    """Resolve the final type name based on the force option.

    ``doc_type`` is the type currently recorded in the docstring.
    ``improved_types`` is an optional sequence of candidate "better" types
    (e.g. from the function signature or class body).  In *FORCE* mode the
    best improved type wins over the docstring type; in *NOFORCE* mode
    improved types are only used to *correct* an already-present docstring
    type -- they are never used to fill in a missing one.

    Parameters
    ----------
    force_option : ForceOption
        The force option controlling type enforcement.
    doc_type : str | None
        The type currently present in the docstring.
        (Default value = None)
    improved_types : Sequence[str | None]
        Candidate replacement types in descending priority order.
        (Default value = ())
    default : str
        Fallback when forcing and no other type is available.
        (Default value = DEFAULT_TYPE)

    Returns
    -------
    str | None
        The resolved type name.
    """
    best_improved: str | None = next((t for t in improved_types if t), None)
    match force_option:
        case ForceOption.FORCE:
            return best_improved or doc_type or default
        case ForceOption.UNFORCE:
            return None
        case ForceOption.NOFORCE:
            if doc_type:
                return best_improved or doc_type
            return None


def new_entry_force_mode(force_mode: ForceOption) -> ForceOption:
    """Return the force mode to use when creating a brand-new docstring entry.

    NOFORCE means "preserve existing types as-is", but a brand-new entry has
    nothing to preserve, so we promote it to FORCE.
    FORCE and UNFORCE are used as-is.

    Parameters
    ----------
    force_mode : ForceOption
        The user's chosen force mode.

    Returns
    -------
    ForceOption
        The effective force mode for the new entry.
    """
    if force_mode == ForceOption.NOFORCE:
        return ForceOption.FORCE
    return force_mode


@dataclass(frozen=True)
class FixerSettings:  # pylint: disable=too-many-instance-attributes
    """Settings to influence which sections are required and when."""

    force_docstrings: bool = True
    force_params: bool = True
    force_return: bool = True
    force_raises: RaisesForceMode = RaisesForceMode.PER_SITE
    force_methods: bool = False
    force_attributes: bool = False
    force_params_min_n_params: int = 0
    force_meta_min_func_length: int = 0
    ignore_privates: bool = True
    ignore_unused_arguments: bool = True
    ignored_decorators: list[str] = field(default_factory=lambda: ["overload"])
    ignored_functions: list[str] = field(default_factory=lambda: ["main"])
    ignored_classes: list[str] = field(default_factory=list[str])
    force_defaults: bool = True
    force_return_type: ForceOption = ForceOption.FORCE
    force_arg_types: ForceOption = ForceOption.FORCE
    force_attribute_types: ForceOption = ForceOption.FORCE
    force_summary_period: bool = True
    force_summary_blank_line: bool = True
    indent: int = 4
    attribute_class_decorators: list[str] = field(default_factory=lambda: ["dataclass"])
    attribute_base_classes: list[str] = field(default_factory=lambda: ["BaseModel"])
    property_decorators: list[str] = field(default_factory=lambda: ["property"])
    additional_excluded_decorators: list[str] = field(
        default_factory=lambda: ["staticmethod", "classmethod"]
    )


@dataclass
class DocstringInfo:
    """Wrapper around raw docstring."""

    name: str
    docstring: str
    lines: tuple[int, int | None]
    modifier: str
    issues: list[str]
    had_docstring: bool

    def output_docstring(
        self,
        *,
        settings: FixerSettings,
        output_style: dsp.DocstringStyle = dsp.DocstringStyle.NUMPYDOC,
        input_style: dsp.DocstringStyle = dsp.DocstringStyle.AUTO,
    ) -> str:
        """Parse and fix input docstrings, then compose output docstring.

        Parameters
        ----------
        settings : FixerSettings
            Settings for what to fix and when.
        output_style : dsp.DocstringStyle
            Output style to use for the docstring.
            (Default value = dsp.DocstringStyle.NUMPYDOC)
        input_style : dsp.DocstringStyle
            Input style to assume for the docstring.
            (Default value = dsp.DocstringStyle.AUTO)

        Returns
        -------
        str
            String representing the updated docstring.

        Raises
        ------
        AssertionError
            If the docstring could not be parsed.
        """
        self._escape_triple_quotes()
        try:
            parsed = dsp.parse(self.docstring, style=input_style)
        except Exception as e:
            msg = f"Failed to parse docstring for `{self.name}` with error: `{e}`"
            raise AssertionError(msg) from e
        if settings.force_docstrings or self.docstring:
            self._fix_docstring(parsed, settings)
            self._fix_blank_lines(parsed, settings)
            return dsp.compose(parsed, style=output_style)
        return ""

    def report_issues(self) -> tuple[int, str]:
        """Report all issues that were found in this docstring.

        Returns
        -------
        tuple[int, str]
            The number of issues found and a string representing a summary
            of those.
        """
        if not self.issues:
            return 0, ""
        return len(self.issues), f"{'-' * 50}\n{self.name}:\n" + "\n".join(self.issues)

    def _escape_triple_quotes(self) -> None:
        r"""Escape \"\"\" in the docstring."""
        if '"""' in self.docstring:
            self.issues.append("Unescaped triple quotes found.")
            self.docstring = self.docstring.replace('"""', r"\"\"\"")

    def _fix_docstring(self, docstring: dsp.Docstring, settings: FixerSettings) -> None:
        """Fix docstrings.

        Default are to add missing dots, blank lines and give defaults for
        descriptions and types.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to fix.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        self._fix_backslashes()
        self._fix_short_description(docstring, settings)
        self._fix_descriptions(docstring)

    def _fix_backslashes(self) -> None:
        """If there is any backslash in the docstring set it as raw."""
        if "\\" in self.docstring and "r" not in self.modifier:
            self.issues.append("Missing 'r' modifier.")
            self.modifier = "r" + self.modifier

    def _fix_short_description(
        self, docstring: dsp.Docstring, settings: FixerSettings
    ) -> None:
        """Set default summary.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to set the default summary for.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        cleaned_short_description = (
            docstring.short_description.strip() if docstring.short_description else ""
        )
        if (
            not cleaned_short_description
            or cleaned_short_description == DEFAULT_SUMMARY
        ):
            self.issues.append("Missing short description.")
        docstring.short_description = cleaned_short_description or DEFAULT_SUMMARY
        if settings.force_summary_period and not docstring.short_description.endswith(
            "."
        ):
            self.issues.append("Short description missing '.' at the end.")
            docstring.short_description = f"{docstring.short_description.rstrip()}."

    def _fix_blank_lines(
        self, docstring: dsp.Docstring, settings: FixerSettings
    ) -> None:
        """Set blank lines after short and long description.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to fix the blank lines for.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        # For parsing a blank line is associated with the description.
        if settings.force_summary_blank_line:
            if (
                docstring.blank_after_short_description
                != bool(docstring.long_description or docstring.meta)
                and self.docstring
            ):
                self.issues.append("Incorrect blank line after short description.")
            docstring.blank_after_short_description = bool(
                docstring.long_description or docstring.meta
            )
        if docstring.long_description:
            if (
                docstring.blank_after_long_description != bool(docstring.meta)
                and self.docstring
            ):
                self.issues.append("Incorrect blank line after long description.")
            docstring.blank_after_long_description = bool(docstring.meta)
        else:
            if docstring.blank_after_long_description and self.docstring:
                self.issues.append("Incorrect blank line after long description.")
            docstring.blank_after_long_description = False

    def _fix_descriptions(self, docstring: dsp.Docstring) -> None:
        """Everything should have a description.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring whose descriptions need fixing.
        """
        for ele in docstring.meta:
            # Description works a bit different for examples.
            if isinstance(ele, dsp.DocstringExample):
                continue
            if not ele.description or DEFAULT_DESCRIPTION in ele.description:
                self.issues.append(
                    f"{ele.args}: Missing or default description `{ele.description}`."
                )
            ele.description = ele.description or DEFAULT_DESCRIPTION


@dataclass
class ModuleDocstring(DocstringInfo):
    """Information about a module."""


@dataclass
class Parameter:
    """Info for parameter from signature."""

    arg_name: str
    type_name: str | None = None
    default: str | None = None

    def custom_hash(self) -> int:
        """Implement custom has function for uniquefying.

        Returns
        -------
        int
            Hash value of the instance.
        """
        return hash((self.arg_name, self.type_name, self.default))

    @staticmethod
    def uniquefy(lst: Iterable["Parameter"]) -> Iterator["Parameter"]:
        """Remove duplicates while keeping order.

        Parameters
        ----------
        lst : Iterable['Parameter']
            Iterable of parameters that should be uniqueified.

        Yields
        ------
        'Parameter'
            Uniqueified parameters.
        """
        seen: set[int] = set()
        for item in lst:
            if (itemhash := item.custom_hash()) not in seen:
                seen.add(itemhash)
                yield item


@dataclass
class ClassDocstring(DocstringInfo):
    """Information about a module."""

    attributes: list[Parameter]
    methods: list[str]

    @override
    def _fix_docstring(self, docstring: dsp.Docstring, settings: FixerSettings) -> None:
        """Fix docstrings.

        Additionally adjust attributes and methods from body.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to fix.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        super()._fix_docstring(docstring, settings)
        self._adjust_attributes(docstring, settings)
        self._adjust_methods(docstring, settings)

    def _adjust_attributes(
        self, docstring: dsp.Docstring, settings: FixerSettings
    ) -> None:
        """Fix types for existing attributes and add missing ones from body.

        For existing attributes the type is resolved using the body-extracted
        type as an improved candidate.  Missing attributes are only added
        when ``force_attributes`` is set or no docstring existed.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust attributes for.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        # Build dicts for faster lookup
        atts_from_doc = {
            att.arg_name: att for att in docstring.params if att.args[0] == "attribute"
        }
        atts_from_sig = {att.arg_name: att for att in self.attributes}

        # --- Fix types for EXISTING attributes (always runs) ---
        for att_doc in docstring.params:
            if att_doc.args[0] != "attribute":
                continue
            att_sig = atts_from_sig.get(att_doc.arg_name)
            match settings.force_attribute_types:
                case ForceOption.FORCE:
                    if not att_doc.type_name or DEFAULT_TYPE in att_doc.type_name:
                        self.issues.append(
                            f"{att_doc.arg_name}: Missing or default type name."
                        )
                    if (
                        att_sig is not None
                        and att_sig.type_name
                        and att_sig.type_name != att_doc.type_name
                    ):
                        self.issues.append(
                            f"{att_doc.arg_name}: Attribute type was"
                            f" `{att_doc.type_name}` but body has"
                            f" type `{att_sig.type_name}`."
                        )
                case ForceOption.UNFORCE:
                    if att_doc.type_name:
                        self.issues.append(f"{att_doc.arg_name}: {ATTRIBUTE_TYPE_SET}")
                case ForceOption.NOFORCE:
                    if (
                        att_sig is not None
                        and att_sig.type_name
                        and att_doc.type_name
                        and att_sig.type_name != att_doc.type_name
                    ):
                        self.issues.append(
                            f"{att_doc.arg_name}: Attribute type was"
                            f" `{att_doc.type_name}` but body has"
                            f" type `{att_sig.type_name}`."
                        )
            att_doc.type_name = resolve_type_name(
                settings.force_attribute_types,
                doc_type=att_doc.type_name,
                improved_types=[att_sig.type_name] if att_sig is not None else [],
            )

        # --- Add MISSING attributes (only when force_attributes or no docstring) ---
        if self.docstring and not settings.force_attributes:
            return
        for name, att_sig in atts_from_sig.items():
            if name in atts_from_doc:
                continue  # Already handled above
            self.issues.append(f"Missing attribute `{att_sig.arg_name}`.")
            docstring.meta.append(
                dsp.DocstringParam(
                    args=["attribute", att_sig.arg_name],
                    description=DEFAULT_DESCRIPTION,
                    arg_name=att_sig.arg_name,
                    type_name=resolve_type_name(
                        new_entry_force_mode(settings.force_attribute_types),
                        improved_types=[att_sig.type_name],
                    ),
                    is_optional=False,
                    default=None,
                )
            )

    def _adjust_methods(
        self, docstring: dsp.Docstring, settings: FixerSettings
    ) -> None:
        """If a new docstring is generated add a methods section.

        Create the full list if there was no original docstring.

        Do not add additional methods and do not create the section
        if it did not exist.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust methods for.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        if self.docstring and not settings.force_methods:
            return
        # Build dicts for faster lookup
        meth_from_doc = {
            meth.arg_name: meth for meth in docstring.params if meth.args[0] == "method"
        }
        for method in self.methods:
            # We already descriptions in the super call.
            if method in meth_from_doc:
                continue
            self.issues.append(f"Missing method `{method}`.")
            docstring.meta.append(
                dsp.DocstringParam(
                    args=["method", method],
                    description=DEFAULT_DESCRIPTION,
                    arg_name=method,
                    type_name=None,
                    is_optional=False,
                    default=None,
                )
            )


@dataclass
class ReturnValue:
    """Info about return value from signature."""

    type_name: str | None = None


@dataclass
class FunctionSignature:
    """Information about a function signature."""

    params: list[Parameter]
    returns: ReturnValue


@dataclass
class FunctionBody:
    """Information about a function from its body."""

    raises: list[str]
    returns: list[tuple[str | None, ...]]
    returns_value: bool
    yields: list[tuple[str | None, ...]]
    yields_value: bool


# ---------------------------------------------------------------------------
# Helper types used by FunctionDocstring for return/yield handling
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NoTypeHint:
    """No type annotation present at all."""


@dataclass(frozen=True)
class NonTupleTypeHint:
    """Explicit annotation that is not a tuple type (e.g. ``str``)."""


@dataclass(frozen=True)
class VariableLengthTuple:
    """Variable-length tuple (e.g. ``tuple[int, ...]``)."""


@dataclass(frozen=True)
class FixedLengthTuple:
    """Fixed-length tuple with a known arity (e.g. ``tuple[int, str, bool]``).

    Parameters
    ----------
    arity : int
        The number of elements in the tuple.
    """

    arity: int


HintClassification: TypeAlias = (
    NoTypeHint | NonTupleTypeHint | VariableLengthTuple | FixedLengthTuple
)


@dataclass(frozen=True)
class ReconcileKindInfo:
    """Kind-specific configuration for return/yield entry reconciliation.

    Parameters
    ----------
    label : str
        Human-readable section name (``"return"`` or ``"yield"``).
    body_tuples : list[tuple[str | None, ...]]
        Name tuples extracted from the function body.
    entry_class : type[dsp.DocstringReturns | dsp.DocstringYields]
        Class to use when creating new placeholder entries.
    args_value : list[str]
        ``args`` field for new entries (e.g. ``["returns"]``).
    """

    label: str
    body_tuples: list[tuple[str | None, ...]]
    entry_class: type[dsp.DocstringReturns | dsp.DocstringYields]
    args_value: list[str]

    @classmethod
    def for_return(cls, body: FunctionBody) -> "ReconcileKindInfo":
        """Create configuration for return entry reconciliation.

        Parameters
        ----------
        body : FunctionBody
            Parsed function body information.

        Returns
        -------
        ReconcileKindInfo
            Return-specific configuration.
        """
        return cls(
            label="return",
            body_tuples=body.returns,
            entry_class=dsp.DocstringReturns,
            args_value=["returns"],
        )

    @classmethod
    def for_yield(cls, body: FunctionBody) -> "ReconcileKindInfo":
        """Create configuration for yield entry reconciliation.

        Parameters
        ----------
        body : FunctionBody
            Parsed function body information.

        Returns
        -------
        ReconcileKindInfo
            Yield-specific configuration.
        """
        return cls(
            label="yield",
            body_tuples=body.yields,
            entry_class=dsp.DocstringYields,
            args_value=["yields"],
        )


@dataclass
class FunctionDocstring(DocstringInfo):
    """Information about a function from docstring."""

    signature: FunctionSignature
    body: FunctionBody
    length: int

    @override
    def _fix_docstring(self, docstring: dsp.Docstring, settings: FixerSettings) -> None:
        """Fix docstrings.

        Additionally adjust:
            parameters from function signature.
            return and yield from signature and body.
            raises from body.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to fix.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        super()._fix_docstring(docstring, settings)
        self._fix_param_types(docstring, settings)
        self._fix_return_types(docstring, settings)
        self._adjust_parameters(docstring, settings)
        self._adjust_returns(docstring, settings)
        self._adjust_yields(docstring, settings)
        self._adjust_raises(docstring, settings)

    def _fix_param_types(
        self, docstring: dsp.Docstring, settings: FixerSettings
    ) -> None:
        """Fix type annotations for parameters in the docstring.

        Resolves types based on the force option using only the types
        already present in the docstring (before reconciliation with
        signature types in ``_adjust_parameters``).

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring whose parameter type information needs fixing.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        for param in docstring.params:
            if param.args[0] == "method":
                continue
            match settings.force_arg_types:
                case ForceOption.FORCE:
                    if not param.type_name or DEFAULT_TYPE in param.type_name:
                        self.issues.append(
                            f"{param.arg_name}: Missing or default type name."
                        )
                case ForceOption.UNFORCE:
                    if param.type_name:
                        self.issues.append(f"{param.arg_name}: {ARG_TYPE_SET}")
                case ForceOption.NOFORCE:
                    pass
            param.type_name = resolve_type_name(
                settings.force_arg_types, doc_type=param.type_name
            )

    def _fix_return_types(
        self, docstring: dsp.Docstring, settings: FixerSettings
    ) -> None:
        """Fix type annotations for return values in the docstring.

        Resolves types based on the force option using only the types
        already present in the docstring (before reconciliation with
        signature types).

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring whose return type information needs fixing.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        for returned in docstring.many_returns:
            match settings.force_return_type:
                case ForceOption.FORCE:
                    if not returned.type_name or DEFAULT_TYPE in returned.type_name:
                        self.issues.append(
                            "Missing or default type name for return value: "
                            f" `{returned.name} |"
                            f" {returned.type_name} |"
                            f" {returned.description}`."
                        )
                case ForceOption.UNFORCE:
                    if returned.type_name:
                        self.issues.append(RETURN_TYPE_SET)
                case ForceOption.NOFORCE:
                    pass
            returned.type_name = resolve_type_name(
                settings.force_return_type, doc_type=returned.type_name
            )

    # -------------------------------------------------------------------
    # Parameter adjustment
    # -------------------------------------------------------------------

    def _escape_default_value(self, default_value: str) -> str:
        r"""Escape the default value so that the docstring remains fully valid.

        Currently only escapes triple quotes '\"\"\"'.

        Parameters
        ----------
        default_value : str
            Value to escape.

        Returns
        -------
        str
            Optionally escaped value.
        """
        if '"""' in default_value:
            if "r" not in self.modifier:
                self.modifier = "r" + self.modifier
            return default_value.replace('"""', r"\"\"\"")
        return default_value

    def _adjust_parameters(
        self, docstring: dsp.Docstring, settings: FixerSettings
    ) -> None:
        """Overwrite or create param docstring entries based on signature.

        If an entry already exists update the type description if one exists
        in the signature. Same for the default value.

        If no entry exists then create one with name, type and default from the
        signature and place holder description.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust parameters for.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        # Build dicts for faster lookup
        params_from_doc = {param.arg_name: param for param in docstring.params}
        params_from_sig = {param.arg_name: param for param in self.signature.params}
        for name, param_sig in params_from_sig.items():
            if name in params_from_doc:
                param_doc = params_from_doc[name]
                match settings.force_arg_types:
                    case ForceOption.FORCE:
                        if (
                            param_sig.type_name
                            and param_sig.type_name != param_doc.type_name
                        ):
                            self.issues.append(
                                f"{name}: Parameter type was"
                                f" `{param_doc.type_name} `but signature"
                                f" has type hint `{param_sig.type_name}`."
                            )
                    case ForceOption.UNFORCE:
                        if param_doc.type_name:
                            self.issues.append(f"{name}: {ARG_TYPE_SET}")
                    case ForceOption.NOFORCE:
                        if (
                            param_sig.type_name
                            and param_doc.type_name
                            and param_sig.type_name != param_doc.type_name
                        ):
                            self.issues.append(
                                f"{name}: Parameter type was"
                                f" `{param_doc.type_name} `but signature"
                                f" has type hint `{param_sig.type_name}`."
                            )
                param_doc.type_name = resolve_type_name(
                    settings.force_arg_types,
                    doc_type=param_doc.type_name,
                    improved_types=[param_sig.type_name],
                )
                param_doc.is_optional = False
                if param_sig.default:
                    param_doc.default = param_sig.default
                    # param_doc.description should never be None at this point
                    # as it should have already been set by '_fix_descriptions'
                    if (
                        param_doc.description is not None
                        and "default" not in param_doc.description.lower()
                        and settings.force_defaults
                    ):
                        self.issues.append(
                            f"{name}: Missing description of default value."
                        )
                        param_doc.description += (
                            f" (Default value = "
                            f"{self._escape_default_value(param_sig.default)})"
                        )
            elif (
                settings.force_params
                and len(params_from_sig) >= settings.force_params_min_n_params
                and self.length >= settings.force_meta_min_func_length
            ) or not self.docstring:
                self.issues.append(f"Missing parameter `{name}`.")
                place_holder_description = DEFAULT_DESCRIPTION
                if param_sig.default:
                    place_holder_description += (
                        f" (Default value = "
                        f"{self._escape_default_value(param_sig.default)})"
                    )
                docstring.meta.append(
                    dsp.DocstringParam(
                        args=["param", name],
                        description=place_holder_description,
                        arg_name=name,
                        type_name=resolve_type_name(
                            new_entry_force_mode(settings.force_arg_types),
                            improved_types=[param_sig.type_name],
                        ),
                        is_optional=False,
                        default=param_sig.default,
                    )
                )

    # -------------------------------------------------------------------
    # Raises adjustment
    # -------------------------------------------------------------------

    def _get_missing_raises_per_site(
        self, docstring: dsp.Docstring, raised_in_body: list[str]
    ) -> list[str]:
        """Get missing raises using per-site (list) comparison.

        Each raise statement in the body requires one corresponding entry
        in the docstring. Same exception type raised multiple times requires
        multiple docstring entries.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to check for documented raises.
        raised_in_body : list[str]
            List of exception types raised in the function body.

        Returns
        -------
        list[str]
            List of missing exception types to add to docstring.
        """
        # Only consider those raises that are not already raised in the body.
        # We are potentially raising the same type of exception multiple times.
        # Only remove the first of each type per one encountered in the docstring..
        missing = raised_in_body.copy()
        # Sort the raised assertions so that `DEFAULT_EXCEPTION` are at the beginning.
        # This ensures that these are removed first before we start removing
        # them through more specific exceptions
        for raised in sorted(
            docstring.raises,
            key=lambda x: x.type_name == DEFAULT_EXCEPTION,
            reverse=True,
        ):
            if raised.type_name in missing:
                missing.remove(raised.type_name)
            # If this specific Error is not in the body but the body contains
            # unknown exceptions then remove one of those instead.
            # For example when exception stored in variable and raised later.
            # We want people to be able to specific them by name and not have
            # pymend constantly force unnamed raises on them.
            elif DEFAULT_EXCEPTION in missing:
                missing.remove(DEFAULT_EXCEPTION)
        return missing

    def _get_missing_raises_per_type(
        self, docstring: dsp.Docstring, raised_in_body: list[str]
    ) -> list[str]:
        """Get missing raises using per-type (set) comparison.

        Each unique exception type raised in the body requires one corresponding
        entry in the docstring. Same exception type raised multiple times only
        requires one docstring entry.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to check for documented raises.
        raised_in_body : list[str]
            List of exception types raised in the function body.

        Returns
        -------
        list[str]
            List of missing exception types to add to docstring.
        """
        raised_set = set(raised_in_body)
        documented = {r.type_name for r in docstring.raises}
        missing = raised_set - documented
        if DEFAULT_EXCEPTION in missing and (documented - raised_set):
            missing.remove(DEFAULT_EXCEPTION)
        return sorted(missing, key=raised_in_body.index)

    def _adjust_raises(self, docstring: dsp.Docstring, settings: FixerSettings) -> None:
        """Adjust raises section based on parsed body.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust raises section for.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        if self.docstring and settings.force_raises == RaisesForceMode.OFF:
            return
        match settings.force_raises:
            # If we dont have a docstring at all at the beginning we
            # still create the maximal raises section even for OFF mode
            case RaisesForceMode.OFF | RaisesForceMode.PER_SITE:
                missing_raises = self._get_missing_raises_per_site(
                    docstring, self.body.raises
                )
            case RaisesForceMode.PER_TYPE:
                missing_raises = self._get_missing_raises_per_type(
                    docstring, self.body.raises
                )
        for missing_raise in missing_raises:
            self.issues.append(f"Missing raised exception `{missing_raise}`.")
            docstring.meta.append(
                dsp.DocstringRaises(
                    args=["raises", missing_raise],
                    description=DEFAULT_DESCRIPTION,
                    type_name=missing_raise,
                )
            )

    # -------------------------------------------------------------------
    # Return / yield adjustment
    # -------------------------------------------------------------------

    def _adjust_returns(
        self, docstring: dsp.Docstring, settings: FixerSettings
    ) -> None:
        """Overwrite or create return docstring entries based on signature.

        If no return value was parsed from the docstring:
        Add one based on the signature with a dummy description except
        if the return type was not specified or specified to be None AND there
        was an existing docstring.

        If one return value is specified overwrite the type with the signature
        if one was present there. For generators this is only done when the
        return type was explicitly extracted from a Generator[Y, S, R]
        annotation, not for ambiguous plain annotations.

        If multiple were specified then reconcile them with the names
        extracted from the function body's return tuples.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust return values for.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        doc_returns = docstring.many_returns
        sig_return = self.signature.returns.type_name
        # If the return type is a generator extract the actual return type.
        sig_return_from_generator = False
        if sig_return and (gen_args := _split_generator_args(sig_return)):
            _yield_type, _send_type, sig_return = gen_args
            sig_return_from_generator = True
        docstring.return_type_annotation = sig_return
        return_info = ReconcileKindInfo.for_return(self.body)

        if (
            not doc_returns
            and self.body.returns_value
            # If we do not want to force returns then only add new ones if
            # there was no docstring at all.
            and (
                (
                    settings.force_return
                    and self.length >= settings.force_meta_min_func_length
                )
                or not self.docstring
            )
        ):
            self._add_placeholder_entry(
                docstring,
                sig_return,
                force_return_type=settings.force_return_type,
                kind_info=return_info,
            )
        # If there is only one return value specified then correct it with
        # the actual return type. For generators this is only safe when
        # we explicitly extracted the return type from Generator[Y, S, R].
        elif len(doc_returns) == 1 and (
            not self.body.yields_value or sig_return_from_generator
        ):
            self._update_single_entry_type(
                doc_returns[0], sig_return, settings=settings, kind_info=return_info
            )
        # If we have multiple return values specified then reconcile with
        # the names from the body's return tuples.
        elif len(doc_returns) > 1:
            self._reconcile_multi_entries(
                docstring,
                doc_returns,
                sig_return,
                settings=settings,
                kind_info=return_info,
            )
        elif settings.force_return_type == ForceOption.UNFORCE:
            for doc_return in doc_returns:
                doc_return.type_name = None

    def _adjust_yields(self, docstring: dsp.Docstring, settings: FixerSettings) -> None:
        """Overwrite or create yield docstring entries based on signature.

        Analogous to ``_adjust_returns`` but extracts the yield type from
        ``Iterator[Y]``, ``Iterable[Y]``, or ``Generator[Y, S, R]`` annotations.
        For plain annotations (e.g. ``-> str``) the yield type is unknown
        and set to None.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to adjust yields for.
        settings : FixerSettings
            Settings for what to fix and when.
        """
        doc_yields = docstring.many_yields
        sig_yield = self.signature.returns.type_name
        # Extract yield type from Iterator/Iterable/Generator annotations.
        if sig_yield and (
            iter_match := re.match(r"(?:Iterable|Iterator)\[(.+)\]$", sig_yield)
        ):
            sig_yield = iter_match[1]
        elif sig_yield and (gen_args := _split_generator_args(sig_yield)):
            sig_yield, _send_type, _return_type = gen_args
        else:
            sig_yield = None
        docstring.yield_type_annotation = sig_yield
        yield_info = ReconcileKindInfo.for_yield(self.body)
        # If no yields documented but body yields, add a placeholder.
        if (
            not doc_yields
            and self.body.yields_value
            and (
                (
                    settings.force_return
                    and self.length >= settings.force_meta_min_func_length
                )
                or not self.docstring
            )
        ):
            self._add_placeholder_entry(
                docstring,
                sig_yield,
                force_return_type=settings.force_return_type,
                kind_info=yield_info,
            )
        elif len(doc_yields) == 1:
            self._update_single_entry_type(
                doc_yields[0], sig_yield, settings=settings, kind_info=yield_info
            )
        # If we have multiple yield values specified then reconcile with
        # the names from the body's yield tuples.
        elif len(doc_yields) > 1:
            self._reconcile_multi_entries(
                docstring,
                doc_yields,
                sig_yield,
                settings=settings,
                kind_info=yield_info,
            )

    # -------------------------------------------------------------------
    # Return / yield helpers (single-entry)
    # -------------------------------------------------------------------

    def _add_placeholder_entry(
        self,
        docstring: dsp.Docstring,
        sig_type: str | None,
        *,
        force_return_type: ForceOption,
        kind_info: ReconcileKindInfo,
    ) -> None:
        """Append a placeholder return or yield entry to the docstring.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring to append the entry to.
        sig_type : str | None
            The signature type annotation for the entry.
        force_return_type : ForceOption
            The user's force mode for return types.
        kind_info : ReconcileKindInfo
            Kind-specific labels, entry class, and args.
        """
        type_name = resolve_type_name(
            new_entry_force_mode(force_return_type), improved_types=[sig_type]
        )
        self.issues.append(f"Missing {kind_info.label} value.")
        docstring.meta.append(
            kind_info.entry_class(
                args=kind_info.args_value,
                description=DEFAULT_DESCRIPTION,
                type_name=type_name,
            )
        )

    def _update_single_entry_type(
        self,
        entry: dsp.DocstringReturns | dsp.DocstringYields,
        sig_type: str | None,
        *,
        settings: FixerSettings,
        kind_info: ReconcileKindInfo,
    ) -> None:
        """Update the type of a single documented return or yield entry.

        Overwrites the entry's type with the signature type when appropriate,
        and reports any issues found.

        Parameters
        ----------
        entry : dsp.DocstringReturns | dsp.DocstringYields
            The single documented entry to update.
        sig_type : str | None
            The signature type annotation.
        settings : FixerSettings
            Settings for what to fix and when.
        kind_info : ReconcileKindInfo
            Kind-specific labels and configuration.
        """
        capitalized_label = kind_info.label.capitalize()
        match settings.force_return_type:
            case ForceOption.FORCE:
                if sig_type and entry.type_name != sig_type:
                    self.issues.append(
                        f"{capitalized_label} type was `{entry.type_name}` but"
                        f" signature has type hint `{sig_type}`."
                    )
            case ForceOption.UNFORCE:
                if entry.type_name:
                    self.issues.append(RETURN_TYPE_SET)
            case ForceOption.NOFORCE:
                if sig_type and entry.type_name and entry.type_name != sig_type:
                    self.issues.append(
                        f"{capitalized_label} type was `{entry.type_name}` but"
                        f" signature has type hint `{sig_type}`."
                    )
        entry.type_name = resolve_type_name(
            settings.force_return_type,
            doc_type=entry.type_name,
            improved_types=[sig_type],
        )

    # -------------------------------------------------------------------
    # Return / yield helpers (multi-entry reconciliation)
    # -------------------------------------------------------------------

    def _reconcile_multi_entries(
        self,
        docstring: dsp.Docstring,
        doc_entries: list[dsp.DocstringReturns] | list[dsp.DocstringYields],
        sig_type: str | None,
        *,
        settings: FixerSettings,
        kind_info: ReconcileKindInfo,
    ) -> None:
        """Reconcile multiple documented return or yield values with body and type hint.

        Validates arity across the type hint, docstring, and body tuples.
        Reports issues for mismatches and adds missing named entries.

        Docstring names always have naming priority: a name from the
        docstring is never replaced by a body name.  However, the
        *positional order* is determined by the body tuples when
        they are consistent (a name always appears at the same position).

        When all body tuples share a single length that is greater than
        the docstring count, and the type hint is either absent, a
        matching fixed-length tuple, or a variable-length tuple, the
        docstring is *extended* to match the body arity.

        Parameters
        ----------
        docstring : dsp.Docstring
            Docstring being adjusted.
        doc_entries : list[dsp.DocstringReturns] | list[dsp.DocstringYields]
            The documented entries (len > 1).
        sig_type : str | None
            The type annotation (after Generator/Iterator extraction).
        settings : FixerSettings
            Settings for what to fix and when.
        kind_info : ReconcileKindInfo
            Kind-specific labels, entry class, and args.
        """
        hint = _classify_type_hint(sig_type)
        body_lengths = {len(t) for t in kind_info.body_tuples}

        self._report_hint_issues(
            hint,
            sig_type,
            len(doc_entries),
            kind_info,
            body_lengths=body_lengths,
        )
        self._report_body_arity_mismatches(
            body_lengths, len(doc_entries), label=kind_info.label
        )

        canonical = _merge_return_names(
            kind_info.body_tuples,
            [entry.name for entry in doc_entries],
            target_length=_determine_target_arity(
                body_lengths, len(doc_entries), hint=hint
            ),
        )

        ordered_entries = self._build_ordered_entries(
            canonical,
            doc_entries,
            kind_info=kind_info,
            force_return_type=settings.force_return_type,
        )
        _apply_reconciled_entries(
            docstring, ordered_entries, entry_class=kind_info.entry_class
        )

    def _report_hint_issues(
        self,
        hint: HintClassification,
        sig_type: str | None,
        doc_count: int,
        kind_info: ReconcileKindInfo,
        *,
        body_lengths: set[int],
    ) -> None:
        """Report issues when the type hint conflicts with the documented entries.

        Parameters
        ----------
        hint : HintClassification
            Classified type annotation.
        sig_type : str | None
            Raw type annotation string.
        doc_count : int
            Number of documented entries.
        kind_info : ReconcileKindInfo
            Kind-specific labels and configuration.
        body_lengths : set[int]
            Distinct lengths of body tuples.
        """
        match hint:
            case NonTupleTypeHint():
                self.issues.append(
                    f"Docstring has {doc_count} {kind_info.label} entries but type"
                    f" hint `{sig_type}` is not a tuple type."
                )
            case FixedLengthTuple(arity=arity) if arity != doc_count:
                self.issues.append(
                    f"Docstring has {doc_count} {kind_info.label} entries but type"
                    f" hint `{sig_type}` has {arity} elements."
                )
                for length in sorted(body_lengths):
                    if length != doc_count:
                        self.issues.append(
                            f"{kind_info.label.capitalize()} tuple has length"
                            f" {length} but type hint `{sig_type}` has"
                            f" {arity} elements."
                        )
            case NoTypeHint() | VariableLengthTuple() | FixedLengthTuple():
                pass

    def _report_body_arity_mismatches(
        self,
        body_lengths: set[int],
        doc_count: int,
        *,
        label: str,
    ) -> None:
        """Report body tuples whose length differs from the documented count.

        Parameters
        ----------
        body_lengths : set[int]
            Distinct lengths of body tuples.
        doc_count : int
            Number of documented entries.
        label : str
            Human-readable label (``"return"`` or ``"yield"``).
        """
        label_cap = label.capitalize()
        for length in sorted(body_lengths):
            if length != doc_count:
                self.issues.append(
                    f"{label_cap} tuple of length {length} does not match"
                    f" {doc_count} documented {label} values."
                )

    def _build_ordered_entries(
        self,
        canonical: tuple[str | None, ...],
        doc_entries: list[dsp.DocstringReturns] | list[dsp.DocstringYields],
        *,
        kind_info: ReconcileKindInfo,
        force_return_type: ForceOption,
    ) -> list[dsp.DocstringReturns | dsp.DocstringYields]:
        """Place existing doc entries at canonical positions, creating missing ones.

        Delegates phases 1 and 2 (name-based and order-based placement) to
        ``_place_existing_entries``, then creates placeholder entries for any
        remaining empty positions (phase 3).

        Parameters
        ----------
        canonical : tuple[str | None, ...]
            Merged name tuple produced by ``_merge_return_names``.
        doc_entries : list[dsp.DocstringReturns] | list[dsp.DocstringYields]
            The existing documented entries.
        kind_info : ReconcileKindInfo
            Kind-specific labels, entry class, and args.
        force_return_type : ForceOption
            Whether to force a default type on new entries.

        Returns
        -------
        list[dsp.DocstringReturns | dsp.DocstringYields]
            Ordered entries ready to be written back to ``docstring.meta``.
        """
        result = _place_existing_entries(canonical, doc_entries)
        any_named = any(entry.name is not None for entry in doc_entries)

        for position, slot in enumerate(result):
            if slot is not None:
                continue
            name = canonical[position]
            if name is not None:
                self.issues.append(
                    f"Missing {kind_info.label} value in multi"
                    f" {kind_info.label} statement `{name}`."
                )
            else:
                self.issues.append(
                    f"Missing unnamed {kind_info.label} value at position {position}."
                )
            result[position] = kind_info.entry_class(
                args=kind_info.args_value,
                description=DEFAULT_DESCRIPTION,
                type_name=resolve_type_name(new_entry_force_mode(force_return_type)),
                name=name if any_named else None,
            )

        return [entry for entry in result if entry is not None]


# ---------------------------------------------------------------------------
# Standalone helper functions for FunctionDocstring return/yield handling
# ---------------------------------------------------------------------------


def _split_bracketed_args(inner: str) -> list[str] | None:
    """Split comma-separated type args respecting nested square brackets.

    Parameters
    ----------
    inner : str
        The content between the outer brackets, e.g. for ``Generator[int, None, str]``
        this would be ``"int, None, str"``.

    Returns
    -------
    list[str] | None
        List of stripped type argument strings, or None if the brackets
        are unbalanced / malformed.
    """
    depth = 0
    parts: list[str] = []
    current: list[str] = []
    for char in inner:
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth < 0:
                return None
        elif char == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    if depth != 0:
        return None
    parts.append("".join(current).strip())
    return parts


def _split_generator_args(type_str: str) -> tuple[str, str, str] | None:
    """Extract (YieldType, SendType, ReturnType) from a Generator annotation.

    Splits ``Generator[Y, S, R]`` into its three type arguments, correctly
    handling nested brackets like ``Generator[list[int], None, tuple[str, int]]``.

    Parameters
    ----------
    type_str : str
        The full type annotation string, e.g. ``"Generator[list[int], None, str]"``.

    Returns
    -------
    tuple[str, str, str] | None
        A 3-tuple of (yield_type, send_type, return_type) if the annotation is a
        well-formed ``Generator[...]`` with exactly 3 type arguments, otherwise None.
    """
    if not (match := re.match(r"Generator\[(.+)\]$", type_str)):
        return None
    parts = _split_bracketed_args(match[1])
    n_generator_type_args = 3
    if parts is None or len(parts) != n_generator_type_args:
        return None
    return parts[0], parts[1], parts[2]


def _classify_type_hint(type_str: str | None) -> HintClassification:
    """Classify a type annotation for multi-return/yield analysis.

    Handles both ``tuple[int, str, bool]`` and ``Tuple[int, str, bool]``.

    Parameters
    ----------
    type_str : str | None
        The full type annotation string, or None if there is no annotation.

    Returns
    -------
    HintClassification
        Classification of the type annotation.
    """
    if type_str is None:
        return NoTypeHint()
    if not (match := re.match(r"[Tt]uple\[(.+)\]$", type_str)):
        return NonTupleTypeHint()
    parts = _split_bracketed_args(match[1])
    if parts is None:
        return NonTupleTypeHint()
    # tuple[int, ...] is a variable-length tuple, not fixed arity.
    var_length_tuple_entries = 2
    if len(parts) == var_length_tuple_entries and parts[1] == "...":
        return VariableLengthTuple()
    return FixedLengthTuple(arity=len(parts))


def _determine_target_arity(
    body_lengths: set[int],
    doc_count: int,
    *,
    hint: HintClassification,
) -> int:
    """Decide the target number of entries after reconciliation.

    If all body tuples share a single length greater than *doc_count*,
    and the type hint allows it, the target is extended to match the body.

    Parameters
    ----------
    body_lengths : set[int]
        Distinct lengths of body tuples.
    doc_count : int
        Number of currently documented entries.
    hint : HintClassification
        Classified type annotation.

    Returns
    -------
    int
        The target number of entries.
    """
    body_arity = next(iter(body_lengths)) if len(body_lengths) == 1 else None
    target = doc_count
    if body_arity is not None and body_arity > doc_count:
        match hint:
            case NoTypeHint() | VariableLengthTuple():
                target = body_arity
            case FixedLengthTuple(arity=hint_arity) if hint_arity == body_arity:
                target = body_arity
            case NonTupleTypeHint() | FixedLengthTuple():
                pass
    return target


def _merge_return_names(
    body_returns: list[tuple[str | None, ...]],
    doc_names: list[str | None],
    *,
    target_length: int,
) -> tuple[str | None, ...]:
    """Merge body return names and docstring names into a canonical ordering.

    Docstring names always have **naming** priority (they are never
    dropped in favour of a body name), but body return tuples determine
    the **positional** order when they are consistent.

    Algorithm
    ---------
    1. Compute the most common body name at each position of
       ``target_length`` from body tuples that match that length.
    2. Compute *body-consistent positions*: for each name that appears in
       the matching body tuples, check whether it **always** occupies the
       same position.  If so, record that position.
    3. For each doc name that has a body-consistent position *and* that
       position is still free, assign the doc name there.
    4. Remaining doc names (those without a consistent body position, or
       whose position was already taken) fill the next free slots in their
       original docstring order.
    5. Any position still unassigned is filled from the body name at that
       position.

    Parameters
    ----------
    body_returns : list[tuple[str | None, ...]]
        All return/yield tuples extracted from the function body.
    doc_names : list[str | None]
        Existing return/yield names from the docstring, by position.
    target_length : int
        The desired length of the result.

    Returns
    -------
    tuple[str | None, ...]
        Canonical tuple of names with one entry per position.
    """
    matching_tuples = [
        body_tuple for body_tuple in body_returns if len(body_tuple) == target_length
    ]

    if not matching_tuples:
        # No body information at all — keep the docstring as-is, padded
        # with None when target exceeds doc_names.
        return tuple(
            doc_names[position] if position < len(doc_names) else None
            for position in range(target_length)
        )

    # Steps 1+2: per-position counters, consistent positions, and the
    # maximum number of times each name appears in any single body tuple.
    name_freq_by_position, consistent, max_occurrences = _analyze_body_names(
        matching_tuples
    )

    # Compute how many times each name is allowed in the result: the
    # maximum of its count in the docstring and its highest count in any
    # single body tuple.
    doc_counts = Counter(name for name in doc_names if name is not None)
    allowance = Counter[str]()
    for name in doc_counts.keys() | max_occurrences.keys():
        allowance[name] = max(doc_counts.get(name, 0), max_occurrences.get(name, 0))

    # Track how many times each name has been used so far.
    used = Counter[str]()

    # Steps 3+4: place doc names at their consistent body positions,
    # then fill remaining doc names at the next free slots.
    assigned = _assign_doc_names(
        doc_names, consistent, target_length=target_length, used=used
    )

    # Step 5: fill remaining positions from body names.
    return _fill_from_body_names(
        assigned,
        name_freq_by_position,
        used=used,
        allowance=allowance,
        target_length=target_length,
    )


def _analyze_body_names(
    same_length_tuples: list[tuple[str | None, ...]],
) -> tuple[list[Counter[str]], dict[str, int], dict[str, int]]:
    """Compute per-position frequency counters and consistent-position mapping.

    All tuples in *same_length_tuples* must share the same length.  Does a
    single pass to collect three things:

    1. **name_freq_by_position**: for each position, a ``Counter`` of
       non-None names across all tuples, ordered by frequency then first
       occurrence.
    2. **consistent**: for each name that only ever occupies a *single*
       position across all tuples, ``{name: position}``.
    3. **max_occurrences**: for each name, the maximum number of times it
       appears in any single body tuple (e.g. ``return a, b, a`` gives
       ``{"a": 2, "b": 1}``).

    Parameters
    ----------
    same_length_tuples : list[tuple[str | None, ...]]
        Body tuples that all share the same length.  Must be non-empty.

    Returns
    -------
    name_freq_by_position : list[Counter[str]]
        Full frequency counter for each position.
    consistent : dict[str, int]
        ``{name: position}`` for names with a single consistent position.
    max_occurrences : dict[str, int]
        Maximum times each name appears in any single body tuple.
    """
    name_freq_by_position: list[Counter[str]] = [
        Counter() for _ in same_length_tuples[0]
    ]
    positions_of: dict[str, set[int]] = {}
    max_occurrences: dict[str, int] = {}
    for body_tuple in same_length_tuples:
        tuple_counts: Counter[str] = Counter()
        for position, name in enumerate(body_tuple):
            if name is not None:
                name_freq_by_position[position][name] += 1
                positions_of.setdefault(name, set()).add(position)
                tuple_counts[name] += 1
        for name, count in tuple_counts.items():
            if count > max_occurrences.get(name, 0):
                max_occurrences[name] = count

    consistent = {
        name: next(iter(positions))
        for name, positions in positions_of.items()
        if len(positions) == 1
    }
    return name_freq_by_position, consistent, max_occurrences


def _assign_doc_names(
    doc_names: list[str | None],
    consistent: dict[str, int],
    *,
    target_length: int,
    used: Counter[str],
) -> dict[int, str]:
    """Assign docstring names to positions using body-consistent placement.

    First, non-None doc names with a consistent body position are placed
    at that position.  Then, remaining non-None doc names fill the next
    free slots in their original docstring order.

    *used* is updated in-place to track how many times each name has been
    placed.

    Parameters
    ----------
    doc_names : list[str | None]
        Existing return/yield names from the docstring.
    consistent : dict[str, int]
        ``{name: position}`` for names with a single consistent body position.
    target_length : int
        Total number of positions in the result.
    used : Counter[str]
        Running count of how many times each name has been placed so far.
        Updated in-place.

    Returns
    -------
    dict[int, str]
        ``{position: name}`` for every position that received a doc name.
    """
    assigned: dict[int, str] = {}
    unmatched: list[str] = []

    for doc_name in doc_names:
        if doc_name is None:
            continue
        consistent_pos = consistent.get(doc_name)
        if consistent_pos is not None and consistent_pos not in assigned:
            assigned[consistent_pos] = doc_name
            used[doc_name] += 1
        else:
            unmatched.append(doc_name)

    free_positions = iter(
        position for position in range(target_length) if position not in assigned
    )
    for doc_name in unmatched:
        free_position = next(free_positions, None)
        if free_position is not None:
            assigned[free_position] = doc_name
            used[doc_name] += 1

    return assigned


def _fill_from_body_names(
    assigned: dict[int, str],
    name_freq_by_position: list[Counter[str]],
    *,
    used: Counter[str],
    allowance: Counter[str],
    target_length: int,
) -> tuple[str | None, ...]:
    """Fill unassigned positions from the most common body names.

    For each position not already in *assigned*, pick the most frequent
    body-name candidate whose usage count has not yet reached its
    allowance.  This avoids spurious duplicates while still allowing
    genuine ones (e.g. ``return a, b, a``).

    Parameters
    ----------
    assigned : dict[int, str]
        Positions already claimed by docstring names.
    name_freq_by_position : list[Counter[str]]
        Per-position frequency counter of body names.
    used : Counter[str]
        Running count of how many times each name has been placed.
        Updated in-place.
    allowance : Counter[str]
        Maximum allowed occurrences for each name.
    target_length : int
        Total number of positions in the result.

    Returns
    -------
    tuple[str | None, ...]
        Final merged tuple of names.
    """
    result: list[str | None] = []
    for position in range(target_length):
        if position in assigned:
            result.append(assigned[position])
            continue
        chosen: str | None = None
        for name, _count in name_freq_by_position[position].most_common():
            if used[name] < allowance[name]:
                chosen = name
                break
        if chosen is not None:
            used[chosen] += 1
        result.append(chosen)
    return tuple(result)


def _place_existing_entries(
    canonical: tuple[str | None, ...],
    doc_entries: list[dsp.DocstringReturns] | list[dsp.DocstringYields],
) -> list[dsp.DocstringReturns | dsp.DocstringYields | None]:
    """Place existing doc entries at canonical positions by name, then by order.

    Phase 1: entries with an exact name match go to their canonical slot.
    Phase 2: leftover existing entries fill the next free slots, updating
    their names to the canonical name when at least one entry was named.

    Parameters
    ----------
    canonical : tuple[str | None, ...]
        Merged name tuple produced by ``_merge_return_names``.
    doc_entries : list[dsp.DocstringReturns] | list[dsp.DocstringYields]
        The existing documented entries.

    Returns
    -------
    list[dsp.DocstringReturns | dsp.DocstringYields | None]
        Partially filled list (same length as *canonical*); ``None`` marks
        positions that still need a new placeholder entry.
    """
    remaining = list(doc_entries)
    result: list[dsp.DocstringReturns | dsp.DocstringYields | None] = [None] * len(
        canonical
    )

    # Phase 1: exact name matches.
    for position, name in enumerate(canonical):
        if name is None:
            continue
        match_idx = next(
            (
                index
                for index, existing in enumerate(remaining)
                if existing.name == name
            ),
            None,
        )
        if match_idx is not None:
            result[position] = remaining.pop(match_idx)

    # Phase 2: fill free positions with leftover existing entries.
    any_named = any(entry.name is not None for entry in doc_entries)
    free = (position for position in range(len(canonical)) if result[position] is None)
    for position, entry in zip(free, remaining, strict=False):
        name = canonical[position]
        if any_named and name is not None:
            entry.name = name
        result[position] = entry

    return result


def _apply_reconciled_entries(
    docstring: dsp.Docstring,
    ordered_entries: list[dsp.DocstringReturns | dsp.DocstringYields],
    *,
    entry_class: type[dsp.DocstringReturns | dsp.DocstringYields],
) -> None:
    """Write reconciled entries back into the docstring's meta list.

    Overwrites existing slots of *entry_class* in canonical order
    and appends any extras beyond the original count.

    Parameters
    ----------
    docstring : dsp.Docstring
        Docstring whose ``meta`` list is updated in-place.
    ordered_entries : list[dsp.DocstringReturns | dsp.DocstringYields]
        Entries in their final order.
    entry_class : type[dsp.DocstringReturns | dsp.DocstringYields]
        Class used to identify existing slots in ``docstring.meta``.
    """
    meta_indices = [
        meta_idx
        for meta_idx, meta_entry in enumerate(docstring.meta)
        if isinstance(meta_entry, entry_class)
    ]
    for slot, entry in enumerate(ordered_entries):
        if slot < len(meta_indices):
            docstring.meta[meta_indices[slot]] = entry
        else:
            docstring.meta.append(entry)


ElementDocstring: TypeAlias = ModuleDocstring | ClassDocstring | FunctionDocstring
DefinitionNodes: TypeAlias = ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
NodeOfInterest: TypeAlias = DefinitionNodes | ast.Module
# pylint: disable=no-member
# Match and try star supported
if sys.version_info >= (3, 11):
    BodyTypes: TypeAlias = (
        ast.Module
        | ast.Interactive
        | ast.FunctionDef
        | ast.AsyncFunctionDef
        | ast.ClassDef
        | ast.For
        | ast.AsyncFor
        | ast.While
        | ast.If
        | ast.With
        | ast.AsyncWith
        | ast.Try
        | ast.ExceptHandler
        | ast.match_case
        | ast.TryStar
    )
    TRY_NODES = (ast.Try, ast.TryStar)
# Only match, no trystar
else:
    BodyTypes: TypeAlias = (
        ast.Module
        | ast.Interactive
        | ast.FunctionDef
        | ast.AsyncFunctionDef
        | ast.ClassDef
        | ast.For
        | ast.AsyncFor
        | ast.While
        | ast.If
        | ast.With
        | ast.AsyncWith
        | ast.Try
        | ast.ExceptHandler
        | ast.match_case
    )
    TRY_NODES = (ast.Try,)
