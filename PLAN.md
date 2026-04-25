# django-completion — Implementation Plan

## Status: COMPLETE (v1 — all 8 steps shipped)

All design decisions are locked. This document is the source of truth for resuming work.

---

## Project Identity

- **PyPI name:** `django-completion`
- **Django app label:** `django_completion`
- **Current pyproject.toml name:** `django-autocomplete` — needs renaming before first publish
- **Min versions:** Python 3.10+, Django 4.2+

---

## Design Decisions (locked)

| # | Decision | Choice |
|---|---|---|
| 1 | Integration mechanism | Django app added to `INSTALLED_APPS` |
| 2 | Setup flow | `pip install` → `INSTALLED_APPS` → one-time `python manage.py autocomplete install` |
| 3 | Performance | JSON cache file, auto-refresh via `BaseCommand.execute()` patch in `AppConfig.ready()` |
| 4 | Cache invalidation | After any `manage.py` call, 60-second cooldown, runs in background thread |
| 5 | Completion depth v1 | Level 3: command names + app labels + option flags |
| 6 | Completion depth v2 | Level 4: migration names, context-aware filtering |
| 7 | Shell support v1 | bash + zsh |
| 8 | Shell support v3 | fish |
| 9 | Intelligence v1 | Fuzzy "did you mean?" on mistype + rich descriptions in zsh completions |
| 10 | Intelligence v2 | Context-aware filtering (e.g. only apps that have migrations) |
| 11 | App classification | Local apps first with `[local]` tag; third-party after; private GitHub in v2 |
| 12 | Management commands | `autocomplete install / status / refresh / uninstall` |
| 13 | Testing | pytest for Python logic + subprocess-based shell script tests |
| 14 | Django core strategy | Ship fast (monkey-patch ok), prove adoption, write DEP later |

---

## Cache Schema

Location: `{project_root}/.django-completion-cache.json` (gitignore this file)

```json
{
  "commands": ["migrate", "runserver", "shell", "..."],
  "app_labels": [
    {"label": "myapp", "origin": "local"},
    {"label": "otherapp", "origin": "local"},
    {"label": "rest_framework", "origin": "pip"},
    {"label": "django.contrib.auth", "origin": "pip"}
  ],
  "command_options": {
    "migrate": ["--fake", "--fake-initial", "--database", "--run-syncdb", "--check"],
    "runserver": ["--noreload", "--nothreading", "--ipv6"]
  },
  "generated_at": 1714000000.0
}
```

---

## Project Structure (target)

```
django_completion/
    __init__.py
    apps.py              # AppConfig — patches BaseCommand.execute() in ready()
    cache.py             # Build, read, write, invalidate the JSON cache
    classify.py          # Detect app origin: local vs pip vs github
    fuzzy.py             # "Did you mean?" matching logic
    management/
        commands/
            autocomplete.py   # install / status / refresh / uninstall subcommands
    scripts/
        bash_completion.sh.tmpl   # bash completion script template
        zsh_completion.zsh.tmpl   # zsh completion script template
tests/
    test_cache.py
    test_classify.py
    test_fuzzy.py
    test_shell.py        # subprocess-based shell script tests
```

---

## Implementation Steps

### Step 1 — Project scaffolding
- [x] Rename `pyproject.toml` name to `django-completion`
- [x] Fix `requires-python` to `>=3.10`
- [x] Add `django>=4.2` as dependency
- [x] Create `django_completion/` package with empty `__init__.py`
- [x] Create `django_completion/apps.py` with basic `AppConfig`
- **Verify:** `python -c "import django_completion"` succeeds

### Step 2 — Cache builder (`cache.py`)
- [x] `build_cache(settings)` — introspects commands via `management.get_commands()`, app labels via `apps.get_app_configs()`, options via each command's `create_parser()`
- [x] `write_cache(data, path)` — writes JSON to `.django-completion-cache.json`
- [x] `read_cache(path)` — returns parsed cache or `None` if missing/corrupt
- [x] `is_stale(cache, cooldown_seconds=60)` — checks `generated_at` against `time.time()`
- **Verify:** `test_cache.py` — build cache from a test Django project, assert structure matches schema

### Step 3 — App classifier (`classify.py`)
- [x] `classify_app(app_config)` → `"local"` or `"pip"`
- [x] Local detection: check if `app_config.module.__file__` is under `BASE_DIR`
- [x] pip detection: check if module path is inside `site-packages`
- **Verify:** `test_classify.py` — test both paths with mock app configs

### Step 4 — Auto-refresh hook (`apps.py`)
- [x] In `AppConfig.ready()`, monkey-patch `BaseCommand.execute()` to call `maybe_refresh_cache()` after command runs
- [x] `maybe_refresh_cache()` — checks staleness, if stale spawns background `threading.Thread` to rebuild cache
- [x] Thread must be daemon=True so it doesn't block process exit
- **Verify:** Run any `manage.py` command twice within 60s, confirm cache only regenerates once

### Step 5 — Fuzzy matching (`fuzzy.py`)
- [x] `suggest(input_str, candidates)` → closest match(es) using `difflib.get_close_matches`
- [x] Hook into Django's `CommandError` output — intercept unknown command errors and append suggestion
- **Verify:** `test_fuzzy.py` — `migarte` → suggests `migrate`, `shel` → suggests `shell`

### Step 6 — `autocomplete` management command
- [x] `autocomplete install` — detect shell (bash/zsh), write completion script to appropriate location, append `source` line to `.bashrc`/`.zshrc`
- [x] `autocomplete status` — print cache age, app count, command count, shell hook status
- [x] `autocomplete refresh` — force cache rebuild regardless of cooldown
- [x] `autocomplete uninstall` — remove sourced line from shell config
- **Verify:** Run each subcommand, assert correct output and file side effects

### Step 7 — Shell script templates
- [x] `bash_completion.sh.tmpl` — reads cache JSON, implements `_django_completion()` function, registers with `complete`
- [x] `zsh_completion.zsh.tmpl` — same logic, adds description annotations from cache for rich tab display
- **Verify:** `test_shell.py` — subprocess invoke `bash -c 'source script; complete -p manage.py'`, assert registration

### Step 8 — Integration test
- [x] Create a minimal test Django project in `tests/testproject/`
- [x] Run full flow: build cache → install shell script → simulate tab completion → assert correct completions returned
- **Verify:** All pytest tests pass

---

## Roadmap

### v2
- Level 4 completions: migration names (`manage.py migrate myapp 000<tab>`)
- Context-aware filtering: `migrate` only suggests apps that have migrations
- Private GitHub app detection in classifier
- Full Docker-based integration tests in CI

### v3
- Fish shell support

### Long-term
- Write Django Enhancement Proposal (DEP) once adoption is proven
- Target: contribute shell completion infrastructure to Django core

---

## Known Issues / Open Questions
- `pyproject.toml` currently named `django-autocomplete` — rename before publishing
- Need to decide cache file location when `BASE_DIR` is not set in settings (fallback: `os.getcwd()`)
- Shell detection (`$SHELL` env var) may be unreliable in some CI environments — `autocomplete install` should accept `--shell bash|zsh` flag as override
