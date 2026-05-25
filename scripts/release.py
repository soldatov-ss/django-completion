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


def _sync_schema_version(version: str) -> None:
    schema_path = Path("overrides/main.html")
    if not schema_path.exists():
        return
    text = schema_path.read_text()
    import re

    updated = re.sub(r'"softwareVersion":\s*"[^"]*"', f'"softwareVersion": "{version}"', text)
    if updated != text:
        schema_path.write_text(updated)
        print(f"Updated softwareVersion in {schema_path} to {version}")


def _check_clean_tree() -> None:
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
    if result.stdout.strip():
        print("Uncommitted changes detected. Clean the working tree before releasing:")
        for line in result.stdout.splitlines():
            print(f"  {line}")
        sys.exit(1)


def _check_changelog(version: str) -> str:
    notes_path = Path(f"CHANGELOG/{version}.md")
    if not notes_path.exists():
        print(f"Missing changelog entry: {notes_path}")
        sys.exit(1)

    lines = notes_path.read_text().splitlines(keepends=True)
    # Strip the H1 heading line (gh uses it as the release title)
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
        if lines and not lines[0].strip():
            lines = lines[1:]
    notes = "".join(lines).rstrip()

    if not notes:
        print(f"Changelog entry {notes_path} exists but is empty after the heading.")
        sys.exit(1)

    return notes


def _check_tests() -> None:
    print("$ uv run pytest -q")
    result = subprocess.run(["uv", "run", "pytest", "-q"], check=False)
    if result.returncode != 0:
        print("Tests failed. Fix them before releasing.")
        sys.exit(1)


def main() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    name = pyproject["project"]["name"]
    version = pyproject["project"]["version"]
    tag = f"v{version}"

    _sync_schema_version(version)
    _check_clean_tree()
    notes = _check_changelog(version)
    _check_tests()

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
