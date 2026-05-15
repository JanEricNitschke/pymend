"""Mutually exclusive option groups for Click."""

from __future__ import annotations

import sys
from collections import defaultdict
from collections.abc import Callable
from enum import Enum
from typing import TypeVar

import click
from typing_extensions import override

from pymend.const import INTERNAL_FAILURE_EXIT_CODE, internal_error_message
from pymend.output import err

_E = TypeVar("_E", bound=Enum)
_FC = TypeVar("_FC", bound=Callable[..., object] | click.Command)


class ExclusiveGroupCommand(click.Command):
    """Command subclass that checks mutually exclusive option groups.

    Snapshots the raw CLI args before parsing, then after parsing checks
    each :class:`MutuallyExclusiveOptionGroup` for conflicts.
    """

    @override
    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        """Parse args and verify mutually exclusive option constraints.

        Parameters
        ----------
        ctx : click.Context
            The current click context.
        args : list[str]
            The raw CLI arguments before parsing.

        Returns
        -------
        list[str]
            Remaining arguments after parsing.

        Raises
        ------
        click.UsageError
            If two or more options from the same exclusive group were provided.
        """
        raw_args = tuple(args)
        result = super().parse_args(ctx, args)

        # Collect which options were explicitly provided, grouped by group instance.
        provided: defaultdict[MutuallyExclusiveOptionGroup, list[str]] = defaultdict(
            list
        )
        for param in self.params:
            if isinstance(param, _GroupedOption) and any(
                flag in raw_args for flag in param.opts
            ):
                provided[param.group].append(param.opts[0])

        errors: list[str] = []
        for group, flags in provided.items():
            if len(flags) > 1:
                names = ", ".join(f"`{flag}`" for flag in sorted(flags))
                errors.append(
                    f"Mutually exclusive options from `{group.name}`"
                    f" cannot be used together: {names}"
                )
        if errors:
            raise click.UsageError("\n".join(errors), ctx=ctx)

        return result


class _GroupedOption(click.Option):
    """Option that belongs to a mutually exclusive group."""

    def __init__(  # pylint: disable=too-many-positional-arguments,redefined-builtin
        self,
        flag: str,
        destination: str,
        group: MutuallyExclusiveOptionGroup,
        type: type[Enum] | None,  # noqa: A002 — matches click.Option API
        flag_value: Enum | None,
        default: Enum | None,
        help: str | None,  # noqa: A002 — matches click.Option API
    ) -> None:
        """Construct a grouped option.

        Parameters
        ----------
        flag : str
            The CLI flag string (e.g. ``--diff``).
        destination : str
            The click parameter name the value is stored under.
        group : MutuallyExclusiveOptionGroup
            The group this option belongs to.
        type : type[Enum] | None
            The click parameter type.
        flag_value : Enum | None
            The value assigned when this flag is provided.
        default : Enum | None
            The default value when no flag in the group is provided.
        help : str | None
            Help text shown in ``--help``.
        """
        super().__init__(
            [flag, destination],
            type=type,
            flag_value=flag_value,
            default=default,
            help=help,
        )
        # Stored for ExclusiveGroupCommand.parse_args to group params by
        # group instance and for the contiguity check in the decorator.
        self.group = group

    @override
    def get_help_record(self, ctx: click.Context) -> tuple[str, str] | None:
        """Return the help record with extra indentation for visual grouping.

        Returns
        -------
        tuple[str, str] | None
            The indented option flags and help text, or ``None``.
        """
        record = super().get_help_record(ctx)
        if record is None:
            return None
        opts, help_text = record
        return f"  {opts}", help_text


