import json
import subprocess
import sys

from django_completion._complete import complete


def _run_complete_cli(cache_file, words_json: str, cword: str = "1"):
    """Run the internal completion CLI for subprocess edge-case tests."""
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "django_completion._complete",
            "--cache",
            str(cache_file),
            "--words-json",
            words_json,
            "--cword",
            cword,
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )


def _cache() -> dict:
    """Return a v2 cache fixture for completion tests."""
    return {
        "schema_version": 2,
        "commands": ["migrate", "runserver", "shell"],
        "command_help": {
            "migrate": "Apply migrations: safely",
            "runserver": "Starts a development server",
            "shell": "Runs a Python shell",
        },
        "app_labels": [
            {"label": "accounts", "origin": "local"},
            {"label": "billing", "origin": "local"},
            {"label": "auth", "origin": "pip"},
            {"label": "sessions", "origin": "pip"},
        ],
        "command_options": {
            "migrate": ["--fake", "--fake-initial", "--database"],
            "shell": ["--interface", "--command"],
        },
        "command_option_descriptions": {
            "migrate": {
                "--fake": "Mark migrations as run",
                "--fake-initial": "Detect initial migrations",
                "--database": "Database: alias",
            },
            "shell": {
                "--interface": "Specify shell interface",
                "--command": "Run command",
            },
        },
        "migrations": {
            "accounts": ["0001_initial", "0002_add_user"],
            "auth": ["0001_initial"],
        },
        "warnings": [],
        "generated_at": 9_999_999_999,
    }


def test_completes_commands_after_manage_py():
    assert complete(_cache(), ["manage.py", ""], 1) == ["migrate", "runserver", "shell"]


def test_completes_commands_after_python_manage_py():
    assert complete(_cache(), ["python", "manage.py", ""], 2) == ["migrate", "runserver", "shell"]


def test_completes_commands_after_path_like_manage_py():
    assert complete(_cache(), ["./manage.py", ""], 1) == ["migrate", "runserver", "shell"]


def test_completes_commands_after_nested_path_like_manage_py():
    assert complete(_cache(), ["python", "backend/manage.py", ""], 2) == ["migrate", "runserver", "shell"]


def test_completes_commands_after_uv_run_python_manage_py():
    assert complete(_cache(), ["uv", "run", "python", "manage.py", ""], 4) == [
        "migrate",
        "runserver",
        "shell",
    ]


def test_uses_last_manage_py_token_before_current_word():
    assert complete(_cache(), ["manage.py", "shell", "python", "manage.py", ""], 4) == [
        "migrate",
        "runserver",
        "shell",
    ]


def test_migrate_completes_only_apps_present_in_migrations():
    assert complete(_cache(), ["manage.py", "migrate", ""], 2) == ["accounts", "auth"]


def test_migrate_app_completion_appends_migration_keys_missing_from_app_labels():
    cache = _cache()
    cache["migrations"]["thirdparty"] = ["0001_initial"]

    assert complete(cache, ["manage.py", "migrate", ""], 2) == ["accounts", "auth", "thirdparty"]


def test_migrate_completes_migration_names_and_zero():
    assert complete(_cache(), ["manage.py", "migrate", "accounts", ""], 3) == [
        "0001_initial",
        "0002_add_user",
        "zero",
    ]


def test_migrate_unknown_app_completes_zero_only():
    assert complete(_cache(), ["manage.py", "migrate", "billing", ""], 3) == ["zero"]


def test_migrate_second_position_dash_completes_options_only():
    assert complete(_cache(), ["manage.py", "migrate", "--"], 2) == ["--fake", "--fake-initial", "--database"]


def test_migrate_third_position_dash_completes_options_only():
    assert complete(_cache(), ["manage.py", "migrate", "accounts", "--"], 3) == [
        "--fake",
        "--fake-initial",
        "--database",
    ]


def test_unlisted_command_completes_options_only():
    assert complete(_cache(), ["manage.py", "shell", ""], 2) == ["--interface", "--command"]


def test_other_command_dash_completes_options_only():
    assert complete(_cache(), ["manage.py", "shell", "--"], 2) == ["--interface", "--command"]


