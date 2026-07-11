from io import StringIO
import json

from django.core.management import call_command
from django.core.management.base import CommandError
import pytest

from django_completion.management.commands.autocomplete import _format_delta, _render_context


@pytest.mark.django_db
def test_autocomplete_wrong_subcommand_suggests_correction():
    """Wrong subcommand error message includes 'Did you mean?'."""
    from django_completion.management.commands.autocomplete import Command

    cmd = Command()
    parser = cmd.create_parser("manage.py", "autocomplete")

    # In programmatic (non-CLI) mode, parser.error raises CommandError.
    with pytest.raises(CommandError) as exc_info:
        parser.parse_args(["states"])

    assert "did you mean" in str(exc_info.value).lower()
    assert "status" in str(exc_info.value)


@pytest.mark.django_db
def test_autocomplete_completely_wrong_subcommand_no_suggestion():
    """An unrelated subcommand still produces an error, just without a suggestion."""
    from django_completion.management.commands.autocomplete import Command

    cmd = Command()
    parser = cmd.create_parser("manage.py", "autocomplete")

    with pytest.raises(CommandError) as exc_info:
        parser.parse_args(["xyzzy"])

    assert "invalid choice" in str(exc_info.value).lower()
    assert "did you mean" not in str(exc_info.value).lower()


# --- 0.2.5-1: shell detection ---


def test_detect_shell_uses_zsh_version(monkeypatch):
    monkeypatch.setenv("ZSH_VERSION", "5.9")
    monkeypatch.delenv("BASH_VERSION", raising=False)
    monkeypatch.setenv("SHELL", "/bin/bash")  # $SHELL says bash — should be ignored
    from importlib import reload

    import django_completion.management.commands.autocomplete as mod

    reload(mod)
    assert mod._detect_shell() == "zsh"


def test_detect_shell_uses_bash_version(monkeypatch):
    monkeypatch.delenv("ZSH_VERSION", raising=False)
    monkeypatch.setenv("BASH_VERSION", "5.2.0")
    monkeypatch.setenv("SHELL", "/bin/zsh")  # $SHELL says zsh — should be ignored
    from importlib import reload

    import django_completion.management.commands.autocomplete as mod

    reload(mod)
    assert mod._detect_shell() == "bash"


def test_detect_shell_falls_back_to_shell_env(monkeypatch):
    monkeypatch.delenv("ZSH_VERSION", raising=False)
    monkeypatch.delenv("BASH_VERSION", raising=False)
    monkeypatch.setenv("SHELL", "/usr/bin/zsh")
    from importlib import reload

    import django_completion.management.commands.autocomplete as mod

    reload(mod)
    assert mod._detect_shell() == "zsh"


# --- 0.2.5-1: source reminder after re-install ---


@pytest.mark.django_db
def test_install_shows_source_reminder_when_already_installed(tmp_path, monkeypatch):
    """Re-running install when hook is already present still prints the source reminder."""
    from io import StringIO

    from django.core.management import call_command

    rc_file = tmp_path / ".bashrc"
    install_dir = tmp_path / "django-completion"

    monkeypatch.setattr(
        "django_completion.management.commands.autocomplete._SHELL_RC",
        {"bash": rc_file, "zsh": tmp_path / ".zshrc"},
    )
    monkeypatch.setattr(
        "django_completion.management.commands.autocomplete._INSTALL_DIR",
        install_dir,
    )
    monkeypatch.setenv("BASH_VERSION", "5.2")
    monkeypatch.delenv("ZSH_VERSION", raising=False)

    # First install — adds the hook block
    out1 = StringIO()
    call_command("autocomplete", "install", stdout=out1)
    assert "source" in out1.getvalue()

    # Second install — hook already present, should still show source reminder
    out2 = StringIO()
    call_command("autocomplete", "install", stdout=out2)
    output2 = out2.getvalue()
    assert "source" in output2
    assert "Script updated" in output2


