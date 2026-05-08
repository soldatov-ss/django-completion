# V2 Implementation Issues

Five sequentially-ordered, independently-grabbable issues. Each is a vertical slice: defines its own files, acceptance criteria, and exit test. Dependencies are explicit.

Issues 1 → 2 → 3 form the core chain. Issue 4 (status improvements) depends on 3. Issue 5 (docs) can proceed in parallel with any of the others and is finalized last.

---

## Issue 1 — Cache v2: schema versioning + migration discovery

**Goal:** `build_cache()` produces a v2 cache — includes `schema_version`, a `migrations` dict keyed by app label, and a `warnings` list for apps whose migrations could not be inspected. Shell templates and status command are not touched in this issue.

**Files:**
- `src/django_completion/cache.py` — extend `build_cache()`
- `tests/test_cache.py` — new tests for migration discovery

**What to implement:**

In `build_cache()`:

1. Add `"schema_version": 2` to the returned dict.
2. After building `app_labels`, iterate over app configs and discover migration files on disk:
   - For each app, determine the migrations module path:
     - Check `settings.MIGRATION_MODULES` if it exists.
     - If the key is present and the value is `None` → app has no migrations, skip it.
     - If the key is present and the value is a string → use that as the module dotted path.
     - If the key is absent → use `{app_label}.migrations` (the default).
   - Resolve the module path to a filesystem directory using `importlib.util.find_spec` or `importlib.import_module`.
   - If the module cannot be imported or found → skip the app, append a warning string to `warnings`.
   - List `.py` files in the directory, excluding `__init__.py`, `__pycache__`, non-Python files, and hidden/private files (names starting with `_` other than `__init__`).
   - Strip the `.py` suffix.
   - Sort names alphabetically.
   - Store under `migrations[app_label]`.
3. Add `"migrations": {...}` and `"warnings": [...]` to the returned dict.

Cache compatibility rule: `read_cache()` needs no changes — callers that check `schema_version` are responsible for handling missing keys.

**Acceptance criteria:**
- `build_cache()["schema_version"]` == 2.
- `build_cache()["migrations"]` is a dict; keys are app labels that have migrations.
- Django's built-in apps (`auth`, `contenttypes`, `sessions`) appear as keys since they ship migrations.
- `build_cache()["migrations"]["auth"]` contains `"0001_initial"` (no `.py` suffix).
- `build_cache()["warnings"]` is a list (may be empty on a clean testproject).
- `settings.MIGRATION_MODULES = {"auth": None}` → `"auth"` absent from `migrations` dict.
- `settings.MIGRATION_MODULES = {"auth": "nonexistent.module"}` → `"auth"` absent from `migrations`, a warning string is appended.
- `uv run pytest tests/test_cache.py -q` passes.
- `uv run ruff check src/django_completion/cache.py` passes.
- `uv run ty check` passes.

**Notes:**
- Do not check database state. Discovery is purely from the filesystem.
- The `warnings` list is informational; a non-empty list must not prevent `build_cache()` from returning normally.
- The testproject has no local apps — test `MIGRATION_MODULES` cases using the `settings` fixture and Django's own apps.

---

## Issue 2 — Internal Python completion helper (`_complete`)

**Goal:** A new internal module `django_completion._complete` callable as `python -m django_completion._complete` that reads a v2 cache file and outputs shell completions. All completion decision logic lives here, not in the shell templates. Shell templates are not touched in this issue.

**Dependency:** Issue 1 (cache must contain `migrations` and `schema_version`).

**Files:**
- `src/django_completion/_complete.py` — new module
- `tests/test_complete.py` — new test file

**CLI contract:**

```
python -m django_completion._complete \
  --cache /path/to/.django-completion-cache.json \
  --words-json '["python", "manage.py", "migrate", "accounts", ""]' \
  --cword 4 \
  --format bash
```