def test_v1_cache_preserves_commands_options_and_migrate_app_fallback():
    cache = _cache()
    cache.pop("schema_version")
    cache.pop("migrations")

    assert complete(cache, ["manage.py", ""], 1) == ["migrate", "runserver", "shell"]
    # Without a migrations dict, migrate falls back to all app labels.
    assert complete(cache, ["manage.py", "migrate", ""], 2) == ["accounts", "billing", "auth", "sessions"]
    assert complete(cache, ["manage.py", "migrate", "--"], 2) == ["--fake", "--fake-initial", "--database"]
    # Non-whitelisted commands still return options only (no app labels).
    assert complete(cache, ["manage.py", "shell", ""], 2) == ["--interface", "--command"]


def test_malformed_migrations_falls_back_to_all_app_labels_for_migrate_apps():
    cache = _cache()
    cache["migrations"] = ["accounts"]

    assert complete(cache, ["manage.py", "migrate", ""], 2) == ["accounts", "billing", "auth", "sessions"]


def test_malformed_app_label_entries_are_ignored_and_missing_origin_defaults_to_pip():
    cache = _cache()
    cache["app_labels"] = [
        {"label": "accounts"},
        {"label": ""},
        {"label": 123},
        "auth",
    ]
    cache["migrations"] = {"accounts": ["0001_initial"]}

    assert complete(cache, ["manage.py", "migrate", ""], 2, fmt="zsh") == ["accounts:[pip]"]


def test_malformed_command_options_returns_no_dash_candidates():
    cache = _cache()
    cache["command_options"] = {"migrate": "--fake"}

    assert complete(cache, ["manage.py", "migrate", "--"], 2) == []


def test_malformed_option_descriptions_still_returns_options():
    cache = _cache()
    cache["command_option_descriptions"] = {"migrate": "--fake help"}

    assert complete(cache, ["manage.py", "migrate", "--"], 2, fmt="zsh") == [
        "--fake:",
        "--fake-initial:",
        "--database:",
    ]


def test_malformed_command_help_still_returns_zsh_commands():
    cache = _cache()
    cache["command_help"] = ["migrate"]

    assert complete(cache, ["manage.py", ""], 1, fmt="zsh") == ["migrate:", "runserver:", "shell:"]


def test_invalid_cword_returns_empty():
    assert complete(_cache(), ["manage.py", ""], -1) == []
    assert complete(_cache(), ["manage.py", ""], 2) == []


def test_no_manage_py_token_returns_empty():
    assert complete(_cache(), ["python", ""], 1) == []


def test_manage_py_at_current_word_does_not_activate():
    assert complete(_cache(), ["python", "manage.py"], 1) == []


def test_zsh_command_descriptions_escape_colons():
    assert complete(_cache(), ["manage.py", ""], 1, fmt="zsh")[0] == "migrate:Apply migrations\\: safely"


def test_zsh_app_label_descriptions_include_origin():
    assert complete(_cache(), ["manage.py", "migrate", ""], 2, fmt="zsh") == [
        "accounts:[local]",
        "auth:[pip]",
    ]


def test_zsh_option_descriptions_escape_colons():
    assert " --database:Database\\: alias".strip() in complete(_cache(), ["manage.py", "migrate", "--"], 2, fmt="zsh")


def test_zsh_migration_names_have_empty_descriptions():
    assert complete(_cache(), ["manage.py", "migrate", "accounts", ""], 3, fmt="zsh") == [
        "0001_initial:",
        "0002_add_user:",
        "zero:",
    ]


def test_autocomplete_completes_subcommands():
    assert complete(_cache(), ["manage.py", "autocomplete", ""], 2) == [
        "install",
        "refresh",
        "status",
        "uninstall",
    ]


def test_autocomplete_dash_completes_options_not_subcommands():
    assert complete(_cache(), ["manage.py", "autocomplete", "--"], 2) == []


def test_migrate_local_apps_come_before_pip_apps():
    result = complete(_cache(), ["manage.py", "migrate", ""], 2)
    # accounts and billing are local; auth is pip — locals must come first
    assert result.index("accounts") < result.index("auth")


