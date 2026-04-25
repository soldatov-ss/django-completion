import json
import time
from pathlib import Path

import pytest

from django_completion.cache import (
    COOLDOWN_SECONDS,
    build_cache,
    is_stale,
    read_cache,
    write_cache,
)


@pytest.mark.django_db
def test_build_cache_structure():
    data = build_cache()
    assert "commands" in data
    assert "app_labels" in data
    assert "command_options" in data
    assert "generated_at" in data
    assert isinstance(data["commands"], list)
    assert len(data["commands"]) > 0


@pytest.mark.django_db
def test_build_cache_contains_known_command():
    data = build_cache()
    assert "migrate" in data["commands"]


@pytest.mark.django_db
def test_build_cache_app_labels_have_origin():
    data = build_cache()
    for entry in data["app_labels"]:
        assert "label" in entry
        assert entry["origin"] in ("local", "pip")


@pytest.mark.django_db
def test_build_cache_command_options():
    data = build_cache()
    # migrate should have --fake option
    migrate_opts = data["command_options"].get("migrate", [])
    assert "--fake" in migrate_opts


def test_write_and_read_cache(tmp_path):
    path = tmp_path / "cache.json"
    data = {"commands": ["migrate"], "app_labels": [], "command_options": {}, "generated_at": time.time()}
    write_cache(data, path)
    result = read_cache(path)
    assert result is not None
    assert result["commands"] == ["migrate"]


def test_read_cache_missing_file(tmp_path):
    assert read_cache(tmp_path / "nonexistent.json") is None


def test_read_cache_corrupt_file(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text("not valid json")
    assert read_cache(path) is None


def test_is_stale_fresh():
    cache = {"generated_at": time.time()}
    assert not is_stale(cache, cooldown_seconds=60)


def test_is_stale_old():
    cache = {"generated_at": time.time() - 120}
    assert is_stale(cache, cooldown_seconds=60)


def test_is_stale_no_timestamp():
    assert is_stale({}, cooldown_seconds=60)
