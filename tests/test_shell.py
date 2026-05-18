"""Subprocess-based shell completion tests (Step 8)."""

import io
import json
from pathlib import Path
import shutil
import subprocess

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "src/django_completion/scripts"
BASH_SCRIPT = SCRIPTS_DIR / "bash_completion.sh.tmpl"
ZSH_SCRIPT = SCRIPTS_DIR / "zsh_completion.zsh.tmpl"


@pytest.fixture
def cache_dir(tmp_path):
    """A temp directory containing a pre-built completion cache."""
    data = {
        "schema_version": 2,
        "commands": ["migrate", "runserver", "shell", "makemigrations", "startapp"],
        "command_help": {
            "migrate": "Updates database schema",
            "runserver": "Starts a development server",
        },
        "app_labels": [
            {"label": "myapp", "origin": "local"},
            {"label": "auth", "origin": "pip"},
        ],
        "command_options": {
            "migrate": ["--fake", "--fake-initial", "--database", "--run-syncdb"],
            "runserver": ["--noreload", "--nothreading", "--ipv6"],
        },
        "command_option_descriptions": {
            "migrate": {
                "--fake": "Mark migrations as run",
                "--fake-initial": "Detect initial migrations",
                "--database": "Database to migrate",
                "--run-syncdb": "Create tables for apps without migrations",
            }
        },
        "migrations": {
            "myapp": ["0001_initial", "0002_add_user"],
            "auth": ["0001_initial"],
        },
        "warnings": [],
        "generated_at": 9_999_999_999,
    }
    (tmp_path / ".django-completion-cache.json").write_text(json.dumps(data))
    return tmp_path