def test_migrate_local_first_ordering_is_alphabetical_within_groups():
    cache = _cache()
    cache["app_labels"] = [
        {"label": "zoo_app", "origin": "local"},
        {"label": "accounts", "origin": "local"},
        {"label": "beta_pkg", "origin": "pip"},
        {"label": "auth", "origin": "pip"},
    ]
    cache["migrations"] = {
        "zoo_app": ["0001_initial"],
        "accounts": ["0001_initial"],
        "beta_pkg": ["0001_initial"],
        "auth": ["0001_initial"],
    }
    result = complete(cache, ["manage.py", "migrate", ""], 2)
    assert result == ["accounts", "zoo_app", "auth", "beta_pkg"]


def test_migrate_unknown_origin_apps_sort_after_local():
    cache = _cache()
    cache["app_labels"] = [{"label": "accounts", "origin": "local"}]
    cache["migrations"] = {
        "accounts": ["0001_initial"],
        "mystery": ["0001_initial"],
    }
    result = complete(cache, ["manage.py", "migrate", ""], 2)
    assert result.index("accounts") < result.index("mystery")


def test_missing_cache_file_cli_prints_nothing(tmp_path):
    result = _run_complete_cli(tmp_path / "missing.json", json.dumps(["manage.py", ""]))

    assert result.returncode == 0
    assert result.stdout == ""


def test_cli_with_no_candidates_prints_nothing(tmp_path):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(json.dumps(_cache()))

    result = _run_complete_cli(cache_file, json.dumps(["python", ""]))

    assert result.returncode == 0
    assert result.stdout == ""


def test_corrupt_cache_file_cli_prints_nothing(tmp_path):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text("not json")

    result = _run_complete_cli(cache_file, json.dumps(["manage.py", ""]))

    assert result.returncode == 0
    assert result.stdout == ""


def test_invalid_words_json_cli_prints_nothing(tmp_path):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(json.dumps(_cache()))

    result = _run_complete_cli(cache_file, "not json")

    assert result.returncode == 0
    assert result.stdout == ""


def test_non_list_words_json_cli_prints_nothing(tmp_path):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(json.dumps(_cache()))

    result = _run_complete_cli(cache_file, json.dumps({"word": "manage.py"}))

    assert result.returncode == 0
    assert result.stdout == ""


def test_non_string_words_json_cli_prints_nothing(tmp_path):
    cache_file = tmp_path / "cache.json"
    cache_file.write_text(json.dumps(_cache()))

    result = _run_complete_cli(cache_file, json.dumps(["manage.py", 123]))

    assert result.returncode == 0
    assert result.stdout == ""


# ── 0.2.2-1: Command whitelist ────────────────────────────────────────────────


def test_whitelist_runserver_completes_options_only():
    result = complete(_cache(), ["manage.py", "runserver", ""], 2)
    assert result == []  # runserver has no options in the fixture


def test_whitelist_shell_completes_options_only():
    result = complete(_cache(), ["manage.py", "shell", ""], 2)
    assert "accounts" not in result
    assert "--interface" in result


def test_whitelist_custom_command_completes_options_only():
    result = complete(_cache(), ["manage.py", "mycustomcommand", ""], 2)
    assert result == []


def test_whitelist_dumpdata_completes_app_labels_and_options():
    cache = _cache()
    cache["commands"].append("dumpdata")
    result = complete(cache, ["manage.py", "dumpdata", ""], 2)
    assert "accounts" in result
    assert "auth" in result


def test_whitelist_test_completes_app_labels_and_options():
    cache = _cache()
    cache["commands"].append("test")
    result = complete(cache, ["manage.py", "test", ""], 2)
    assert "accounts" in result
    assert "auth" in result


def test_whitelist_check_completes_app_labels_and_options():
    cache = _cache()
    cache["commands"].append("check")
    result = complete(cache, ["manage.py", "check", ""], 2)
    assert "accounts" in result
    assert "auth" in result


# ── 0.2.2-2: makemigrations ───────────────────────────────────────────────────


def test_makemigrations_completes_local_apps_only():
    result = complete(_cache(), ["manage.py", "makemigrations", ""], 2)
    assert "accounts" in result
    assert "billing" in result
    assert "auth" not in result
    assert "sessions" not in result


