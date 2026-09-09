***************
Getting Started
***************

New to *PyMend*? Don't worry, you've found the perfect place to get started!


Installation
============

*PyMend* can be installed by running :code:`pip install pymend`. It requires Python 3.9+ to run.

If you can't wait for the latest *hotness* and want to install from GitHub, use:

:code:`pip install git+https://github.com/JanEricNitschke/pymend`

Basic usage
===========

To get started right away with sensible defaults:

.. code-block:: sh

    pymend {source_file}...


You can run *PyMend* as a package if running it as a script doesn't work:

.. code-block:: sh

    python -m pymend {source_file}...


Exit codes
==========

*PyMend* uses exit codes to indicate the result of processing files:

- **0**: All files are well formatted with no issues
- **1**: One or more files had issues (would be reformatted or have docstring problems)
- **2**: Usage error (e.g. invalid or conflicting command-line options)
- **123**: An internal error occurred

Issues include missing or wrong information, as well as placeholders (e.g. :code:`_description_`, :code:`_type_`) that were not overwritten.

Examples
--------

.. code:: console

    $ pymend src/
    All done! ✨ 🍰 ✨
    5 files would be left unchanged.
    $ echo $?
    0

    $ pymend src/ --check-only
    would reformat src/main.py
    Oh no! 💥 💔 💥
    1 file would be reformatted.

    The following issues were found in file src/main.py:

    --------------------------------------------------
    my_function (line 12):
    Missing short description.
    Missing parameter `x`.

    $ echo $?
    1

    $ pymend src/
    error: cannot format src/main.py: INTERNAL ERROR: PyMend produced different docstrings on the second pass.
    Oh no! 💥 💔 💥
    1 file would fail to reformat.
    $ echo $?
    123

Issue locations
~~~~~~~~~~~~~~~

Each issue header includes the line containing its docstring. For a missing
docstring, this is the line where *PyMend* would insert it; it is not the line
of the corresponding function, class, or method definition. In diff and
check-only modes, locations refer to the source that was inspected. In write
mode, *PyMend* rechecks the written file, so reported locations refer to the
final on-disk source.


Next steps
==========

Try out *PyMend*? Fantastic, you're ready for more.

Why not explore some more on using *PyMend* by reading
:ref:`Usage and Configuration: The basics<The basics>`.

Alternatively, you can check out the
:ref:`Introducing *PyMend* to your project<Introducing Pymend to your project>`
guide.