Arguments:
- `--cache` — absolute path to the cache JSON file. If missing or unreadable, print nothing and exit 0.
- `--words-json` — JSON array of the current command line tokens (all words including the one being completed).
- `--cword` — integer index into `words-json` of the word being completed (0-based).
- `--format` — `bash` (plain newline-delimited) or `zsh` (`candidate:description` newline-delimited). Default: `bash`.

**Completion logic:**

1. Load cache from `--cache`. If any error → exit 0 silently.
2. Find the manage.py token: scan `words[0 .. cword-1]` for the last word ending in `manage.py`. If not found → exit 0.
3. Let `pos = cword - manage_idx` (position relative to manage.py).
4. Let `cur = words[cword]` (the word being completed, may be empty string).
5. Let `cmd = words[manage_idx + 1]` if `pos >= 2`, else `None`.

Completion rules by position:

| pos | cur starts with `-` | cmd       | Complete                                                     |
|-----|---------------------|-----------|--------------------------------------------------------------|
| 1   | —                   | —         | All command names                                            |
| 2   | yes                 | any       | Options for `cmd`                                            |
| 2   | no                  | `migrate` | App labels that appear in `cache["migrations"]`, local-first |
| 2   | no                  | other     | All app labels + options for `cmd`                           |
| 3   | yes                 | `migrate` | Options for `migrate`                                        |
| 3   | no                  | `migrate` | Migration names for `words[manage_idx+2]` + `"zero"`         |
| ≥3  | yes                 | other     | Options for `cmd`                                            |
| ≥3  | no                  | other     | All app labels + options for `cmd`                           |

Output format:
- `bash`: one candidate per line, plain string.
- `zsh`: one `candidate:description` per line. Colons inside descriptions must be escaped as `\:`. For commands, description = `command_help[cmd]`. For options, description = `command_option_descriptions[cmd][opt]`. For app labels, description = `[{origin}]`. For migration names, description is empty.

**Acceptance criteria (unit tests — no shell subprocess needed):**

Each test below calls a helper function `complete(cache, words, cword, fmt="bash") -> list[str]` that wraps the module's core logic (not the CLI) for ease of testing.

- `["manage.py", ""]`, cword=1 → command names list.
- `["python", "manage.py", ""]`, cword=2 → command names list.
- `["./manage.py", ""]`, cword=1 → command names list (path-like first token).
- `["uv", "run", "python", "manage.py", ""]`, cword=4 → command names list.
- `["manage.py", "migrate", ""]`, cword=2 → only apps present in `migrations` key (not all app labels).
- `["manage.py", "migrate", "accounts", ""]`, cword=3 → migration names for `accounts` + `"zero"`.
- `["manage.py", "migrate", "--"]`, cword=2 → options only, no app labels.
- `["manage.py", "migrate", "accounts", "--"]`, cword=3 → options only.
- `["manage.py", "shell", ""]`, cword=2 → all app labels + options (v1 fallback).
- `["manage.py", "shell", "--"]`, cword=2 → options only.
- Cache file missing → empty list.
- v1 cache (no `schema_version`, no `migrations`) → commands/options/app-labels still work; migrate pos-2 falls back to all app labels.
- `["python", ""]`, cword=1 → empty (no manage.py token found).
- `zsh` format: command candidates are `name:description`, colons in descriptions escaped.
- `zsh` format: app label candidates are `name:[local]` or `name:[pip]`.

- `uv run pytest tests/test_complete.py -q` passes.
- `uv run ruff check src/django_completion/_complete.py` passes.
- `uv run ty check` passes.

**Notes:**
- Keep the module small. The full logic should fit in ~100 lines.
- `_complete.py` is internal. Do not add public docstrings or expose it in `__init__.py`.
- Use `if __name__ == "__main__"` or `__main__` at module level to handle CLI entry.
- `importlib` is not needed here — the module only reads JSON; it never imports Django.

---

## Issue 3 — Shell templates: thin wrappers calling the Python helper

**Goal:** Replace inline `python3 -c '...'` snippets in both shell templates with calls to `python3 -m django_completion._complete`. End-to-end: `python manage.py migrate accounts <TAB>` returns migration names in a live shell. Shell tests updated to use a v2 fixture.

