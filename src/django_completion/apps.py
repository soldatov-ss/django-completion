import logging
import threading
from typing import Any, cast

from django.apps import AppConfig

_logger = logging.getLogger("django_completion")


def _refresh_safely() -> None:
    try:
        from django_completion.cache import maybe_refresh_cache

        maybe_refresh_cache()
    except Exception as exc:
        _logger.warning("cache refresh failed: %s", exc)


def _make_execute_hook(original_execute, refresh_fn):
    """Return a patched BaseCommand.execute that calls refresh_fn in a background thread."""

    def patched(cmd_self: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return original_execute(cmd_self, *args, **kwargs)
        finally:
            from django.conf import settings

            if getattr(settings, "DJANGO_COMPLETION_AUTO_REFRESH", True):
                thread = threading.Thread(target=refresh_fn, name="django-completion-refresh")
                thread.start()

    return patched


class DjangoCompletionConfig(AppConfig):
    name = "django_completion"

    def ready(self):
        from django.core.management.base import BaseCommand

        base_command = cast(Any, BaseCommand)
        if getattr(base_command, "_django_completion_patched", False):
            return

        original_execute = BaseCommand.execute
        base_command.execute = _make_execute_hook(original_execute, _refresh_safely)
        base_command._django_completion_patched = True
