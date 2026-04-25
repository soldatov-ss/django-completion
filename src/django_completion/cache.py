import json
import time
from pathlib import Path

CACHE_FILENAME = ".django-completion-cache.json"
COOLDOWN_SECONDS = 60


def _cache_path() -> Path:
    try:
        from django.conf import settings

        if hasattr(settings, "BASE_DIR"):
            return Path(settings.BASE_DIR) / CACHE_FILENAME
    except Exception:
        pass
    return Path.cwd() / CACHE_FILENAME


def build_cache() -> dict:
    from django.apps import apps
    from django.core import management

    from django_completion.classify import classify_app

    commands_map = management.get_commands()
    command_names = sorted(commands_map.keys())

    app_labels = [
        {"label": cfg.label, "origin": classify_app(cfg)}
        for cfg in apps.get_app_configs()
    ]

    command_options: dict[str, list[str]] = {}
    for cmd_name, app_name in commands_map.items():
        try:
            cmd = management.load_command_class(app_name, cmd_name)
            parser = cmd.create_parser("manage.py", cmd_name)
            opts: list[str] = []
            for action in parser._actions:
                opts.extend(s for s in action.option_strings if s.startswith("-"))
            command_options[cmd_name] = sorted(set(opts))
        except Exception:
            command_options[cmd_name] = []

    return {
        "commands": command_names,
        "app_labels": app_labels,
        "command_options": command_options,
        "generated_at": time.time(),
    }


def write_cache(data: dict, path: Path | None = None) -> None:
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


def maybe_refresh_cache() -> None:
    path = _cache_path()
    cache = read_cache(path)
    if cache is not None and not is_stale(cache):
        return
    try:
        data = build_cache()
        write_cache(data, path)
    except Exception:
        pass