**Dependency:** Issue 2 (the `_complete` module must exist).

**Files:**
- `src/django_completion/scripts/bash_completion.sh.tmpl` — refactor
- `src/django_completion/scripts/zsh_completion.zsh.tmpl` — refactor
- `tests/test_shell.py` — update `cache_dir` fixture to v2 shape; thin down or replace Python-inline tests; add a test verifying the helper is called

**What to change in the bash template:**

Replace each `python3 -c '...'` block with a call to the helper. The helper is called with words built from `${COMP_WORDS[@]}` and `$COMP_CWORD`. Example pattern:

```bash
local words_json
words_json=$(printf '%s\n' "${COMP_WORDS[@]}" | python3 -c "
import json, sys
print(json.dumps(sys.stdin.read().splitlines()))
")
local candidates
candidates=$(python3 -m django_completion._complete \
  --cache "$cache_file" \
  --words-json "$words_json" \
  --cword "$COMP_CWORD" \
  --format bash 2>/dev/null)
COMPREPLY=($(compgen -W "$candidates" -- "$cur"))
```

The two existing functions (`_django_manage_completion` for `manage.py` and `_django_python_completion` for `python`/`python3`) can be unified into a single function backed by the helper, since the helper itself handles manage.py token detection. Unify only if it simplifies the template; do not unify for its own sake.

`complete` registrations to keep/add:
- `complete -F _django_manage_completion manage.py` (existing)
- `complete -o default -F _django_python_completion python python3` (existing)
- `complete -o default -F _django_python_completion uv` — add this to enable `uv run python manage.py` support. The `-o default` fallback means uv's own filename completion fires when COMPREPLY is empty (i.e., when no manage.py token is in the words). This is an acceptable tradeoff; uv's own shell integration is usually installed separately and takes precedence when both are active.

**What to change in the zsh template:**

Same logic: replace inline Python snippets with calls to the helper using `--format zsh`. The helper's `candidate:description` lines are already compatible with `_describe`.

For zsh, add `compdef _django_python_manage uv` alongside existing `compdef` lines. The function already handles the case where manage.py is absent (calls `_default`).

**Updated `cache_dir` fixture in `tests/test_shell.py`:**

Add `schema_version`, `migrations`, and `warnings` to the fixture dict:
```python
"schema_version": 2,
"migrations": {
    "myapp": ["0001_initial", "0002_add_user"],
    "auth": ["0001_initial"],
},
"warnings": [],
```

**New shell tests to add:**
- `test_bash_migrate_completes_migration_apps` — `manage.py migrate <TAB>` returns only apps that appear in `migrations` key (`myapp`, `auth`), not apps absent from it.
- `test_bash_migrate_completes_migration_names` — `manage.py migrate myapp <TAB>` returns `0001_initial`, `0002_add_user`, `zero`.
- `test_bash_helper_is_invoked` — source the template and verify it contains `django_completion._complete` (string check on the template file, not subprocess).

Existing shell tests (commands, options, app labels, no-cache) should continue to pass with the updated fixture.

