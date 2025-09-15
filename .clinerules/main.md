# Main cline rules

This project provides a python utility called pychoice. Details can be found in the main README.md.

## Building and Testing

The project uses `uv` and so builds and tests must be run using `uv`. There are also various helpers within the Makefile.

When finishing a new change, the change should be tested using:

1. `make check` which runs the formatter ruff, mypy, and deptry
2. `make test` which runs pytest
3. `make docs-test` to ensure that the documentation can build