class GroupTitle(click.Option):
    """Invisible option that renders the group heading in `--help`."""

    def __init__(self, group: MutuallyExclusiveOptionGroup) -> None:
        """Construct a group title pseudo-option.

        Parameters
        ----------
        group : MutuallyExclusiveOptionGroup
            The group whose title to render.
        """
        self._group = group
        super().__init__(
            [f"--_grp-{id(group)}"],
            hidden=True,
            expose_value=False,
        )

    @override
    def get_help_record(self, ctx: click.Context) -> tuple[str, str] | None:
        """Return the group title as a help record."""
        return f"{self._group.name} [mutually exclusive]:", self._group.help

    def get_destination(self) -> str:
        """Return the destination (click parameter name) for this group.

        Returns
        -------
        str
            The destination name.

        Raises
        ------
        SystemExit
            If the destination was never set, indicating an internal error.
        """
        if self._group.destination is None:
            err(
                internal_error_message(
                    f"Group '{self._group.name}' has no destination set."
                )
            )
            sys.exit(INTERNAL_FAILURE_EXIT_CODE)
        return self._group.destination


class MutuallyExclusiveOptionGroup:  # pylint: disable=too-few-public-methods
    """A named set of click options where at most one may be provided."""

    def __init__(self, name: str, *, help: str = "") -> None:  # noqa: A002 — matches click API convention  # pylint: disable=redefined-builtin
        """Construct an option group.

        Parameters
        ----------
        name : str
            Display name shown in `--help`.
        help : str
            Help text shown after the group title. (Default value = '')
        """
        self.name = name
        self.help = help
        self._pending = 0
        self._applied = 0
        self.destination: str | None = None

    def option(  # pylint: disable=redefined-builtin
        self,
        flag: str,
        *,
        destination: str,
        type: type[_E],  # noqa: A002 — matches click.option API
        flag_value: _E,
        default: _E | None = None,
        help: str = "",  # noqa: A002 — matches click.option API
    ) -> Callable[[_FC], _FC]:
        """Add a click option to this group.

        Must be applied bottom-to-top like normal click decorators.

        Parameters
        ----------
        flag : str
            The CLI flag string (e.g. ``--diff``).
        destination : str
            The click parameter name the value is stored under.
        type : type[_E]
            The enum type for the option value.
        flag_value : _E
            The value assigned when this flag is provided.
        default : _E | None
            The default value when no flag in the group is provided.
        help : str
            Help text shown in ``--help``. (Default value = '')

        Returns
        -------
        Callable[[_FC], _FC]
            A decorator that registers the option on the click command.
        """
        self._pending += 1

        if self.destination is None:
            self.destination = destination
        elif self.destination != destination:
            err(
                internal_error_message(
                    f"All options in group '{self.name}' must have the"
                    f" same destination. Got '{destination}' but expected"
                    f" '{self.destination}'."
                )
            )
            sys.exit(INTERNAL_FAILURE_EXIT_CODE)

        def decorator(func: _FC) -> _FC:
            """Register the grouped option on the decorated function.

            Parameters
            ----------
            func : _FC
                The click command callback being decorated.

            Returns
            -------
            _FC
                The same function with the option attached.
            """
            grouped_option = _GroupedOption(
                flag,
                destination,
                group=self,
                type=type,
                flag_value=flag_value,
                default=default,
                help=help,
            )

            params: list[click.Parameter] = getattr(func, "__click_params__", [])
            if not hasattr(func, "__click_params__"):
                func.__click_params__ = params  # type: ignore[missing-attribute, union-attr]

            # Ensure group options are contiguous — no interleaved click.option calls.
            if self._applied > 0 and params:
                prev = params[-1]
                if not isinstance(prev, _GroupedOption) or prev.group is not self:
                    err(
                        internal_error_message(
                            f"Options in group '{self.name}' must be"
                            f" contiguous. Found a non-group option"
                            f" between '{flag}' and the previous group"
                            f" option."
                        )
                    )
                    sys.exit(INTERNAL_FAILURE_EXIT_CODE)

            params.append(grouped_option)

            self._applied += 1
            if self._applied == self._pending:
                params.append(GroupTitle(self))

            return func

        return decorator