**Acceptance criteria:**
- `uv run pytest tests/test_shell.py -q` passes.
- `uv run pytest -q` (full suite) passes.
- Manually: `source` the bash template in a shell that has `django_completion` installed, then `python manage.py migrate <TAB>` completes migration app labels.
- Manually: `python manage.py migrate auth <TAB>` completes migration names + `zero`.
- `uv run ruff check src/django_completion/scripts/` passes (skip if ruff doesn't lint `.tmpl`; verify the Python-side changes instead).
- `uv run ty check` passes.

**Notes:**
- Path-like `./manage.py <TAB>` as the first and only token requires a `complete` wildcard or bash hook (`complete -D`) that is out of scope for this issue. The helper already handles `./manage.py` when it appears mid-command (e.g., `python ./manage.py <TAB>`). Document this limitation in a comment in the template.
- Keep the shell templates readable. Inline Python for JSON building is acceptable if it remains short (< 5 lines). The goal is to remove completion decision logic from the templates, not all Python.

---

## Issue 4 — `autocomplete status`: verbose output + script version tracking

**Goal:** `status` shows v2-relevant counts and detects stale installed scripts. `status --verbose` outputs full diagnostic info. `autocomplete install` embeds the package version in the generated script file.

**Dependency:** Issue 3 (need to know what a v2 script looks like before defining "current vs outdated").

**Files:**
- `src/django_completion/management/commands/autocomplete.py` — `_install`, `_status`
- `tests/test_shell.py` or new `tests/test_autocomplete.py` — status tests

**Changes to `_install`:**

Before writing the script content, prepend a version comment:
```
# django-completion version: {version}
```
Where `{version}` comes from `importlib.metadata.version("django-completion")` or is read from `pyproject.toml`. Using `importlib.metadata` is preferred.

The script file on disk then starts with this line. `_status` compares it against the current package version to determine currency.

**Changes to `_status`:**

Add `--verbose` argument to the `status` subparser.

Default (non-verbose) output — replace current output with v2-aware version:
```
Cache: /path/to/.django-completion-cache.json (age 42s, fresh)
Schema: v2 (current)          ← or "v1 (outdated)" if schema_version missing/< 2
Commands: 28
Apps: 12
Apps with migrations: 8
Warnings: 0
bash hook: installed
zsh hook: installed
bash script: current           ← or "outdated (script v0.1.0, package v0.2.0)"
zsh script: not installed
```

Verbose output (`--verbose`):
```
Cache path: /path/to/.django-completion-cache.json
Generated: 2026-04-28 14:00:00 UTC
Schema version: 2
Commands: 28
Apps: 12
Apps with migrations: 8 (accounts, auth, billing, blog, ...)
Warnings: 0
bash hook: /home/user/.bashrc (installed)
zsh hook: /home/user/.zshrc (not installed)
bash script: /home/user/.local/share/django-completion/completion.bash (v0.2.0, current)
zsh script: not installed
Package version: 0.2.0
```

Script currency check: read the first line of the installed script file, parse the version comment, compare to the current package version. If the file does not exist or has no version comment → report "outdated".

**Acceptance criteria:**
- `autocomplete status` output includes schema version, apps-with-migrations count, and script currency.
- `autocomplete status --verbose` includes all fields listed above.
- After `autocomplete install`, the script file at `~/.local/share/django-completion/completion.bash` starts with `# django-completion version: 0.1.0` (current version).
- `autocomplete status` reports `bash script: current` after a fresh install.
- Manually editing the version comment in the installed file to `0.0.1` causes `autocomplete status` to report `outdated`.
- Cache with `schema_version` missing → `status` reports `v1 (outdated)`.
- `uv run pytest tests/ -q` passes.
- `uv run ty check` passes.

---

## Issue 5 — Launch assets: README, docs, changelog

**Goal:** All text assets are launch-ready for `0.2.0`. No TODO placeholders. README leads with the migrate demo. Docs cover installation, usage, how it works, troubleshooting, compatibility, safety/privacy, and API reference.

**Dependency:** Issues 1–4 must be complete so the docs accurately describe implemented behavior.

**Files:**
- `README.md` — rewrite for v2 public launch
- `CHANGELOG/0.2.0.md` — new file
- `docs/installation.md` — update for v2
- `docs/usage.md` — update for v2 (migrate completion, uv invocation)
- `docs/how_it_works.md` — update (Python helper, monkey-patch wording from PLAN)
- `docs/troubleshooting.md` — expand with v2 scenarios
- `docs/api.md` — update (v2 cache schema, `status --verbose`)
- `.github/ISSUE_TEMPLATE/` — add bug-report, completion-wrong, feature-request, shell-environment templates
- `pyproject.toml` — bump `version` to `0.2.0` and update `Development Status` classifier to `4 - Beta`

**README structure (from PLAN):**

1. Headline + subheadline.
2. Terminal demo block showing `migrate <TAB>`, `migrate accounts <TAB>`, `runserver --<TAB>`.
3. Installation (`pip install` / `uv add`).
4. Setup (INSTALLED_APPS → `autocomplete install` → restart shell).
5. Status / refresh / uninstall.
6. Compatibility matrix (Python 3.10+, Django 4.2+, bash/zsh, Linux/macOS).
7. Safety and privacy (no telemetry, no network, no DB, shell edits are reversible — exact wording from PLAN).
8. Limitations (no fish, no django-admin, no Windows official support, no global options before command).
9. Short roadmap (v2.1 candidates, v3 fish/wrappers).
10. Long-term core wording (exact phrase from PLAN).

**Changelog `0.2.0.md`** must accurately describe:
- Migration-aware completion for `migrate` (app labels + migration names + `zero`).
- Internal Python completion helper replacing inline shell snippets.
- `uv run python manage.py` support.
- Cache schema v2 with `schema_version`, `migrations`, `warnings`.
- `autocomplete status --verbose`.
- Script version tracking and currency detection.

**Issue templates** must request:
- OS, shell, Python version, Django version, install method.
- Invocation style.
- Output of `python manage.py autocomplete status --verbose`.

**Acceptance criteria:**
- `README.md` has no TODO or placeholder text.
- All five docs pages are complete per PLAN section "Documentation Pages".
- Troubleshooting covers all nine scenarios listed in PLAN.
- `CHANGELOG/0.2.0.md` exists and accurately reflects implemented behavior.
- `pyproject.toml` version is `0.2.0`.
- At least two GitHub issue templates exist under `.github/ISSUE_TEMPLATE/`.
- `uv build` produces a `0.2.0` wheel.
- `uv run pytest -q`, `uv run ruff check .`, `uv run ty check` all pass.

---

# 0.2.1 Patch Issues

Five fixes discovered during real-world testing after `0.2.0` shipped. Issues 1–4 are code changes; Issue 5 is docs-only. All are independent and can be grabbed in any order.

---

## Issue 0.2.1-1 — `autocomplete <TAB>` completes subcommands, not app labels

**Goal:** `python manage.py autocomplete <TAB>` completes `install`, `status`, `refresh`, `uninstall` — not app labels.

**Root cause:** `_complete.py` has no special case for `autocomplete`. It falls through to the v1 fallback (app labels + options), which is wrong because `autocomplete` takes subcommands, not app labels.

**Files:**
- `src/django_completion/_complete.py` — add `autocomplete` as a special case
- `tests/test_complete.py` — new tests

**What to implement:**

In the completion logic, add a rule for `cmd == "autocomplete"` at pos 2:
- Complete the hardcoded list: `["install", "status", "refresh", "uninstall"]`.
- If `cur` starts with `-`, fall through to options as usual.

The subcommand list is static and does not need to be read from cache.

**Acceptance criteria:**
- `["manage.py", "autocomplete", ""]`, cword=2 → `["install", "refresh", "status", "uninstall"]` (or any order).
- `["manage.py", "autocomplete", "s"]`, cword=2 → completions starting with `s` (shell filters, but list must include `status`).
- `["manage.py", "autocomplete", "--"]`, cword=2 → options only (existing behavior).
- `uv run pytest tests/test_complete.py -q` passes.
- `uv run ruff check src/django_completion/_complete.py` passes.
- `uv run ty check` passes.

---

## Issue 0.2.1-2 — `migrate <TAB>` shows local apps before pip/Django apps

**Goal:** `python manage.py migrate <TAB>` returns apps with migrations sorted local-first, then pip/django apps — not purely alphabetically.

**Root cause:** `_migration_app_labels()` in `_complete.py` returns apps in the order they appear in `cache["migrations"]`, which is alphabetical from `build_cache()`. The `origin` field in `cache["app_labels"]` carries `"local"` vs `"pip"` but is not consulted during migration app ordering.

**Files:**
- `src/django_completion/_complete.py` — update `_migration_app_labels()` to sort by origin
- `tests/test_complete.py` — new ordering test

**What to implement:**

In `_migration_app_labels(cache)`:
1. Build a lookup `{label: origin}` from `cache["app_labels"]`.
2. Sort migration app labels: `origin == "local"` first, then everything else, alphabetically within each group.

**Acceptance criteria:**
- Given cache with local app `accounts` and pip app `auth`, both in `migrations` dict: `migrate <TAB>` returns `accounts` before `auth`.
- Alphabetical order is preserved within each group.
- Apps absent from `cache["app_labels"]` (unknown origin) sort after local apps, treated as non-local.
- `uv run pytest tests/test_complete.py -q` passes.
- `uv run ruff check src/django_completion/_complete.py` passes.
- `uv run ty check` passes.

---

## Issue 0.2.1-3 — Status cache age is human-readable

**Goal:** `autocomplete status` shows `age 2 days` or `age 47 minutes` instead of `age 203692s`.

**Root cause:** `_status()` in `autocomplete.py` formats age as raw seconds. There is no human-readable duration formatter.

**Files:**
- `src/django_completion/management/commands/autocomplete.py` — add duration formatter, apply to status output
- `tests/test_shell.py` or new `tests/test_autocomplete.py` — test the formatter

**What to implement:**

Add a small helper (≤10 lines):

```python
def _human_age(seconds: float) -> str:
    ...
```

Conversion table:
- `< 60` → `"{n}s"`
- `< 3600` → `"{n} minutes"` (or `"1 minute"`)
- `< 86400` → `"{n} hours"` (or `"1 hour"`)
- `>= 86400` → `"{n} days"` (or `"1 day"`)

Apply to the `(age ..., fresh/stale)` part of the default status output and the verbose `Generated:` line.

**Acceptance criteria:**
- `_human_age(30)` → `"30s"`.
- `_human_age(90)` → `"1 minute"` or `"2 minutes"`.
- `_human_age(3700)` → `"1 hour"` or similar.
- `_human_age(203692)` → `"2 days"` or similar.
- `autocomplete status` output contains `age 2 days` not `age 203692s` for a 2-day-old cache.
- `uv run pytest tests/ -q` passes.
- `uv run ty check` passes.

---

## Issue 0.2.1-4 — Post-uninstall message: remind user to reload shell

**Goal:** After `autocomplete uninstall`, the output tells the user to run `source ~/.bashrc` (or `~/.zshrc`) or open a new terminal. Without this, completion functions remain loaded in the current session and the user thinks uninstall failed.

**Root cause:** `_uninstall()` in `autocomplete.py` prints a success message but does not mention that the current shell session still has the functions loaded in memory.

**Files:**
- `src/django_completion/management/commands/autocomplete.py` — update `_uninstall()` output

**What to implement:**

After the existing uninstall success message, print:

```
To complete removal from your current session, run:
  source ~/.bashrc   # or ~/.zshrc
Or open a new terminal.

Note: .django-completion-cache.json was left in place. Delete it manually if needed.
```

The shell rc file path should reflect the shell that was uninstalled (detect from the installed hook or fall back to both).

**Acceptance criteria:**
- Running `autocomplete uninstall` prints a message that mentions `source` and/or opening a new terminal.
- The cache note is included in the output.
- `uv run pytest tests/ -q` passes.
- `uv run ty check` passes.

---

## Issue 0.2.1-5 — Troubleshooting: "Unknown command: 'autocomplete'" (docs only)

**Goal:** A user who sees `Unknown command: 'autocomplete'` can find the answer in troubleshooting docs without opening a GitHub issue.

**Root cause:** When `DJANGO_SETTINGS_MODULE` (or equivalent env vars) is not set in the terminal, Django cannot load settings, cannot discover installed apps, and therefore does not see `django_completion` in `INSTALLED_APPS`. The `autocomplete` management command does not exist from Django's perspective. There is no code-side intercept — this fires at Django's command-discovery layer before any `django_completion` code runs. Shell completion still works because it reads the cache file and never imports Django.

**Files:**
- `docs/troubleshooting.md` — add new entry

**What to implement:**

Add a troubleshooting entry:

**"'Unknown command: autocomplete' error"**

Explain:
- The `autocomplete` management command requires Django to be fully configured (settings loaded, app discovered).
- Tab completion works independently because it reads the cache file and does not import Django.
- The fix is to ensure environment variables (`DJANGO_SETTINGS_MODULE`, database credentials, etc.) are set before running `python manage.py autocomplete ...`.
- Show the env-loading pattern from the project's `.env` setup.
- Note that `python manage.py autocomplete refresh` and `status` require the same env setup.

**Acceptance criteria:**
- `docs/troubleshooting.md` contains an entry for this error.
- The entry explains the root cause (settings not loaded) and the fix (load env vars).
- No code changes required.
- `uv run ruff check .` and `uv run ty check` still pass.

---

# 0.2.2 Issues

Four improvements that require per-command knowledge. All changes are in `_complete.py` and `tests/test_complete.py`. Issues are independent but share context — read Issue 0.2.2-1 first as it defines the whitelist used by the others.

Dependencies: 0.2.2-2, 0.2.2-3, 0.2.2-4 depend on the whitelist introduced in 0.2.2-1.

---

## Issue 0.2.2-1 — Replace generic fallback with command whitelist

**Goal:** For commands not known to accept app labels (`runserver`, `shell`, `createsuperuser`, etc.), complete options only — not app labels. App label completion is only offered for commands where it is semantically useful.

**Root cause:** The v1 generic fallback shows "app labels + options" for every command that is not `migrate`. This pollutes completion for `runserver`, `shell`, and dozens of other commands that never take app labels.

**Files:**
- `src/django_completion/_complete.py` — replace generic fallback with whitelist check
- `tests/test_complete.py` — new tests for whitelist behavior

**What to implement:**

Define a frozenset of Django built-in commands that accept app labels as positional arguments:

```python
_APP_LABEL_COMMANDS = frozenset({
    "migrate",
    "makemigrations",
    "showmigrations",
    "sqlmigrate",
    "dumpdata",
    "test",
    "check",
})
```

In the completion logic, replace the generic fallback rule:
- If `cmd` is in `_APP_LABEL_COMMANDS` → app labels + options (existing fallback behavior).
- If `cmd` is not in `_APP_LABEL_COMMANDS` → options only.

`migrate`, `makemigrations`, `showmigrations`, and `sqlmigrate` each get their own special cases (Issues 0.2.2-2 through 0.2.2-4); the whitelist controls the generic fallback for `dumpdata`, `test`, `check`, and any future commands added to the set.

**Acceptance criteria:**
- `["manage.py", "runserver", ""]`, cword=2 → options only, no app labels.
- `["manage.py", "shell", ""]`, cword=2 → options only, no app labels.
- `["manage.py", "dumpdata", ""]`, cword=2 → app labels + options (whitelist hit).
- `["manage.py", "test", ""]`, cword=2 → app labels + options (whitelist hit).
- `["manage.py", "mycustomcommand", ""]`, cword=2 → options only (unknown command, safe default).
- `uv run pytest tests/test_complete.py -q` passes.
- `uv run ruff check src/django_completion/_complete.py` passes.
- `uv run ty check` passes.

**Notes:**
- Custom management commands not in the whitelist fall back to options-only. This is the safe default — the user can still type an app label manually.
- Do not try to detect what custom commands accept at completion time; that would require importing Django.

---

## Issue 0.2.2-2 — `makemigrations <TAB>` completes local apps only

**Goal:** `python manage.py makemigrations <TAB>` completes only apps where `origin == "local"` — not pip packages or Django contrib apps. Running `makemigrations` on `auth` or `contenttypes` is never intentional.

**Dependency:** Issue 0.2.2-1 (whitelist).

**Files:**
- `src/django_completion/_complete.py` — add `makemigrations` special case
- `tests/test_complete.py` — new tests

**What to implement:**

Add a helper `_local_app_labels(cache) -> list[str]` that returns labels where `origin == "local"`, preserving alphabetical order.

Add a completion rule for `cmd == "makemigrations"` at pos ≥ 2:
- If `cur` starts with `-` → options only.
- Otherwise → local app labels only (from `_local_app_labels`).

**Acceptance criteria:**
- `["manage.py", "makemigrations", ""]`, cword=2 → only local apps, no `auth`, `contenttypes`, `sessions`.
- `["manage.py", "makemigrations", "--"]`, cword=2 → options only.
- Given cache with local app `accounts` and pip app `authtoken`: `makemigrations <TAB>` returns `accounts` but not `authtoken`.
- `uv run pytest tests/test_complete.py -q` passes.
- `uv run ruff check src/django_completion/_complete.py` passes.
- `uv run ty check` passes.

---

## Issue 0.2.2-3 — `showmigrations <TAB>` completes apps from migrations dict

**Goal:** `python manage.py showmigrations <TAB>` completes only apps that have migrations, local-first — same filtering as `migrate` at pos 2.

**Dependency:** Issue 0.2.2-1 (whitelist). Reuses `_migration_app_labels()` from Issue 0.2.1-2.

**Files:**
- `src/django_completion/_complete.py` — add `showmigrations` special case
- `tests/test_complete.py` — new tests

**What to implement:**

Add a completion rule for `cmd == "showmigrations"` at pos 2:
- If `cur` starts with `-` → options only.
- Otherwise → `_migration_app_labels(cache)` (local-first, same as `migrate`).

`showmigrations` does not take a migration name at pos 3 (unlike `migrate` and `sqlmigrate`), so pos ≥ 3 falls through to options only.

**Acceptance criteria:**
- `["manage.py", "showmigrations", ""]`, cword=2 → apps from `migrations` dict, local-first.
- `["manage.py", "showmigrations", "--"]`, cword=2 → options only.
- `["manage.py", "showmigrations", "accounts", ""]`, cword=3 → options only.
- `uv run pytest tests/test_complete.py -q` passes.
- `uv run ruff check src/django_completion/_complete.py` passes.
- `uv run ty check` passes.

---

## Issue 0.2.2-4 — `sqlmigrate <app> <migration> <TAB>` smart completion

**Goal:** `python manage.py sqlmigrate <TAB>` completes app labels from migrations dict; `python manage.py sqlmigrate accounts <TAB>` completes migration names for that app. Same two-level logic as `migrate`.

**Dependency:** Issue 0.2.2-1 (whitelist). Reuses `_migration_app_labels()` and `_migration_names()` from Issue 0.2.1-2.

**Files:**
- `src/django_completion/_complete.py` — add `sqlmigrate` special case
- `tests/test_complete.py` — new tests

**What to implement:**

Add completion rules for `cmd == "sqlmigrate"`:
- pos 2, `cur` starts with `-` → options only.
- pos 2, no dash → `_migration_app_labels(cache)` (local-first).
- pos 3, `cur` starts with `-` → options only.
- pos 3, no dash → `_migration_names(cache, words[manage_idx + 2])` (no `"zero"` — `sqlmigrate` requires an exact applied migration, `zero` is not valid).
- pos ≥ 4 → options only.

Note: unlike `migrate`, do **not** append `"zero"` to the migration names list. `sqlmigrate` requires an exact migration name; `zero` is a `migrate`-specific target.

**Acceptance criteria:**
- `["manage.py", "sqlmigrate", ""]`, cword=2 → apps from `migrations` dict.
- `["manage.py", "sqlmigrate", "accounts", ""]`, cword=3 → migration names for `accounts`, no `"zero"`.
- `["manage.py", "sqlmigrate", "--"]`, cword=2 → options only.
- `["manage.py", "sqlmigrate", "accounts", "--"]`, cword=3 → options only.
- `uv run pytest tests/test_complete.py -q` passes.
- `uv run ruff check src/django_completion/_complete.py` passes.
- `uv run ty check` passes.
