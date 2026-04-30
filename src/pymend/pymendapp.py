#!/usr/bin/python
"""Command line interface for pymend."""

import platform
import re
import traceback
from pathlib import Path
from re import Pattern
from typing import Any

import click
from click.core import ParameterSource

import pymend.docstring_parser as dsp
from pymend import PyComment, __version__

from .const import DEFAULT_EXCLUDES, OutputMode
from .docstring_info import FixerSettings, ForceOption, RaisesForceMode
from .files import find_pyproject_toml, parse_pyproject_toml
from .option_groups import ExclusiveGroupCommand, MutuallyExclusiveOptionGroup
from .output import out
from .report import Report

# --- Mutually exclusive option groups ---

mode_group = MutuallyExclusiveOptionGroup(
    "Output mode", help="How pymend should output its results."
)

force_arg_types_group = MutuallyExclusiveOptionGroup(
    "Argument type handling",
    help="Control type information in argument sections.",
)

force_return_type_group = MutuallyExclusiveOptionGroup(
    "Return type handling",
    help="Control type information in return/yield sections.",
)

force_attribute_types_group = MutuallyExclusiveOptionGroup(
    "Attribute type handling",
    help="Control type information in attribute sections.",
)

force_raises_group = MutuallyExclusiveOptionGroup(
    "Raises section handling",
    help="Control enforcement of raises sections.",
)

STRING_TO_STYLE = {
    "rest": dsp.DocstringStyle.REST,
    "javadoc": dsp.DocstringStyle.EPYDOC,
    "numpydoc": dsp.DocstringStyle.NUMPYDOC,
    "google": dsp.DocstringStyle.GOOGLE,
}

FORCE_OPTION_KEYS = {"force_arg_types", "force_return_type", "force_attribute_types"}
RAISES_FORCE_KEYS = {"force_raises"}


def path_is_excluded(
    normalized_path: str,
    pattern: Pattern[str] | None,
) -> bool:
    """Check if a path is excluded because it matches and exclusion regex.

    Parameters
    ----------
    normalized_path : str
        Normalized path to check
    pattern : Pattern[str] | None
        Optionally a regex pattern to check against

    Returns
    -------
    bool
        True if the path is excluded by the regex.
    """
    match = pattern.search(normalized_path) if pattern else None
    return bool(match and match.group(0))


def style_option_callback(
    _c: click.Context, _p: click.Option | click.Parameter, style: str
) -> dsp.DocstringStyle:
    """Compute the output style from a --output_stye flag.

    Parameters
    ----------
    style : str
        String representation of the style to use.

    Returns
    -------
    dsp.DocstringStyle
        Style to use.
    """
    if style in STRING_TO_STYLE:
        return STRING_TO_STYLE[style]
    return dsp.DocstringStyle.AUTO


def re_compile_maybe_verbose(regex: str) -> Pattern[str]:
    """Compile a regular expression string in `regex`.

    If it contains newlines, use verbose mode.

    Parameters
    ----------
    regex : str
        Regex to compile.

    Returns
    -------
    Pattern[str]
        Compiled regex.
    """
    if "\n" in regex:
        regex = "(?x)" + regex
    compiled: Pattern[str] = re.compile(regex)
    return compiled


def validate_regex(
    _ctx: click.Context,
    _param: click.Parameter,
    value: str | None,
) -> Pattern[str] | None:
    """Validate the regex from command line.

    Parameters
    ----------
    value : str | None
        Regex pattern to validate.

    Returns
    -------
    Pattern[str] | None
        Compiled regex pattern or None if the input was None.

    Raises
    ------
    click.BadParameter
        If the value is not a valid regex.
    """
    try:
        return re_compile_maybe_verbose(value) if value is not None else None
    except re.error as e:
        msg = f"Not a valid regular expression: {e}"
        raise click.BadParameter(msg) from None