def test_detect_shell_bash_wins_when_both_set(monkeypatch):
    """bash spawned inside zsh inherits $ZSH_VERSION — $BASH_VERSION must win."""
    monkeypatch.setenv("ZSH_VERSION", "5.9.0")  # inherited from parent zsh
    monkeypatch.setenv("BASH_VERSION", "5.2.21")  # set by the running bash
    monkeypatch.setenv("SHELL", "/usr/bin/zsh")  # login shell (also misleading)
    from importlib import reload

    import django_completion.management.commands.autocomplete as mod

    reload(mod)
    assert mod._detect_shell() == "bash"


# --- 0.2.8-1: refresh delta output ---


def test_format_delta_positive():
    assert _format_delta(98, 96) == " (+2)"


def test_format_delta_negative():
    assert _format_delta(95, 96) == " (-1)"


def test_format_delta_no_change():
    assert _format_delta(96, 96) == ""


def test_format_delta_no_old():
    assert _format_delta(96, None) == ""


@pytest.mark.django_db
def test_refresh_output_shows_totals(tmp_path, monkeypatch):
    monkeypatch.setattr("django_completion.management.commands.autocomplete._INSTALL_DIR", tmp_path / "install")
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(tmp_path / "cache.json"))

    out = StringIO()
    call_command("autocomplete", "refresh", stdout=out)
    output = out.getvalue()

    assert "Cache rebuilt:" in output
    assert "commands" in output
    assert "apps" in output


@pytest.mark.django_db
def test_refresh_output_shows_no_delta_on_first_run(tmp_path, monkeypatch):
    cache_path = tmp_path / "cache.json"
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(cache_path))

    out = StringIO()
    call_command("autocomplete", "refresh", stdout=out)
    output = out.getvalue()

    # No prior cache → no delta in parentheses
    assert "(+" not in output
    assert "(-" not in output


@pytest.mark.django_db
def test_refresh_output_no_warning_suffix_when_no_warnings(tmp_path, monkeypatch, settings):
    cache_path = tmp_path / "cache.json"
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(cache_path))

    out = StringIO()
    call_command("autocomplete", "refresh", stdout=out)

    assert "warning" not in out.getvalue().lower()


# --- 0.3.0: autocomplete context ---


def _context_cache():
    return {
        "schema_version": 2,
        "commands": ["check", "import_articles", "migrate"],
        "app_labels": [
            {"label": "blog", "origin": "local"},
            {"label": "auth", "origin": "pip"},
        ],
        "command_apps": {"check": "django.core", "import_articles": "blog", "migrate": "django.core"},
        "command_help": {"check": "", "import_articles": "Import articles from a feed.", "migrate": ""},
        "command_options": {
            "check": [],
            "import_articles": ["--dry-run", "--help", "--limit", "--settings", "--verbosity", "-h", "-v"],
            "migrate": ["--fake"],
        },
        "command_option_descriptions": {},
        "migrations": {"blog": ["0001_initial", "0002_add_slug"]},
        "warnings": [],
        "generated_at": 1751000000.0,
    }


def test_render_context_local_command_with_help_and_own_flags():
    out = _render_context(_context_cache())
    assert "- import_articles — Import articles from a feed." in out
    assert "--dry-run" in out
    assert "--limit" in out


def test_render_context_strips_global_flags():
    out = _render_context(_context_cache())
    assert "--settings" not in out
    assert "--verbosity" not in out


def test_render_context_sections_and_classification():
    out = _render_context(_context_cache())
    assert out.startswith("# manage.py — 3 commands")
    assert "## Project commands [local]" in out
    assert "- blog: 0001_initial, 0002_add_slug" in out
    # built-ins land in the compact section, not under project commands
    local_section = out.split("## Migrations on disk")[0]
    assert "migrate" not in local_section
    assert "check, migrate" in out


def test_render_context_empty_sections():
    cache = _context_cache()
    cache["app_labels"] = [{"label": "auth", "origin": "pip"}]
    cache["migrations"] = {}
    out = _render_context(cache)
    assert out.count("(none found)") == 2


@pytest.mark.django_db
def test_context_json_round_trips(tmp_path, monkeypatch):
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(tmp_path / "cache.json"))

    out = StringIO()
    call_command("autocomplete", "context", "--json", stdout=out)
    data = json.loads(out.getvalue())

    assert data["schema_version"] == 2
    assert data["command_apps"]["migrate"] == "django.core"


