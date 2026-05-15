from collections.abc import Mapping
import importlib.util
import json
from pathlib import Path
import threading
import time
from typing import Any, TypedDict

from django.apps import apps
from django.conf import settings
from django.core import management

from django_completion.classify import classify_app


class AppLabelEntry(TypedDict):
    label: str
    origin: str  # "local" | "pip"


class CacheData(TypedDict):
    schema_version: int
    commands: list[str]
    app_labels: list[AppLabelEntry]
    command_help: dict[str, str]
    command_options: dict[str, list[str]]
    command_option_descriptions: dict[str, dict[str, str]]
    migrations: dict[str, list[str]]
    warnings: list[str]
    generated_at: float


CACHE_FILENAME = ".django-completion-cache.json"
COOLDOWN_SECONDS = 60
_refresh_lock = threading.Lock()


def _cache_path() -> Path:
    try:
        from django.conf import settings

        if hasattr(settings, "BASE_DIR"):
            return Path(settings.BASE_DIR) / CACHE_FILENAME
    except Exception:
        pass
    return Path.cwd() / CACHE_FILENAME


def _migration_module_path(app_config, migration_modules: dict) -> tuple[str | None, bool]:
    """Return the migrations module path and whether it was explicitly configured."""
    if app_config.label in migration_modules:
        return migration_modules[app_config.label], True
    return f"{app_config.name}.migrations", False


def _migration_names_from_module(module_path: str) -> list[str]:
    """List public migration module names from a migrations package."""
    spec = importlib.util.find_spec(module_path)
    if spec is None or spec.submodule_search_locations is None:
        raise ModuleNotFoundError(f"No module named {module_path!r}")

    names: set[str] = set()
    for location in spec.submodule_search_locations:
        migrations_dir = Path(location)
        if not migrations_dir.is_dir():
            continue
        for path in migrations_dir.iterdir():
            if not path.is_file() or path.suffix != ".py":
                continue
            if path.name == "__init__.py" or path.name.startswith((".", "_")):
                continue
            names.add(path.stem)
    return sorted(names)


def _discover_migrations(app_configs, migration_modules: dict) -> tuple[dict[str, list[str]], list[str]]:
    """Discover migration names for app configs and collect non-fatal inspection warnings."""
    migrations: dict[str, list[str]] = {}
    warnings: list[str] = []

    for app_config in app_configs:
        module_path, is_configured = _migration_module_path(app_config, migration_modules)
        if module_path is None:
            continue
        if not isinstance(module_path, str):
            warnings.append(
                f"Could not inspect migrations for app '{app_config.label}': "
                f"MIGRATION_MODULES value must be a string or None"
            )
            continue
        try:
            migration_names = _migration_names_from_module(module_path)
        except ModuleNotFoundError as exc:
            if is_configured:
                warnings.append(f"Could not inspect migrations for app '{app_config.label}' at '{module_path}': {exc}")
            continue
        except (ImportError, OSError, ValueError) as exc:
            warnings.append(f"Could not inspect migrations for app '{app_config.label}' at '{module_path}': {exc}")
            continue
        if migration_names:
            migrations[app_config.label] = migration_names
    return migrations, warnings


def _collect_commands(
    commands_map: dict[str, str],
) -> tuple[dict[str, str], dict[str, list[str]], dict[str, dict[str, str]], list[str]]:
    """Inspect each command class and collect help text, options, and warnings.

    Returns (command_help, command_options, command_option_descriptions, warnings).
    """
    command_help: dict[str, str] = {}
    command_options: dict[str, list[str]] = {}
    command_option_descriptions: dict[str, dict[str, str]] = {}
    warnings: list[str] = []

    for cmd_name, app_name in commands_map.items():
        try:
            cmd = management.load_command_class(app_name, cmd_name)
            command_help[cmd_name] = cmd.help or ""
            parser = cmd.create_parser("manage.py", cmd_name)
            opts: list[str] = []
            option_descriptions: dict[str, str] = {}
            for action in parser._actions:
                opts.extend(s for s in action.option_strings if s.startswith("-"))
                help_text = "" if action.help is None else str(action.help)
                for opt in action.option_strings:
                    if opt.startswith("-"):
                        option_descriptions[opt] = help_text
            command_options[cmd_name] = sorted(set(opts))
            command_option_descriptions[cmd_name] = {
                opt: option_descriptions.get(opt, "") for opt in command_options[cmd_name]
            }
        except Exception as exc:
            command_help[cmd_name] = ""
            command_options[cmd_name] = []
            command_option_descriptions[cmd_name] = {}
            warnings.append(f"Could not inspect command '{cmd_name}': {exc}")

    return command_help, command_options, command_option_descriptions, warnings


def build_cache() -> CacheData:
    commands_map = management.get_commands()
    command_names = sorted(commands_map.keys())

    app_configs = list(apps.get_app_configs())
    app_labels: list[AppLabelEntry] = [{"label": cfg.label, "origin": classify_app(cfg)} for cfg in app_configs]
    app_labels.sort(key=lambda entry: (entry["origin"] != "local", entry["label"]))

    migration_modules = getattr(settings, "MIGRATION_MODULES", {}) or {}
    migrations, migration_warnings = _discover_migrations(app_configs, migration_modules)

    command_help, command_options, command_option_descriptions, command_warnings = _collect_commands(commands_map)

    return {
        "schema_version": 2,
        "commands": command_names,
        "app_labels": app_labels,
        "command_help": command_help,
        "command_options": command_options,
        "command_option_descriptions": command_option_descriptions,
        "migrations": migrations,
        "warnings": migration_warnings + command_warnings,
        "generated_at": time.time(),
    }


def write_cache(data: Mapping[str, Any], path: Path | None = None) -> None:
    if path is None:
        path = _cache_path()
    path.write_text(json.dumps(data, indent=2))


def read_cache(path: Path | None = None) -> dict | None:
    if path is None:
        path = _cache_path()
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def is_stale(cache: dict, cooldown_seconds: int = COOLDOWN_SECONDS) -> bool:
    return (time.time() - cache.get("generated_at", 0)) > cooldown_seconds


def maybe_refresh_cache() -> bool:
    """Rebuild and persist the cache if stale or missing; returns True if the cache was refreshed."""
    path = _cache_path()
    cache = read_cache(path)
    if cache is not None and not is_stale(cache):
        return False
    if not _refresh_lock.acquire(blocking=False):
        return False
    try:
        data = build_cache()
        write_cache(data, path)
        return True
    finally:
        _refresh_lock.release()
