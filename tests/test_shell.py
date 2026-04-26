"""Subprocess-based shell completion tests (Step 8)."""

import io
import json
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "src/django_completion/scripts"
BASH_SCRIPT = SCRIPTS_DIR / "bash_completion.sh.tmpl"
ZSH_SCRIPT = SCRIPTS_DIR / "zsh_completion.zsh.tmpl"


@pytest.fixture
def cache_dir(tmp_path):
    """A temp directory containing a pre-built completion cache."""
    data = {
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
    completions = _bash_complete(cache_dir, ["manage.py", "migrate", ""], 2)
    assert "--fake" in completions
    assert "--database" in completions


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_completes_app_labels(cache_dir):
    completions = _bash_complete(cache_dir, ["manage.py", "migrate", ""], 2)
    assert "myapp" in completions
    assert "auth" in completions


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
    assert "--fake" in completions
    assert "--database" in completions


@pytest.mark.skipif(not shutil.which("bash"), reason="bash not available")
def test_bash_python_without_manage_returns_nothing(cache_dir):
    # python TAB with no manage.py — should not activate django completion
    completions = _bash_complete(cache_dir, ["python", ""], 1, "_django_python_completion")
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
    assert "_describe -t commands" in text
    assert "_describe -t arguments" in text


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