@pytest.mark.django_db
def test_context_markdown_output(tmp_path, monkeypatch):
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(tmp_path / "cache.json"))

    out = StringIO()
    call_command("autocomplete", "context", stdout=out)
    output = out.getvalue()

    assert output.startswith("# manage.py — ")
    assert "## Project commands [local]" in output
    assert "## Migrations on disk" in output
    assert "## Built-in and third-party commands" in output
    assert "migrate" in output


@pytest.mark.django_db
def test_context_respects_cooldown_and_refresh_flag(tmp_path, monkeypatch):
    cache_path = tmp_path / "cache.json"
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(cache_path))
    call_command("autocomplete", "refresh", stdout=StringIO())
    first = json.loads(cache_path.read_text())["generated_at"]

    # Fresh cache within the cooldown — context must not rewrite it.
    call_command("autocomplete", "context", stdout=StringIO())
    assert json.loads(cache_path.read_text())["generated_at"] == first

    call_command("autocomplete", "context", "--refresh", stdout=StringIO())
    assert json.loads(cache_path.read_text())["generated_at"] > first


@pytest.mark.django_db
def test_context_rebuilds_cache_missing_command_apps(tmp_path, monkeypatch):
    """A fresh pre-0.3.0 cache (no command_apps) is rebuilt rather than misclassified."""
    import time

    cache_path = tmp_path / "cache.json"
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(cache_path))
    old = _context_cache()
    del old["command_apps"]
    old["generated_at"] = time.time()
    cache_path.write_text(json.dumps(old))

    out = StringIO()
    call_command("autocomplete", "context", "--json", stdout=out)

    assert "command_apps" in json.loads(out.getvalue())
    assert "command_apps" in json.loads(cache_path.read_text())


@pytest.mark.django_db
@pytest.mark.parametrize("field", ["commands", "migrations", "command_apps", "generated_at"])
def test_context_rebuilds_hand_edited_cache_with_null_field(tmp_path, monkeypatch, field):
    """Valid JSON with a field nulled out is rebuilt, not a traceback."""
    import time

    cache_path = tmp_path / "cache.json"
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(cache_path))
    broken = _context_cache()
    broken["generated_at"] = time.time()
    broken[field] = None
    cache_path.write_text(json.dumps(broken))

    out = StringIO()
    call_command("autocomplete", "context", stdout=out)

    assert out.getvalue().startswith("# manage.py — ")
    assert json.loads(cache_path.read_text())[field] is not None


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("app_labels", ["blog"]),
        ("migrations", {"blog": None}),
        ("command_options", {"import_articles": None}),
        ("command_apps", {"import_articles": None}),
        ("command_help", {"import_articles": None}),
        ("commands", [None]),
    ],
    ids=[
        "app_labels-str-entries",
        "migrations-null-value",
        "command_options-null-value",
        "command_apps-null-value",
        "command_help-null-value",
        "commands-null-entry",
    ],
)
def test_context_rebuilds_cache_with_element_level_corruption(tmp_path, monkeypatch, field, value):
    """A container of the right type but wrong-typed elements is rebuilt, not a traceback."""
    import time

    cache_path = tmp_path / "cache.json"
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(cache_path))
    broken = _context_cache()
    broken["generated_at"] = time.time()
    broken[field] = value
    cache_path.write_text(json.dumps(broken))

    out = StringIO()
    call_command("autocomplete", "context", stdout=out)

    assert out.getvalue().startswith("# manage.py — ")


@pytest.mark.django_db
@pytest.mark.parametrize("raw", ["[]", '"hi"', "42"])
def test_context_rebuilds_when_cache_file_is_not_a_json_object(tmp_path, monkeypatch, raw):
    """Valid JSON that isn't even an object (list/string/number) is rebuilt, not a traceback."""
    cache_path = tmp_path / "cache.json"
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(cache_path))
    cache_path.write_text(raw)

    out = StringIO()
    call_command("autocomplete", "context", stdout=out)

    assert out.getvalue().startswith("# manage.py — ")


