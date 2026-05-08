import argparse
from collections.abc import Sequence
import json
from pathlib import Path
from typing import Any

# Commands known to accept app labels as positional arguments.
# Commands not in this set fall back to options-only completion.
_APP_LABEL_COMMANDS = frozenset(
    {
        "check",
        "dumpdata",
        "makemigrations",
        "migrate",
        "showmigrations",
        "sqlmigrate",
        "test",
    }
)


def _load_cache(path: str) -> dict[str, Any] | None:
    """Read a completion cache from disk, returning None when it is unavailable."""
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _manage_index(words: list[str], cword: int) -> int | None:
    """Return the last manage.py token index before cword."""
    indexes = [idx for idx, word in enumerate(words[:cword]) if word.endswith("manage.py")]
    return indexes[-1] if indexes else None


def _app_labels(cache: dict[str, Any]) -> list[tuple[str, str]]:
    """Return cached app labels with their origin in cache order."""
    labels: list[tuple[str, str]] = []

    for entry in cache.get("app_labels", []):
        if not isinstance(entry, dict):
            continue

        label = entry.get("label")
        if isinstance(label, str) and label:
            origin = entry.get("origin")
            labels.append((label, origin if isinstance(origin, str) and origin else "pip"))
    return labels


def _migration_app_labels(cache: dict[str, Any]) -> list[tuple[str, str]]:
    """Return app labels that have migrations, local apps first then others alphabetically."""
    migrations = cache.get("migrations")
    if not isinstance(migrations, dict):
        return _app_labels(cache)

    migration_labels = {label for label in migrations if isinstance(label, str)}

    origin_lookup: dict[str, str] = {}
    for entry in cache.get("app_labels", []):
        if isinstance(entry, dict):
            label = entry.get("label")
            if isinstance(label, str) and label:
                origin = entry.get("origin")
                origin_lookup[label] = origin if isinstance(origin, str) and origin else "pip"

    local = sorted(label for label in migration_labels if origin_lookup.get(label) == "local")
    non_local = sorted(label for label in migration_labels if origin_lookup.get(label) != "local")

    result = [(label, "local") for label in local]
    result.extend((label, origin_lookup.get(label, "pip")) for label in non_local)
    return result


def _options(cache: dict[str, Any], cmd: str | None) -> list[str]:
    """Return cached option strings for a command."""
    command_options = cache.get("command_options", {})
    if not isinstance(cmd, str) or not isinstance(command_options, dict):
        return []

    opts = command_options.get(cmd, [])
    if not isinstance(opts, list):
        return []
    return [opt for opt in opts if isinstance(opt, str) and opt]


def _local_app_labels(cache: dict[str, Any]) -> list[str]:
    """Return app labels where origin is 'local', alphabetically sorted."""
    return sorted(label for label, origin in _app_labels(cache) if origin == "local")


def _migration_names(cache: dict[str, Any], app_label: str | None, *, include_zero: bool = True) -> list[str]:
    """Return cached migration names for an app, optionally including the zero target."""
    migrations = cache.get("migrations")
    if not isinstance(app_label, str) or not isinstance(migrations, dict):
        return ["zero"] if include_zero else []

    names = migrations.get(app_label, [])
    if not isinstance(names, list):
        return ["zero"] if include_zero else []
    result = [name for name in names if isinstance(name, str) and name]
    if include_zero:
        result.append("zero")
    return result


def _escape_zsh_description(description: str) -> str:
    """Escape zsh description separators."""
    return description.replace(":", r"\:")


def _format_candidates(candidates: Sequence[tuple[str, str | None]], fmt: str) -> list[str]:
    """Format candidates for bash or zsh output."""
    if fmt == "zsh":
        return [f"{value}:{_escape_zsh_description(description or '')}" for value, description in candidates if value]
    return [value for value, _description in candidates if value]


def _command_candidates(cache: dict[str, Any]) -> list[tuple[str, str]]:
    """Return command candidates with help descriptions."""
    command_help = cache.get("command_help", {})
    if not isinstance(command_help, dict):
        command_help = {}

    commands = [cmd_name for cmd_name in cache.get("commands", []) if isinstance(cmd_name, str) and cmd_name]
    return [(cmd_name, command_help.get(cmd_name, "")) for cmd_name in commands]


