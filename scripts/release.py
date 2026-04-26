# /// script
# requires-python = ">=3.10"
# dependencies = ["tomli; python_version < '3.11'"]
# ///
"""Tag the current version and create a GitHub release."""

from pathlib import Path
import subprocess
import sys

# tomllib is stdlib on 3.11+; fall back to the third-party backport on 3.10
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def _run(*cmd: str) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> None:
    # Read version and project name from pyproject.toml
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    name = pyproject["project"]["name"]
    version = pyproject["project"]["version"]
    tag = f"v{version}"

    # Strip the H1 heading line from the changelog entry (gh uses it as the title)
    notes_path = Path(f"CHANGELOG/{version}.md")
    lines = notes_path.read_text().splitlines(keepends=True)
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        if lines and not lines[0].strip():
            lines = lines[1:]
    notes = "".join(lines).rstrip()

    # Tag, push, then create the GitHub release
    _run("git", "tag", "-a", tag, "-m", f"Release {tag}")
    _run("git", "push", "origin", tag)
    _run(
        "gh",
        "release",
        "create",
        tag,
        "--verify-tag",
        "--title",
        f"{name} {version}",
        "--notes",
        notes,
    )


if __name__ == "__main__":
    main()
