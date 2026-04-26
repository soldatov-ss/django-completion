import threading
from typing import Any, cast
import warnings

from django.apps import AppConfig


class DjangoCompletionConfig(AppConfig):
    name = "django_completion"

    def ready(self):
        from django.core.management.base import BaseCommand

        from django_completion.cache import maybe_refresh_cache

        base_command = cast(Any, BaseCommand)
        if getattr(base_command, "_django_completion_patched", False):
            return

        original_execute = BaseCommand.execute

        def refresh_safely():
            try:
                maybe_refresh_cache()
            except Exception as exc:
                warnings.warn(f"django-completion cache refresh failed: {exc}", RuntimeWarning, stacklevel=2)

        def patched_execute(cmd_self: BaseCommand, *args: Any, **kwargs: Any) -> Any:
            try:
                return original_execute(cmd_self, *args, **kwargs)
            finally:
                from django.conf import settings

                if getattr(settings, "DJANGO_COMPLETION_AUTO_REFRESH", True):
                    thread = threading.Thread(target=refresh_safely, name="django-completion-refresh")
                    thread.start()

        base_command.execute = patched_execute
        base_command._django_completion_patched = True