def _option_candidates(cache: dict[str, Any], cmd: str | None) -> list[tuple[str, str]]:
    """Return option candidates with descriptions for a command."""
    option_descriptions = cache.get("command_option_descriptions", {})
    if not isinstance(option_descriptions, dict):
        option_descriptions = {}
    descriptions = option_descriptions.get(cmd, {}) if isinstance(cmd, str) else {}
    if not isinstance(descriptions, dict):
        descriptions = {}
    return [(opt, descriptions.get(opt, "")) for opt in _options(cache, cmd)]


def _app_and_option_candidates(cache: dict[str, Any], cmd: str | None) -> list[tuple[str, str]]:
    """Return v1-style app label and option candidates for a command."""
    candidates = [(label, f"[{origin}]") for label, origin in _app_labels(cache)]
    candidates.extend(_option_candidates(cache, cmd))
    return candidates


def _migration_app_label_candidates(cache: dict[str, Any], fmt: str) -> list[str]:
    return _format_candidates([(label, f"[{origin}]") for label, origin in _migration_app_labels(cache)], fmt)


def _migration_command_candidates(
    cache: dict[str, Any],
    cmd: str,
    pos: int,
    words: list[str],
    manage_idx: int,
    fmt: str,
) -> list[str]:
    """Handle migrate / showmigrations / sqlmigrate positional completion."""
    if pos == 2:
        return _migration_app_label_candidates(cache, fmt)
    if pos == 3 and cmd in ("migrate", "sqlmigrate"):
        app = words[manage_idx + 2] if manage_idx + 2 < len(words) else None
        include_zero = cmd == "migrate"
        return _format_candidates([(name, "") for name in _migration_names(cache, app, include_zero=include_zero)], fmt)
    return _format_candidates(_option_candidates(cache, cmd), fmt)


def _positional_candidates(
    cache: dict[str, Any],
    cmd: str | None,
    pos: int,
    words: list[str],
    manage_idx: int,
    fmt: str,
) -> list[str]:
    """Return candidates for a non-dash positional argument after the command is known."""
    if cmd == "autocomplete" and pos == 2:
        subcommands = [("install", ""), ("refresh", ""), ("status", ""), ("uninstall", "")]
        return _format_candidates(subcommands, fmt)

    if cmd == "makemigrations":
        return _format_candidates([(label, "[local]") for label in _local_app_labels(cache)], fmt)

    if cmd in ("migrate", "showmigrations", "sqlmigrate") and isinstance(cmd, str):
        return _migration_command_candidates(cache, cmd, pos, words, manage_idx, fmt)

    # Whitelist: commands known to accept app labels get app-label + option completion.
    # Everything else (runserver, shell, custom commands, etc.) gets options only.
    if cmd in _APP_LABEL_COMMANDS:
        return _format_candidates(_app_and_option_candidates(cache, cmd), fmt)
    return _format_candidates(_option_candidates(cache, cmd), fmt)


def complete(cache: dict[str, Any], words: list[str], cword: int, fmt: str = "bash") -> list[str]:
    """Return completion candidates for a tokenized manage.py command line."""
    if cword < 0 or cword >= len(words):
        return []

    # Completion can be registered for wrappers such as python, python3, and uv.
    # Only activate once a manage.py token appears before the word being completed.
    manage_idx = _manage_index(words, cword)
    if manage_idx is None:
        return []

    # pos is relative to manage.py:
    #   manage.py <TAB>             -> pos == 1
    #   manage.py migrate <TAB>     -> pos == 2
    #   manage.py migrate app <TAB> -> pos == 3
    pos = cword - manage_idx
    cur = words[cword]
    cmd = words[manage_idx + 1] if pos >= 2 and manage_idx + 1 < len(words) else None

    if pos == 1:
        return _format_candidates(_command_candidates(cache), fmt)

    # A dash prefix always means option completion for the active command.
    if cur.startswith("-"):
        return _format_candidates(_option_candidates(cache, cmd), fmt)

    return _positional_candidates(cache, cmd, pos, words, manage_idx, fmt)


def _main() -> int:
    """Run the completion helper CLI."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", required=True)
    parser.add_argument("--words-json", required=True)
    parser.add_argument("--cword", required=True, type=int)
    parser.add_argument("--format", choices=("bash", "zsh"), default="bash")
    args = parser.parse_args()

    cache = _load_cache(args.cache)
    if cache is None:
        return 0

    try:
        words = json.loads(args.words_json)
    except json.JSONDecodeError:
        return 0
    if not isinstance(words, list) or not all(isinstance(word, str) for word in words):
        return 0

    candidates = complete(cache, words, args.cword, args.format)
    if candidates:
        print("\n".join(candidates))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