def _bash_complete(
    cache_dir: Path, comp_words: list[str], comp_cword: int, func: str = "_django_manage_completion"
) -> list[str]:
    words_str = " ".join(f'"{w}"' for w in comp_words)
    result = subprocess.run(
        [
            "bash",
            "-c",
            f"""
source {BASH_SCRIPT}
cd {cache_dir}
COMP_WORDS=({words_str})
COMP_CWORD={comp_cword}
{func}
echo "${{COMPREPLY[@]}}"
""",
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    raw = result.stdout.strip()
    return raw.split() if raw else []


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_completes_commands(cache_dir):
    completions = _bash_complete(cache_dir, ["manage.py", ""], 1)
    assert "migrate" in completions
    assert "runserver" in completions
    assert "shell" in completions


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_filters_by_prefix(cache_dir):
    completions = _bash_complete(cache_dir, ["manage.py", "mig"], 1)
    assert "migrate" in completions
    assert "runserver" not in completions
    assert "makemigrations" not in completions  # starts with "mak", not "mig"

    completions_mak = _bash_complete(cache_dir, ["manage.py", "mak"], 1)
    assert "makemigrations" in completions_mak
    assert "migrate" not in completions_mak


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_completes_options(cache_dir):
    completions = _bash_complete(cache_dir, ["manage.py", "migrate", "--"], 2)
    assert "--fake" in completions
    assert "--database" in completions


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_runserver_completes_options_only(cache_dir):
    completions = _bash_complete(cache_dir, ["manage.py", "runserver", ""], 2)
    assert "myapp" not in completions
    assert "auth" not in completions
    assert "--noreload" in completions


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_migrate_completes_migration_apps(cache_dir):
    completions = _bash_complete(cache_dir, ["manage.py", "migrate", ""], 2)
    assert "myapp" in completions
    assert "auth" in completions
    assert "--fake" not in completions


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_migrate_completes_migration_names(cache_dir):
    completions = _bash_complete(cache_dir, ["manage.py", "migrate", "myapp", ""], 3)
    assert "0001_initial" in completions
    assert "0002_add_user" in completions
    assert "zero" in completions


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_filters_options_when_prefix_is_dash(cache_dir):
    completions = _bash_complete(cache_dir, ["manage.py", "migrate", "--f"], 2)
    assert "--fake" in completions
    assert "myapp" not in completions


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_no_cache_returns_nothing(tmp_path):
    # tmp_path has no cache file — walk up should find nothing
    completions = _bash_complete(tmp_path, ["manage.py", ""], 1)
    assert completions == []


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_python_manage_completes_commands(cache_dir):
    completions = _bash_complete(cache_dir, ["python", "manage.py", ""], 2, "_django_python_completion")
    assert "migrate" in completions
    assert "runserver" in completions


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_python3_manage_completes_commands(cache_dir):
    completions = _bash_complete(cache_dir, ["python3", "manage.py", ""], 2, "_django_python_completion")
    assert "migrate" in completions
    assert "runserver" in completions


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_python_manage_completes_options(cache_dir):
    completions = _bash_complete(cache_dir, ["python", "manage.py", "migrate", ""], 3, "_django_python_completion")
    assert "myapp" in completions
    assert "auth" in completions
    assert "--fake" not in completions


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_python_manage_migrate_completes_migration_names(cache_dir):
    completions = _bash_complete(
        cache_dir,
        ["python", "manage.py", "migrate", "myapp", ""],
        4,
        "_django_python_completion",
    )
    assert "0001_initial" in completions
    assert "0002_add_user" in completions
    assert "zero" in completions


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_python_without_manage_returns_nothing(cache_dir):
    # python TAB with no manage.py — should not activate django completion
    completions = _bash_complete(cache_dir, ["python", ""], 1, "_django_python_completion")
    assert completions == []


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_uv_run_python_manage_completes_commands(cache_dir):
    completions = _bash_complete(cache_dir, ["uv", "run", "python", "manage.py", ""], 4, "_django_python_completion")
    assert "migrate" in completions
    assert "runserver" in completions


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_uv_run_python_manage_migrate_completes_migration_names(cache_dir):
    completions = _bash_complete(
        cache_dir,
        ["uv", "run", "python", "manage.py", "migrate", "myapp", ""],
        6,
        "_django_python_completion",
    )
    assert "0001_initial" in completions
    assert "0002_add_user" in completions
    assert "zero" in completions


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_empty_completions_do_not_leak_filenames(cache_dir):
    # Create files in the cache dir so filename fallback would produce results
    (cache_dir / "somefile.py").write_text("")
    (cache_dir / "other.txt").write_text("")
    # An unknown command has no cached options — helper returns nothing
    completions = _bash_complete(cache_dir, ["manage.py", "unknowncmd", ""], 2)
    assert completions == []


@pytest.mark.skipif(not shutil.which("zsh"), reason="zsh not available")
def test_zsh_script_sources_without_error(cache_dir):
    result = subprocess.run(
        ["zsh", "-c", f"source {ZSH_SCRIPT}; echo OK"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(cache_dir),
    )
    assert result.returncode == 0
    assert "OK" in result.stdout


def test_zsh_template_uses_descriptions():
    text = ZSH_SCRIPT.read_text()
    assert '_describe -t "$tag" "$description" candidates' in text
    assert '_django_complete_with_helper commands "django command"' in text
    assert '_django_complete_with_helper arguments "django argument"' in text


def test_bash_helper_is_invoked():
    text = BASH_SCRIPT.read_text()
    assert "django_completion._complete" in text
    assert "python3 -m django_completion._complete" in text
    assert "complete -o default -F _django_python_completion python python3 uv" in text


def test_zsh_helper_is_invoked():
    text = ZSH_SCRIPT.read_text()
    assert "django_completion._complete" in text
    assert "python3 -m django_completion._complete" in text
    assert "compdef _django_python_manage python python3 uv" in text


# ── Full integration: refresh command writes a valid cache ──────────────────


@pytest.mark.django_db
def test_autocomplete_refresh_writes_cache(tmp_path, settings):
    settings.BASE_DIR = str(tmp_path)

    from django.core.management import call_command

    out = io.StringIO()
    call_command("autocomplete", "refresh", stdout=out)

    cache_file = tmp_path / ".django-completion-cache.json"
    assert cache_file.exists(), "cache file not written"

    data = json.loads(cache_file.read_text())
    assert "migrate" in data["commands"]
    assert len(data["commands"]) > 5
    assert any(e["label"] == "django_completion" for e in data["app_labels"])


@pytest.mark.django_db
def test_autocomplete_refresh_output_message(tmp_path, settings):
    settings.BASE_DIR = str(tmp_path)

    from django.core.management import call_command

    out = io.StringIO()
    call_command("autocomplete", "refresh", stdout=out, no_color=True)
    message = out.getvalue()
    assert "commands" in message
    assert "apps" in message


@pytest.mark.django_db
def test_autocomplete_status_no_cache(tmp_path, settings):
    settings.BASE_DIR = str(tmp_path)

    from django.core.management import call_command

    out = io.StringIO()
    call_command("autocomplete", "status", stdout=out, no_color=True)
    assert "not found" in out.getvalue()


@pytest.mark.django_db
def test_autocomplete_status_with_cache(tmp_path, settings):
    settings.BASE_DIR = str(tmp_path)

    from django.core.management import call_command

    call_command("autocomplete", "refresh", stdout=io.StringIO())

    out = io.StringIO()
    call_command("autocomplete", "status", stdout=out, no_color=True)
    output = out.getvalue()
    assert "Commands:" in output
    assert "Apps:" in output


@pytest.fixture
def isolated_autocomplete_paths(tmp_path, monkeypatch):
    from django_completion.management.commands import autocomplete

    install_dir = tmp_path / "share" / "django-completion"
    bashrc = tmp_path / ".bashrc"
    zshrc = tmp_path / ".zshrc"
    bashrc.write_text("")
    zshrc.write_text("")

    monkeypatch.setattr(autocomplete, "_INSTALL_DIR", install_dir)
    monkeypatch.setattr(
        autocomplete,
        "_SHELL_RC",
        {
            "bash": bashrc,
            "zsh": zshrc,
        },
    )
    return autocomplete, install_dir, bashrc, zshrc


@pytest.mark.django_db
def test_autocomplete_install_writes_version_marker_and_status_current(tmp_path, settings, isolated_autocomplete_paths):
    settings.BASE_DIR = str(tmp_path)
    autocomplete, install_dir, _, _ = isolated_autocomplete_paths

    from django.core.management import call_command

    call_command("autocomplete", "install", "--shell", "bash", stdout=io.StringIO(), no_color=True)

    script_path = install_dir / "completion.bash"
    first_line = script_path.read_text().splitlines()[0]
    assert first_line == f"# django-completion version: {autocomplete._package_version()}"

    out = io.StringIO()
    call_command("autocomplete", "status", stdout=out, no_color=True)
    output = out.getvalue()
    assert "Schema: v2 (current)" in output
    assert "Apps with migrations:" in output
    assert "Warnings:" in output
    assert "bash script: current" in output


@pytest.mark.django_db
def test_autocomplete_status_reports_outdated_script(tmp_path, settings, isolated_autocomplete_paths):
    settings.BASE_DIR = str(tmp_path)
    _, install_dir, _, _ = isolated_autocomplete_paths

    from django.core.management import call_command

    call_command("autocomplete", "install", "--shell", "bash", stdout=io.StringIO(), no_color=True)
    script_path = install_dir / "completion.bash"
    lines = script_path.read_text().splitlines()
    lines[0] = "# django-completion version: 0.0.1"
    script_path.write_text("\n".join(lines))

    out = io.StringIO()
    call_command("autocomplete", "status", stdout=out, no_color=True)
    assert "bash script: outdated (script v0.0.1, package v" in out.getvalue()


@pytest.mark.django_db
def test_autocomplete_status_reports_v1_cache_outdated(tmp_path, settings, isolated_autocomplete_paths):
    settings.BASE_DIR = str(tmp_path)
    cache_file = tmp_path / ".django-completion-cache.json"
    cache_file.write_text(
        json.dumps(
            {
                "commands": ["migrate"],
                "app_labels": [{"label": "auth", "origin": "pip"}],
                "generated_at": 9_999_999_999,
            }
        )
    )

    from django.core.management import call_command

    out = io.StringIO()
    call_command("autocomplete", "status", stdout=out, no_color=True)
    output = out.getvalue()
    assert "Schema: v1 (outdated)" in output
    assert "Apps with migrations: 0" in output


@pytest.mark.django_db
def test_autocomplete_status_verbose_outputs_diagnostics(tmp_path, settings, isolated_autocomplete_paths):
    settings.BASE_DIR = str(tmp_path)
    _, install_dir, _, _ = isolated_autocomplete_paths
    cache_file = tmp_path / ".django-completion-cache.json"
    cache_file.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "commands": ["migrate", "shell"],
                "app_labels": [{"label": "auth", "origin": "pip"}],
                "migrations": {"auth": ["0001_initial"]},
                "warnings": ["Could not inspect migrations for app 'legacy'"],
                "generated_at": 1_771_920_000,
            }
        )
    )
    install_dir.mkdir(parents=True)
    (install_dir / "completion.bash").write_text("# django-completion version: 0.0.1\n")

    from django.core.management import call_command

    out = io.StringIO()
    call_command("autocomplete", "status", "--verbose", stdout=out, no_color=True)
    output = out.getvalue()
    assert f"Cache path: {cache_file}" in output
    assert "Generated: 2026-02-24 08:00:00 UTC" in output
    assert "Schema version: 2" in output
    assert "Apps with migrations: 1 (auth)" in output
    assert "Warnings: 1" in output
    assert "- Could not inspect migrations for app 'legacy'" in output
    assert "bash hook:" in output
    assert "bash script:" in output
    assert "(v0.0.1, outdated)" in output
    assert "Package version:" in output


