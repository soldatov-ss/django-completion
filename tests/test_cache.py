import time

from django.core import management
import pytest

from django_completion.cache import _collect_commands, build_cache, is_stale, read_cache, write_cache


@pytest.mark.django_db
def test_build_cache_structure():
    data = build_cache()
    assert data["schema_version"] == 2
    assert "commands" in data
    assert "app_labels" in data
    assert "command_help" in data
    assert "command_options" in data
    assert "command_option_descriptions" in data
    assert "migrations" in data
    assert "warnings" in data
    assert "generated_at" in data
    assert isinstance(data["commands"], list)
    assert isinstance(data["migrations"], dict)
    assert isinstance(data["warnings"], list)
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
def test_build_cache_app_labels_local_first(settings, tmp_path):
    settings.BASE_DIR = str(tmp_path)
    data = build_cache()
    origins = [entry["origin"] for entry in data["app_labels"]]
    assert origins == sorted(origins, key=lambda origin: origin != "local")


@pytest.mark.django_db
def test_build_cache_command_options():
    data = build_cache()
    # migrate should have --fake option
    migrate_opts = data["command_options"].get("migrate", [])
    assert "--fake" in migrate_opts


@pytest.mark.django_db
def test_build_cache_command_descriptions():
    data = build_cache()
    assert isinstance(data["command_help"].get("migrate"), str)
    assert isinstance(data["command_option_descriptions"].get("migrate", {}).get("--fake"), str)


@pytest.mark.django_db
def test_build_cache_discovers_django_builtin_migrations():
    data = build_cache()
    assert "auth" in data["migrations"]
    assert "contenttypes" in data["migrations"]
    assert "sessions" in data["migrations"]
    assert "0001_initial" in data["migrations"]["auth"]
    assert all(not migration.endswith(".py") for migration in data["migrations"]["auth"])


@pytest.mark.django_db
def test_build_cache_respects_disabled_migration_module(settings):
    settings.MIGRATION_MODULES = {"auth": None}

    data = build_cache()

    assert "auth" not in data["migrations"]
    assert "contenttypes" in data["migrations"]


@pytest.mark.django_db
def test_build_cache_warns_for_uninspectable_migration_module(settings):
    settings.MIGRATION_MODULES = {"auth": "nonexistent.module"}

    data = build_cache()

    assert "auth" not in data["migrations"]
    assert any("auth" in warning and "nonexistent.module" in warning for warning in data["warnings"])


@pytest.mark.django_db
def test_build_cache_does_not_warn_for_apps_without_default_migrations():
    data = build_cache()

    assert all("django_completion" not in warning for warning in data["warnings"])


@pytest.mark.django_db
def test_build_cache_discovers_custom_migration_module_and_filters_files(settings, tmp_path, monkeypatch):
    migrations_dir = tmp_path / "custom_auth_migrations"
    migrations_dir.mkdir()
    (migrations_dir / "__init__.py").write_text("")
    (migrations_dir / "0002_second.py").write_text("")
    (migrations_dir / "0001_initial.py").write_text("")
    (migrations_dir / "_private.py").write_text("")
    (migrations_dir / ".hidden.py").write_text("")
    (migrations_dir / "README.md").write_text("")
    (migrations_dir / "__pycache__").mkdir()
    monkeypatch.syspath_prepend(str(tmp_path))
    settings.MIGRATION_MODULES = {"auth": "custom_auth_migrations"}

    data = build_cache()

    assert data["migrations"]["auth"] == ["0001_initial", "0002_second"]


@pytest.mark.django_db
def test_build_cache_warns_for_uninspectable_command(monkeypatch):
    original_load = management.load_command_class

    def broken_load(app_name, cmd_name):
        if cmd_name == "migrate":
            raise RuntimeError("simulated import failure")
        return original_load(app_name, cmd_name)

    monkeypatch.setattr(management, "load_command_class", broken_load)
    data = build_cache()

    assert any("migrate" in w and "simulated import failure" in w for w in data["warnings"])
    assert data["command_options"]["migrate"] == []
    assert "migrate" in data["commands"]


# --- 0.2.8-2: _collect_commands() ---


def test_collect_commands_returns_four_dicts():
    commands_map = management.get_commands()
    help_, options, descriptions, warnings = _collect_commands(commands_map)
    assert isinstance(help_, dict)
    assert isinstance(options, dict)
    assert isinstance(descriptions, dict)
    assert isinstance(warnings, list)
    assert "migrate" in help_


def test_collect_commands_warns_for_broken_class(monkeypatch):
    original = management.load_command_class

    def broken(app_name, cmd_name):
        if cmd_name == "migrate":
            raise RuntimeError("simulated failure")
        return original(app_name, cmd_name)

    monkeypatch.setattr(management, "load_command_class", broken)
    _, options, _, warnings = _collect_commands(management.get_commands())
    assert any("migrate" in w and "simulated failure" in w for w in warnings)
    assert options["migrate"] == []


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
