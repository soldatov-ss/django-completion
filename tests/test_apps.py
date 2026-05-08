import logging
import threading

import pytest

from django_completion.apps import _make_execute_hook, _refresh_safely


def test_hook_calls_refresh_fn_after_execute(settings):
    settings.DJANGO_COMPLETION_AUTO_REFRESH = True
    called = threading.Event()
    hook = _make_execute_hook(lambda self, *a, **kw: "result", lambda: called.set())
    result = hook(None)
    assert called.wait(timeout=1), "refresh_fn was not called"
    assert result == "result"


def test_hook_skips_refresh_when_disabled(settings):
    settings.DJANGO_COMPLETION_AUTO_REFRESH = False
    called = threading.Event()
    hook = _make_execute_hook(lambda self, *a, **kw: None, lambda: called.set())
    hook(None)
    assert not called.wait(timeout=0.1), "refresh_fn should not have been called"


def test_hook_fires_refresh_even_when_execute_raises(settings):
    settings.DJANGO_COMPLETION_AUTO_REFRESH = True
    called = threading.Event()

    def raising_execute(self, *a, **kw):
        raise RuntimeError("command failed")

    hook = _make_execute_hook(raising_execute, lambda: called.set())
    with pytest.raises(RuntimeError, match="command failed"):
        hook(None)
    assert called.wait(timeout=1), "refresh_fn should fire even after execute raises"


def test_refresh_safely_does_not_propagate_exceptions(monkeypatch):
    from django_completion import cache

    def raise_error():
        raise RuntimeError("oops")

    monkeypatch.setattr(cache, "maybe_refresh_cache", raise_error)
    _refresh_safely()  # must not raise


def test_refresh_safely_logs_exception(monkeypatch, caplog):
    from django_completion import cache

    def raise_error():
        raise RuntimeError("oops")

    monkeypatch.setattr(cache, "maybe_refresh_cache", raise_error)
    with caplog.at_level(logging.WARNING, logger="django_completion"):
        _refresh_safely()
    assert "oops" in caplog.text