@pytest.mark.django_db
def test_autocomplete_status_verbose_shows_source_reminder_when_installed_and_current(
    tmp_path, settings, isolated_autocomplete_paths
):
    settings.BASE_DIR = str(tmp_path)
    _, _install_dir, bashrc, _ = isolated_autocomplete_paths

    from django.core.management import call_command

    call_command("autocomplete", "install", "--shell", "bash", stdout=io.StringIO(), no_color=True)

    out = io.StringIO()
    call_command("autocomplete", "status", "--verbose", stdout=out, no_color=True)
    output = out.getvalue()

    assert f"source {bashrc}" in output


@pytest.mark.django_db
def test_autocomplete_status_verbose_no_source_reminder_when_hook_not_installed(
    tmp_path, settings, isolated_autocomplete_paths
):
    settings.BASE_DIR = str(tmp_path)
    autocomplete_mod, install_dir, _bashrc, _ = isolated_autocomplete_paths
    pkg_version = autocomplete_mod._package_version()
    install_dir.mkdir(parents=True)
    script_path = install_dir / "completion.bash"
    script_path.write_text(f"# django-completion version: {pkg_version}\n")
    # hook is NOT installed (bashrc is empty)

    from django.core.management import call_command

    out = io.StringIO()
    call_command("autocomplete", "status", "--verbose", stdout=out, no_color=True)
    output = out.getvalue()

    assert "If completion is not active" not in output