def test_makemigrations_dash_completes_options_only():
    result = complete(_cache(), ["manage.py", "makemigrations", "--"], 2)
    assert "accounts" not in result


def test_makemigrations_local_apps_sorted_alphabetically():
    cache = _cache()
    cache["app_labels"] = [
        {"label": "zoo_app", "origin": "local"},
        {"label": "accounts", "origin": "local"},
        {"label": "auth", "origin": "pip"},
    ]
    result = complete(cache, ["manage.py", "makemigrations", ""], 2)
    assert result == ["accounts", "zoo_app"]


def test_makemigrations_no_pip_apps_even_with_migrations():
    cache = _cache()
    cache["app_labels"] = [
        {"label": "accounts", "origin": "local"},
        {"label": "authtoken", "origin": "pip"},
    ]
    cache["migrations"]["authtoken"] = ["0001_initial"]
    result = complete(cache, ["manage.py", "makemigrations", ""], 2)
    assert "accounts" in result
    assert "authtoken" not in result


# ── 0.2.2-3: showmigrations ───────────────────────────────────────────────────


def test_showmigrations_completes_migration_apps_local_first():
    result = complete(_cache(), ["manage.py", "showmigrations", ""], 2)
    assert "accounts" in result
    assert "auth" in result
    assert result.index("accounts") < result.index("auth")


def test_showmigrations_dash_completes_options_only():
    result = complete(_cache(), ["manage.py", "showmigrations", "--"], 2)
    assert "accounts" not in result


def test_showmigrations_pos3_completes_options_only():
    result = complete(_cache(), ["manage.py", "showmigrations", "accounts", ""], 3)
    assert "accounts" not in result
    assert "0001_initial" not in result


# ── 0.2.2-4: sqlmigrate ───────────────────────────────────────────────────────


def test_sqlmigrate_completes_migration_apps():
    result = complete(_cache(), ["manage.py", "sqlmigrate", ""], 2)
    assert "accounts" in result
    assert "auth" in result


def test_sqlmigrate_dash_at_pos2_completes_options_only():
    result = complete(_cache(), ["manage.py", "sqlmigrate", "--"], 2)
    assert "accounts" not in result


def test_sqlmigrate_completes_migration_names_without_zero():
    result = complete(_cache(), ["manage.py", "sqlmigrate", "accounts", ""], 3)
    assert "0001_initial" in result
    assert "0002_add_user" in result
    assert "zero" not in result


def test_sqlmigrate_dash_at_pos3_completes_options_only():
    result = complete(_cache(), ["manage.py", "sqlmigrate", "accounts", "--"], 3)
    assert "0001_initial" not in result
    assert "zero" not in result


def test_sqlmigrate_pos4_completes_options_only():
    result = complete(_cache(), ["manage.py", "sqlmigrate", "accounts", "0001_initial", ""], 4)
    assert "accounts" not in result
    assert "0001_initial" not in result


# --- 0.2.5-2: autocomplete subcommand option completion ---


def test_autocomplete_status_dash_completes_verbose():
    result = complete(_cache(), ["manage.py", "autocomplete", "status", "--"], 3)
    assert "--verbose" in result
    assert "--shell" not in result


def test_autocomplete_install_dash_completes_shell():
    result = complete(_cache(), ["manage.py", "autocomplete", "install", "--"], 3)
    assert "--shell" in result
    assert "--verbose" not in result


def test_autocomplete_install_shell_value_completes_bash_zsh():
    result = complete(_cache(), ["manage.py", "autocomplete", "install", "--shell", ""], 4)
    assert "bash" in result
    assert "zsh" in result


def test_autocomplete_install_shell_value_no_other_candidates():
    result = complete(_cache(), ["manage.py", "autocomplete", "install", "--shell", ""], 4)
    assert len(result) == 2


def test_autocomplete_refresh_dash_returns_empty():
    # refresh has no subcommand-specific options; fall back to empty
    result = complete(_cache(), ["manage.py", "autocomplete", "refresh", "--"], 3)
    assert result == []
