#!/usr/bin/env python
"""Regenerate .expected files for pymend integration tests.

Thin wrapper around pytest that sets PYMEND_UPDATE_EXPECTED=1 and
forwards all arguments.  Any test that calls ``check_expected_diff``
will overwrite its .expected file with the current actual output
instead of asserting.

All arguments are passed straight through to pytest, so the full
pytest CLI is available (-k, -v, --collect-only, node IDs, etc.).

Examples::

    # Single test by name pattern
    python scripts/regen_expected.py -k test_positional_only_identifier

    # Full pytest node ID
    python scripts/regen_expected.py tests/test_pymend/test_numpyoutput.py::test_returns

    # Whole test module
    python scripts/regen_expected.py tests/test_pymend/test_numpyoutput.py

    # All integration tests
    python scripts/regen_expected.py tests/test_pymend/

    # Dry-run (see what would be selected, writes nothing)
    python scripts/regen_expected.py --collect-only -q -k test_blank_lines
"""

import os
import subprocess
import sys

MIN_ARGC_WITH_PYTEST_ARGS = 2


def main() -> int:
    """Run pytest in update mode and show which expected files changed."""
    if len(sys.argv) < MIN_ARGC_WITH_PYTEST_ARGS:
        print((__doc__ or "").strip(), file=sys.stderr)
        return 1

    env = os.environ.copy()
    env["PYMEND_UPDATE_EXPECTED"] = "1"

    command = [sys.executable, "-m", "pytest", "-x", *sys.argv[1:]]
    print(f"[REGENERATING] {' '.join(command)}\n")

    # S603: dev-only script forwarding user supplised args to pytest.
    returncode = subprocess.run(command, env=env, check=False).returncode  # noqa: S603

    # Show which expected files were touched.
    # S607: If someone changed your git you are fucked here anyway.
    subprocess.run(
        ["git", "diff", "--stat", "--", "tests/test_pymend/refs/"],  # noqa: S607
        check=False,
    )

    return returncode


if __name__ == "__main__":
    sys.exit(main())