# ── _human_age unit tests ─────────────────────────────────────────────────────


from django_completion.management.commands.autocomplete import _human_age  # noqa: E402


def test_human_age_seconds():
    assert _human_age(0) == "0s"
    assert _human_age(30) == "30s"
    assert _human_age(59) == "59s"


def test_human_age_minutes():
    assert _human_age(60) == "1 minute"
    assert _human_age(90) == "1 minute"
    assert _human_age(120) == "2 minutes"
    assert _human_age(3599) == "59 minutes"


def test_human_age_hours():
    assert _human_age(3600) == "1 hour"
    assert _human_age(7200) == "2 hours"
    assert _human_age(86399) == "23 hours"


def test_human_age_days():
    assert _human_age(86400) == "1 day"
    assert _human_age(172800) == "2 days"
    assert _human_age(203692) == "2 days"


# ── _uninstall tests ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_autocomplete_uninstall_prints_reload_hint(tmp_path, settings, isolated_autocomplete_paths):
    settings.BASE_DIR = str(tmp_path)

    from django.core.management import call_command

    call_command("autocomplete", "install", "--shell", "bash", stdout=io.StringIO(), no_color=True)

    out = io.StringIO()
    call_command("autocomplete", "uninstall", stdout=out, no_color=True)
    output = out.getvalue()

    assert "source" in output
    assert "new terminal" in output


@pytest.mark.django_db
def test_autocomplete_uninstall_prints_cache_note(tmp_path, settings, isolated_autocomplete_paths):
    settings.BASE_DIR = str(tmp_path)

    from django.core.management import call_command

    call_command("autocomplete", "install", "--shell", "bash", stdout=io.StringIO(), no_color=True)

    out = io.StringIO()
    call_command("autocomplete", "uninstall", stdout=out, no_color=True)
    output = out.getvalue()

    assert ".django-completion-cache.json" in output
    assert "left in place" in output


@pytest.mark.django_db
def test_autocomplete_uninstall_removes_rc_block_and_script(tmp_path, settings, isolated_autocomplete_paths):
    settings.BASE_DIR = str(tmp_path)
    _, install_dir, bashrc, _ = isolated_autocomplete_paths

    from django.core.management import call_command

    call_command("autocomplete", "install", "--shell", "bash", stdout=io.StringIO(), no_color=True)
    assert "django-completion begin" in bashrc.read_text()

    call_command("autocomplete", "uninstall", stdout=io.StringIO(), no_color=True)

    assert "django-completion begin" not in bashrc.read_text()
    assert not (install_dir / "completion.bash").exists()


# --- 0.2.5-3: suppress file-completion fallback ---


def test_bash_template_suppresses_file_fallback():
    text = BASH_SCRIPT.read_text()
    assert "compopt +o default" in text