def run(
    files: tuple[str, ...],
    *,
    mode: OutputMode = OutputMode.DIFF,
    output_style: dsp.DocstringStyle = dsp.DocstringStyle.NUMPYDOC,
    input_style: dsp.DocstringStyle = dsp.DocstringStyle.AUTO,
    exclude: Pattern[str],
    extend_exclude: Pattern[str] | None,
    report: Report,
    fixer_settings: FixerSettings,
) -> None:
    r"""Run pymend over the list of files..

    Parameters
    ----------
    files : tuple[str, ...]
        List of files to analyze and fix.
    mode : OutputMode
        Output mode - write, diff, or check-only.
        (Default value = OutputMode.DIFF)
    output_style : dsp.DocstringStyle
        Output style to use for the modified docstrings.
        (Default value = dsp.DocstringStyle.NUMPYDOC)
    input_style : dsp.DocstringStyle
        Input docstring style.
        Auto means that the style is detected automatically. Can cause issues when
        styles are mixed in examples or descriptions."
        (Default value = dsp.DocstringStyle.AUTO)
    exclude : Pattern[str]
        Optional regex pattern to use to exclude files from reformatting.
    extend_exclude : Pattern[str] | None
        Additional regexes to add onto the exclude pattern.
        Useful if one just wants to add some to the existing default.
    report : Report
        Reporter for pretty communication with the user.
    fixer_settings : FixerSettings
        Settings for which fixes should be performed.

    Raises
    ------
    AssertionError
        If the input and output lines are identical but pymend reports
        some elements to have changed.
    """
    for file in files:
        if path_is_excluded(file, exclude):
            report.path_ignored(file, "matches the --exclude regular expression")
            continue
        if path_is_excluded(file, extend_exclude):
            report.path_ignored(file, "matches the --extend-exclude regular expression")
            continue
        try:
            comment = PyComment(
                Path(file),
                output_style=output_style,
                input_style=input_style,
                fixer_settings=fixer_settings,
            )
            n_issues, issue_report = comment.report_issues()
            match mode:
                case OutputMode.WRITE:
                    changed = comment.output_fix()
                case OutputMode.DIFF:
                    changed = comment.output_patch()
                case OutputMode.CHECK_ONLY:
                    changed = comment.check_only()
            report.done(
                file, changed=changed, issues=bool(n_issues), issue_report=issue_report
            )
        except Exception as exc:  # noqa: BLE001
            if report.verbose:
                traceback.print_exc()
            report.failed(file, str(exc))


def _process_force_options(config: dict[str, object]) -> None:
    """Process ForceOption keys in config, converting strings to enum values.

    Parameters
    ----------
    config : dict[str, object]
        Configuration dictionary to process in-place.

    Raises
    ------
    click.BadOptionUsage
        If a force option key has an invalid value.
    """
    for key in FORCE_OPTION_KEYS:
        if (raw := config.get(key)) is not None:
            try:
                config[key] = ForceOption(str(raw).lower())
            except ValueError:
                valid = ", ".join(e.value for e in ForceOption)
                raise click.BadOptionUsage(
                    key.replace("_", "-"),
                    f"Config key {key.replace('_', '-')} must be one of: {valid}",
                ) from None


def _process_raises_force_options(config: dict[str, object]) -> None:
    """Process RaisesForceMode keys in config, converting bool/strings to enum values.

    Parameters
    ----------
    config : dict[str, object]
        Configuration dictionary to process in-place.

    Raises
    ------
    click.BadOptionUsage
        If the force option for raises has an invalid value.
    """
    for key in RAISES_FORCE_KEYS:
        if (raw := config.get(key)) is not None:
            if isinstance(raw, bool):
                config[key] = RaisesForceMode.PER_SITE if raw else RaisesForceMode.OFF
            else:
                try:
                    config[key] = RaisesForceMode(str(raw).lower())
                except ValueError:
                    valid = ", ".join(e.value for e in RaisesForceMode)
                    raise click.BadOptionUsage(
                        key.replace("_", "-"),
                        f"Config key {key.replace('_', '-')} must be one of: {valid}",
                    ) from None


