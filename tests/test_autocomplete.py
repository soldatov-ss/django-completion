from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
import pytest

from django_completion.management.commands.autocomplete import _format_delta


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
