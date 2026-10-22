============
Contributing
============

Thank you for contributing to pymend! This guide covers local setup, CI
checks, and contribution expectations.

Ways to contribute
==================

-  Report bugs or request features by opening a `GitHub issue
   <https://github.com/JanEricNitschke/pymend/issues>`__.
-  Improve the documentation in ``docs/`` or ``README.rst``.
-  Fix bugs or implement features and open a focused pull request.

Development setup
=================

pymend supports Python versions from the oldest non-EOL release through the
newest fully released version. It uses `uv <https://docs.astral.sh/uv/>`__
for dependency management. From a checkout of the repository, install the
development environment with:

.. code-block:: sh

   uv sync --all-extras --dev

Local workflow
==============

Before opening a pull request:

-  Run the pre-commit hooks:

   .. code-block:: sh

      uv run pre-commit run --all-files

-  Run the full test suite:

   .. code-block:: sh

      uv run pytest -q

-  If your change affects docstring output, you can auto-regenerate the
   expected patches and rerun the integration tests:

   .. code-block:: sh

      uv run python scripts/regen_expected.py tests/test_pymend/ -q
      uv run pytest tests/test_pymend/ -q

   Review the regenerated diff **in detail**. Regenerated expected files
   belong in the same pull request as the change that caused them.

CI gates
========

Every pull request is validated by the ``build`` GitHub Actions workflow on
Linux, macOS, and Windows for every supported Python version. All jobs must
pass before a change can be merged. CI runs ruff (lint and format), the
configured type checkers, pylint, pre-commit, pytest, and the expected-patch
regeneration check described above.

Coding standards
================

Follow the conventions enforced by the configured tooling. Ruff handles
formatting and linting, the type checkers validate ``src/pymend``, and
docstrings use the numpy style. ``uv run pre-commit run --all-files`` runs
these checks for you. Add tests under ``tests/`` rather than doctests. Source
lives in ``src/pymend``; user-facing documentation lives in ``docs/`` and uses
reStructuredText/Sphinx. Update the documentation when behavior or
configuration changes.

Testing standards
=================

Prefer full integration tests over narrow unit tests. Integration fixtures
live in ``tests/test_pymend/refs/``: ``<name>.py`` is the input and
``<name>.py.patch.<style>.expected`` is the expected patch. Tests compare them
with ``check_expected_diff`` from ``tests/test_pymend/util.py``.

Add issue regressions to ``tests/test_pymend/test_issues.py`` and CLI or
configuration tests to ``tests/test_pymend/test_app.py``. Generate expected
files with ``scripts/regen_expected.py`` and review the diff; do not hand-edit
them.

AI-assisted contributions
=========================

AI-assisted contributions are allowed, but a human is responsible for
everything submitted. Maintainers will not communicate with an AI. The code
MUST be reviewed by a human before the pull request is opened. A human MUST
open the pull request, and its title, description, and all review comments and
responses MUST be written by a human.

Submitting pull requests
========================

-  Keep pull requests focused and small. Separate unrelated refactors,
   formatting changes, and behavior changes.
-  Include tests and documentation updates in the same pull request as the
   behavior they cover.
-  Run the local workflow above before opening the pull request.
-  Reference the relevant issue in the pull request description when
   applicable, for example ``Fixes #123``.
-  Be responsive to review comments and keep the discussion focused on the
   change.

Reporting bugs and requesting features
======================================

Please use the `GitHub issue tracker
<https://github.com/JanEricNitschke/pymend/issues>`__ for bug reports and
feature requests.

For bug reports, include:

-  the pymend version and Python version,
-  the command you ran and any relevant configuration,
-  a minimal input file that reproduces the problem,
-  the actual and expected output; patches are ideal.

For feature requests, describe the use case, the desired behavior, and any
alternatives you considered.