def _validate_exclude_options(config: dict[str, object]) -> None:
    """Validate exclude options in config.

    Parameters
    ----------
    config : dict[str, object]
        Configuration dictionary to validate.

    Raises
    ------
    click.BadOptionUsage
        If the value passed for `exclude` is not a string.
    click.BadOptionUsage
        If the value passed for `extend_exclude` is not a string.
    """
    exclude = config.get("exclude")
    if exclude is not None and not isinstance(exclude, str):
        raise click.BadOptionUsage(
            "exclude",  # noqa: EM101
            "Config key exclude must be a string",
        )

    extend_exclude = config.get("extend_exclude")
    if extend_exclude is not None and not isinstance(extend_exclude, str):
        raise click.BadOptionUsage(
            "extend-exclude",  # noqa: EM101
            "Config key extend-exclude must be a string",
        )


def read_pyproject_toml(
    ctx: click.Context, _param: click.Parameter, value: str | None
) -> str | None:
    """Inject Pymend configuration from "pyproject.toml" into defaults in `ctx`.

    Returns the path to a successfully found and read configuration file, None
    otherwise.

    Parameters
    ----------
    ctx : click.Context
        Context containing preexisting default values.
    value : str | None
        Optionally path to the config file.

    Returns
    -------
    str | None
        Path to the config file if one was found or specified.

    Raises
    ------
    click.FileError
        If there was a problem reading the configuration file.
    click.BadOptionUsage
        If the value passed for `exclude` was not a string.
    click.BadOptionUsage
        If the value passed for `extended_exclude` was not a string.
    click.BadOptionUsage
        If a force option key has an invalid value.
    click.BadOptionUsage
        If the force option for raises has an invalid value.
    """
    if not value:
        value = find_pyproject_toml(ctx.params.get("src", ()))
        if value is None:
            return None

    try:
        config = parse_pyproject_toml(value)
    except (OSError, ValueError) as e:
        raise click.FileError(
            filename=value, hint=f"Error reading configuration file: {e}"
        ) from None

    if not config:
        return None
    # Sanitize the values to be Click friendly. For more information please see:
    # https://github.com/psf/black/issues/1458
    # https://github.com/pallets/click/issues/1567
    config: dict[str, Any] = {
        k: str(v) if not isinstance(v, (list, dict)) else v for k, v in config.items()
    }

    _validate_exclude_options(config)
    _process_force_options(config)
    _process_raises_force_options(config)

    default_map: dict[str, Any] = {}
    if ctx.default_map:
        default_map.update(ctx.default_map)
    default_map.update(config)

    ctx.default_map = default_map
    return value


