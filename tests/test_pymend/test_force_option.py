"""Integration tests for ForceOption modes (force, unforce, noforce)."""

import pytest

import pymend.docstring_parser as dsp
import pymend.pymend as pym
from pymend.docstring_info import FixerSettings, ForceOption

from .util import absdir, check_expected_diff

ALL_MODES = list(ForceOption)
# Numpydoc requires force_return_type=FORCE; the other styles support all modes.
STYLES_ALL_MODES = [
    dsp.DocstringStyle.GOOGLE,
    dsp.DocstringStyle.EPYDOC,
    dsp.DocstringStyle.REST,
]


@pytest.mark.parametrize("mode", ALL_MODES)
def test_force_option_numpydoc(mode: ForceOption) -> None:
    """Numpydoc: force_return_type must stay FORCE, arg/attr types vary."""
    check_expected_diff(
        "force_option",
        fixer_settings=FixerSettings(
            force_arg_types=mode,
            force_return_type=ForceOption.FORCE,
            force_attribute_types=mode,
        ),
        reference_name=f"force_option.{mode.value}",
    )


@pytest.mark.parametrize("mode", [ForceOption.UNFORCE, ForceOption.NOFORCE])
def test_force_option_numpydoc_rejects_non_force_return(mode: ForceOption) -> None:
    """UNFORCE and NOFORCE return types are incompatible with numpydoc."""
    with pytest.raises(ValueError, match="NumPy docstring style requires return types"):
        pym.PyComment(
            absdir("refs/force_option.py"),
            fixer_settings=FixerSettings(
                force_arg_types=mode,
                force_return_type=mode,
                force_attribute_types=mode,
            ),
        )


@pytest.mark.parametrize("mode", ALL_MODES)
@pytest.mark.parametrize("style", STYLES_ALL_MODES, ids=lambda s: s.name.lower())
def test_force_option_all_styles(mode: ForceOption, style: dsp.DocstringStyle) -> None:
    """Check force_option.py patch for each mode and output style."""
    check_expected_diff(
        "force_option",
        output_style=style,
        fixer_settings=FixerSettings(
            force_arg_types=mode,
            force_return_type=mode,
            force_attribute_types=mode,
        ),
        reference_name=f"force_option.{mode.value}",
    )