@pytest.mark.django_db
@pytest.mark.parametrize(
    "literal",
    ["NaN", "Infinity", "-Infinity", "1" + "0" * 400, "1751976000000", "-1"],
    ids=["nan", "inf", "-inf", "huge-int", "ms-epoch", "negative"],
)
def test_context_rebuilds_when_generated_at_is_unusable(tmp_path, monkeypatch, literal):
    """Non-finite or out-of-range timestamps must not reach arithmetic or fromtimestamp."""
    import re
    import time

    cache_path = tmp_path / "cache.json"
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(cache_path))
    broken = _context_cache()
    text = re.sub(r'"generated_at":\s*[0-9.]+', f'"generated_at": {literal}', json.dumps(broken))
    cache_path.write_text(text)

    out = StringIO()
    call_command("autocomplete", "context", stdout=out)

    assert out.getvalue().startswith("# manage.py — ")
    new_generated_at = json.loads(cache_path.read_text())["generated_at"]
    assert new_generated_at > time.time() - 60


@pytest.mark.django_db
@pytest.mark.parametrize("literal", ["NaN", "1" + "0" * 400], ids=["nan", "huge-int"])
def test_status_survives_corrupt_generated_at(tmp_path, monkeypatch, literal):
    """status reads the cache without the context gate; corrupt timestamps must not crash it."""
    cache_path = tmp_path / "cache.json"
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(cache_path))
    cache_path.write_text(
        f'{{"generated_at": {literal}, "commands": [], "app_labels": [], "migrations": {{}}, "warnings": []}}'
    )

    call_command("autocomplete", "status", stdout=StringIO())

    out = StringIO()
    call_command("autocomplete", "status", "--verbose", stdout=out)
    assert "Generated: unknown" in out.getvalue()


@pytest.mark.django_db
def test_context_survives_permission_error_on_write(tmp_path, monkeypatch):
    """A read-only cache directory must not crash context — it still prints the freshly built summary."""
    cache_path = tmp_path / "cache.json"
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(cache_path))

    def _raise(*args, **kwargs):
        raise PermissionError("read-only filesystem")

    monkeypatch.setattr("django_completion.cache.write_cache", _raise)

    out = StringIO()
    err = StringIO()
    call_command("autocomplete", "context", stdout=out, stderr=err)

    assert out.getvalue().startswith("# manage.py — ")
    assert "cache not written" in err.getvalue()


@pytest.mark.django_db
def test_context_does_not_write_when_auto_refresh_disabled(tmp_path, monkeypatch, settings):
    cache_path = tmp_path / "cache.json"
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(cache_path))
    settings.DJANGO_COMPLETION_AUTO_REFRESH = False

    out = StringIO()
    call_command("autocomplete", "context", stdout=out)

    assert out.getvalue().startswith("# manage.py — ")
    assert not cache_path.exists()


@pytest.mark.django_db
def test_context_refresh_flag_writes_even_when_auto_refresh_disabled(tmp_path, monkeypatch, settings):
    cache_path = tmp_path / "cache.json"
    monkeypatch.setattr("django_completion.cache.CACHE_FILENAME", str(cache_path))
    settings.DJANGO_COMPLETION_AUTO_REFRESH = False

    out = StringIO()
    call_command("autocomplete", "context", "--refresh", stdout=out)

    assert cache_path.exists()


@pytest.mark.parametrize(
    "help_text",
    ["Import stuff.\n\n## Notes\n- reads FEED_URL", "\nImport stuff.\n"],
    ids=["multiline", "leading-newline"],
)
def test_render_context_uses_first_nonempty_help_line(help_text):
    cache = _context_cache()
    cache["command_help"]["import_articles"] = help_text
    out = _render_context(cache)
    assert "- import_articles — Import stuff." in out
    assert "## Notes" not in out
    assert "reads FEED_URL" not in out


def test_render_context_shows_warning_summary():
    cache = _context_cache()
    cache["warnings"] = ["Could not inspect command 'broken_cmd': ImportError"]
    out = _render_context(cache)
    assert "> 1 warning — run" in out


def test_render_context_no_warning_banner_when_clean():
    out = _render_context(_context_cache())
    assert "warning" not in out.lower()


def test_render_context_migrations_filtered_to_local_apps():
    cache = _context_cache()
    cache["migrations"]["auth"] = ["0001_initial"]  # auth is origin "pip" in the fixture
    out = _render_context(cache)
    assert "auth:" not in out
    assert "blog:" in out