@click.command(
    cls=ExclusiveGroupCommand,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Create, update or convert docstrings.",
)
@mode_group.option(
    "--diff",
    destination="mode",
    type=OutputMode,
    flag_value=OutputMode.DIFF,
    default=OutputMode.DIFF,
    help="Output a diff/patch for each file instead of modifying.",
)
@mode_group.option(
    "--write",
    destination="mode",
    type=OutputMode,
    flag_value=OutputMode.WRITE,
    help="Directly overwrite the source files.",
)
@mode_group.option(
    "--check-only",
    destination="mode",
    type=OutputMode,
    flag_value=OutputMode.CHECK_ONLY,
    help="Only report issues, do not output any changes.",
)
@click.option(
    "-o",
    "--output-style",
    type=click.Choice(list(STRING_TO_STYLE)),
    callback=style_option_callback,
    multiple=False,
    default="numpydoc",
    help="Output docstring style.",
)
@click.option(
    "-i",
    "--input-style",
    type=click.Choice([*list(STRING_TO_STYLE), "auto"]),
    callback=style_option_callback,
    multiple=False,
    default="auto",
    help=(
        "Input docstring style."
        " Auto means that the style is detected automatically. Can cause issues when"
        " styles are mixed in examples or descriptions."
    ),
)
@click.option(
    "--force-docstrings/--noforce-docstrings",
    is_flag=True,
    default=True,
    help=(
        "Whether to force a docstring even if there is none present."
        " If set to `False`, will only fix existing docstrings."
    ),
)
@click.option(
    "--force-params/--noforce-params",
    is_flag=True,
    default=True,
    help="Whether to force a parameter section even if"
    " there is already an existing docstring."
    " If set will also force the parameters section to name every parameter.",
)
@click.option(
    "--force-params-min-n-params",
    default=0,
    help="Minimum number of arguments detected in the signature"
    " to actually enforce parameters."
    " If less than the specified numbers of arguments are"
    " detected then a parameters section is only build for new docstrings."
    " No new sections are created for existing docstrings and existing sections"
    " are not extended. Only has an effect with --force-params set to true.",
)
@force_arg_types_group.option(
    "--force-arg-types",
    destination="force_arg_types",
    type=ForceOption,
    flag_value=ForceOption.FORCE,
    default=ForceOption.FORCE,
    help="Force the arguments section to specify type information (default).",
)
@force_arg_types_group.option(
    "--unforce-arg-types",
    destination="force_arg_types",
    type=ForceOption,
    flag_value=ForceOption.UNFORCE,
    help="Strip type information from argument sections.",
)
@force_arg_types_group.option(
    "--noforce-arg-types",
    destination="force_arg_types",
    type=ForceOption,
    flag_value=ForceOption.NOFORCE,
    help="Preserve existing type information in argument sections as-is.",
)
@click.option(
    "--force-defaults/--noforce-defaults",
    is_flag=True,
    default=True,
    help="Whether to enforce descriptions having to"
    " name/explain the default value of their parameter.",
)
@click.option(
    "--force-return/--noforce-return",
    is_flag=True,
    default=True,
    help="Whether to force a return/yield section even if"
    " there is already an existing docstring."
    " Will only actually force return/yield sections"
    " if any value return or yield is found in the body.",
)
@force_return_type_group.option(
    "--force-return-type",
    destination="force_return_type",
    type=ForceOption,
    flag_value=ForceOption.FORCE,
    default=ForceOption.FORCE,
    help="Force the returns/yields section to specify type information (default).",
)
@force_return_type_group.option(
    "--unforce-return-type",
    destination="force_return_type",
    type=ForceOption,
    flag_value=ForceOption.UNFORCE,
    help="Strip type information from returns/yields sections.",
)
@force_return_type_group.option(
    "--noforce-return-type",
    destination="force_return_type",
    type=ForceOption,
    flag_value=ForceOption.NOFORCE,
    help="Preserve existing type information in returns/yields sections as-is.",
)
@click.option(
    "--force-meta-min-func-length",
    default=0,
    help="Minimum number statements in the function body"
    " to actually enforce parameters and returns."
    " If less than the specified numbers of statements are"
    " detected then a parameters and return section is only build for new docstrings."
    " No new sections are created for existing docstrings and existing sections"
    " are not extended. Only has an effect with"
    " `--force-params` or `--force-return` set to true.",
)
@force_raises_group.option(
    "--force-raises",
    destination="force_raises",
    type=RaisesForceMode,
    flag_value=RaisesForceMode.PER_SITE,
    default=RaisesForceMode.PER_SITE,
    help="Force raises section with one entry per raise site (default).",
)
@force_raises_group.option(
    "--noforce-raises",
    destination="force_raises",
    type=RaisesForceMode,
    flag_value=RaisesForceMode.OFF,
    help="Don't force raises section.",
)
@force_raises_group.option(
    "--force-raises-per-type",
    destination="force_raises",
    type=RaisesForceMode,
    flag_value=RaisesForceMode.PER_TYPE,
    help="Force raises section with one entry per exception type.",
)
@click.option(
    "--force-methods/--noforce-methods",
    is_flag=True,
    default=False,
    help="Whether to force a methods section for classes even if"
    " there is already an existing docstring."
    " If set it will force one entry in the section per method found."
    " If only some methods are desired to be specified then this should be left off.",
)
@click.option(
    "--property-decorators",
    multiple=True,
    default=["property"],
    help="Decorators that mark a method as a property."
    " Property return types are used as attribute types.",
)
@click.option(
    "--additional-excluded-decorators",
    multiple=True,
    default=["staticmethod", "classmethod"],
    help="Additional decorators (besides property decorators) that exclude"
    " a method from being listed in the Methods section.",
)
@click.option(
    "--force-attributes/--noforce-attributes",
    is_flag=True,
    default=False,
    help="Whether to force an attributes section for classes even if"
    " there is already an existing docstring."
    " If set it will force on entry in the section per attribute found."
    " If only some attributes are desired then this should be left off.",
)
@force_attribute_types_group.option(
    "--force-attribute-types",
    destination="force_attribute_types",
    type=ForceOption,
    flag_value=ForceOption.FORCE,
    default=ForceOption.FORCE,
    help="Force the attributes section to specify type information (default).",
)
@force_attribute_types_group.option(
    "--unforce-attribute-types",
    destination="force_attribute_types",
    type=ForceOption,
    flag_value=ForceOption.UNFORCE,
    help="Strip type information from attribute sections.",
)
@force_attribute_types_group.option(
    "--noforce-attribute-types",
    destination="force_attribute_types",
    type=ForceOption,
    flag_value=ForceOption.NOFORCE,
    help="Preserve existing type information in attribute sections as-is.",
)
@click.option(
    "--attribute-class-decorators",
    multiple=True,
    default=["dataclass"],
    help="Decorators that signal class-level annotated assignments should be"
    " treated as attributes (e.g. @dataclass).",
)
@click.option(
    "--attribute-base-classes",
    multiple=True,
    default=["BaseModel"],
    help="Base classes that signal class-level annotated assignments should be"
    " treated as attributes (e.g. BaseModel).",
)
@click.option(
    "--force-summary-period/--noforce-summary-period",
    is_flag=True,
    default=True,
    help="Whether to enforce the short description ending with a period.",
)
@click.option(
    "--force-summary-blank-line/--noforce-summary-blank-line",
    is_flag=True,
    default=True,
    help="Whether to enforce a blank line after the short description.",
)
@click.option(
    "--force-multiline-docs-end-with-blank/--unforce-multiline-docs-end-with-blank",
    is_flag=True,
    default=False,
    help="Whether to force multiline docstrings to end with a blank line,"
    " or force it to not end with a blank line",
)
@click.option(
    "--ignore-privates/--handle-privates",
    is_flag=True,
    default=True,
    help="Whether to ignore attributes and methods that start with an underscore '_'."
    " This also means that methods with two underscores are ignored."
    " Consequently turning this off also forces processing of such methods."
    " Dunder methods are an exception and are"
    " always ignored regardless of this setting.",
)
@click.option(
    "--ignore-unused-arguments/--handle-unused-arguments",
    is_flag=True,
    default=True,
    help="Whether to ignore arguments starting with an underscore '_'"
    " when building parameter sections.",
)
@click.option(
    "--ignored-decorators",
    multiple=True,
    default=["overload"],
    help="Decorators that, if present,"
    " should cause a function to be ignored for docstring analysis and generation.",
)
@click.option(
    "--ignored-functions",
    multiple=True,
    default=["main"],
    help="Functions that should be ignored for docstring analysis and generation."
    " Only exact matches are ignored. This is not a regex pattern.",
)
@click.option(
    "--ignored-classes",
    multiple=True,
    default=[],
    help="Classes that should be ignored for docstring analysis and generation."
    " Only exact matches are ignored. This is not a regex pattern.",
)
@click.option("--indent", default=4, help="Number of characters used for indentation.")
@click.option(
    "--exclude",
    type=str,
    callback=validate_regex,
    help=(
        "A regular expression that matches files and directories that should be"
        " excluded. An empty value means no paths are excluded."
        " Use forward slashes for directories on all platforms (Windows, too)."
        f" [default: {DEFAULT_EXCLUDES}]"
    ),
    show_default=False,
)
@click.option(
    "--extend-exclude",
    type=str,
    callback=validate_regex,
    help=(
        "Like --exclude, but adds additional files and directories on top of the"
        " excluded ones. (Useful if you simply want to add to the default)"
    ),
)
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help=(
        "Don't emit non-error messages to stderr. Errors are still emitted; silence"
        " those with 2>/dev/null."
    ),
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help=(
        "Also emit messages to stderr about files that were not changed or were ignored"
        " due to exclusion patterns."
    ),
)
@click.version_option(
    version=__version__,
    message=(
        f"%(prog)s, %(version)s\n"
        f"Python ({platform.python_implementation()}) {platform.python_version()}"
    ),
)
@click.argument(
    "src",
    nargs=-1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, readable=True, allow_dash=False
    ),
    is_eager=True,
    metavar="SRC ...",
)
@click.option(
    "--config",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        allow_dash=False,
        path_type=str,
    ),
    is_eager=True,
    callback=read_pyproject_toml,
    help="Read configuration from FILE path.",
)
@click.pass_context
def main(  # pylint: disable=too-many-arguments, too-many-locals  # noqa: PLR0913
    ctx: click.Context,
    *,
    mode: OutputMode,
    output_style: dsp.DocstringStyle,
    input_style: dsp.DocstringStyle,
    exclude: Pattern[str] | None,
    extend_exclude: Pattern[str] | None,
    force_docstrings: bool,
    force_params: bool,
    force_params_min_n_params: bool,
    force_meta_min_func_length: bool,
    force_return: bool,
    force_raises: RaisesForceMode,
    force_methods: bool,
    force_attributes: bool,
    ignore_privates: bool,
    ignore_unused_arguments: bool,
    ignored_decorators: list[str],
    ignored_functions: list[str],
    ignored_classes: list[str],
    attribute_class_decorators: list[str],
    attribute_base_classes: list[str],
    property_decorators: list[str],
    additional_excluded_decorators: list[str],
    force_defaults: bool,
    force_return_type: ForceOption,
    force_arg_types: ForceOption,
    force_attribute_types: ForceOption,
    force_summary_period: bool,
    force_summary_blank_line: bool,
    force_multiline_docs_end_with_blank: bool,
    indent: int,
    quiet: bool,
    verbose: bool,
    src: tuple[str, ...],
    config: str | None,
) -> None:
    """Create, update or convert docstrings."""
    ctx.ensure_object(dict)

    if not src:
        out(main.get_usage(ctx) + "\n\nError: Missing argument 'SRC ...'.")
        ctx.exit(1)

    if verbose and config:
        config_source = ctx.get_parameter_source("config")
        if config_source in (
            ParameterSource.DEFAULT,
            ParameterSource.DEFAULT_MAP,
        ):
            out("Using configuration from project root.", fg="blue")
        else:
            out(f"Using configuration in '{config}'.", fg="blue")
        if ctx.default_map:
            for param, value in ctx.default_map.items():
                out(f"{param}: {value}")

    if (
        output_style == dsp.DocstringStyle.NUMPYDOC
        and force_return_type != ForceOption.FORCE
    ):
        msg = (
            "NumPy docstring style requires return types. "
            f"Cannot use --{force_return_type.value}-return-type"
            " with NumPy output style."
        )
        raise click.UsageError(msg)

    report = Report(mode=mode, quiet=quiet, verbose=verbose)
    fixer_settings = FixerSettings(
        force_docstrings=force_docstrings,
        force_params=force_params,
        force_return=force_return,
        force_raises=force_raises,
        force_methods=force_methods,
        force_attributes=force_attributes,
        force_params_min_n_params=force_params_min_n_params,
        force_meta_min_func_length=force_meta_min_func_length,
        ignore_privates=ignore_privates,
        ignore_unused_arguments=ignore_unused_arguments,
        ignored_decorators=ignored_decorators,
        ignored_functions=ignored_functions,
        ignored_classes=ignored_classes,
        force_defaults=force_defaults,
        force_return_type=force_return_type,
        force_arg_types=force_arg_types,
        force_attribute_types=force_attribute_types,
        force_summary_period=force_summary_period,
        force_summary_blank_line=force_summary_blank_line,
        force_multiline_docs_end_with_blank=force_multiline_docs_end_with_blank,
        indent=indent,
        attribute_class_decorators=attribute_class_decorators,
        attribute_base_classes=attribute_base_classes,
        property_decorators=property_decorators,
        additional_excluded_decorators=additional_excluded_decorators,
    )

    run(
        src,
        mode=mode,
        output_style=output_style,
        input_style=input_style,
        exclude=exclude or DEFAULT_EXCLUDES,
        extend_exclude=extend_exclude,
        report=report,
        fixer_settings=fixer_settings,
    )

    if verbose or not quiet:
        if verbose or report.change_count or report.failure_count:
            out()
        error_msg = "Oh no! 💥 💔 💥"
        out(error_msg if report.return_code else "All done! ✨ 🍰 ✨")
        click.echo(str(report), err=True)
    ctx.exit(report.return_code)
