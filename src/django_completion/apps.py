import threading

from django.apps import AppConfig


class DjangoCompletionConfig(AppConfig):
    name = "django_completion"

    def ready(self):
        from django.core.management.base import BaseCommand

        from django_completion.cache import maybe_refresh_cache

        original_execute = BaseCommand.execute

        def patched_execute(cmd_self, *args, **kwargs):
            result = original_execute(cmd_self, *args, **kwargs)
            thread = threading.Thread(target=maybe_refresh_cache, daemon=True)
            thread.start()
            return result

        BaseCommand.execute = patched_execute
