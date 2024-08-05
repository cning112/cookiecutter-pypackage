import shlex

import nox
from nox.sessions import Session

PY_VERSION = ["3.11", "3.12"]

locations = "src", "tests", "noxfile.py", "docs/conf.py"

@nox.session(python=PY_VERSION)
def tests(session):
    session.install("pytest", "pytest-cov")
    session.run(*shlex.split("pytest --cov"))


@nox.session(python=PY_VERSION, reuse_venv=True)
def lint(session):
    session.install("ruff")
    fix = bool(session.posargs and session.posargs[0] == "fix")
    session.run(
        *shlex.split(f"ruff check --config=./pyproject.toml {'--fix' if fix else ''}")
    )
    session.run(
        *shlex.split(f"ruff format --config=./pyproject.toml {'' if fix else '--diff'}")
    )


@nox.session(python=PY_VERSION)
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or locations
    session.install("mypy")
    session.run("mypy", *args)
