# How it works

## Overview

django-completion has three separate pieces:

1. **Cache builder** — runs inside Django and writes project metadata to JSON
2. **Internal completion helper** — reads the cache and decides which candidates match the current command line
3. **Shell scripts** — collect shell words, call the helper, and hand candidates to bash or zsh

Tab completion never imports Django and never touches the database.

## The cache

Location: `{project_root}/.django-completion-cache.json`

The cache is generated runtime state. It contains:

- `schema_version`
- management command names
- app labels and their origin (`local` or `pip`)
- option flags per command
- option and command help text
- migration names discovered on disk
- non-fatal migration-discovery warnings
- a `generated_at` timestamp

The cache is a plain JSON file. You can inspect it with any JSON viewer. It is machine-specific runtime state and should not be committed.

## Migration discovery

Migration completion is based on migration files on disk, not database state.

For each installed app, django-completion respects `settings.MIGRATION_MODULES`:

- custom module path — inspect that module
- `None` — treat the app as having no migrations
- missing key — use the default `{app}.migrations` package

Only public `.py` migration files are included. `__init__.py`, private files, hidden files, non-Python files, and `__pycache__` are ignored. `zero` is added by the completion helper at tab-completion time, not stored in the cache.

## Cache refresh lifecycle

The cache is built or rebuilt in three situations:

1. **`autocomplete install`** — always builds immediately after installing the hook
2. **`autocomplete refresh`** — always rebuilds on demand
3. **Auto-refresh** — after each `manage.py` command, a background thread checks whether the cache is older than 60 seconds and rebuilds if so

Auto-refresh uses a process-local lock so only one rebuild runs at a time. It never blocks the command that triggered it.

Set `DJANGO_COMPLETION_AUTO_REFRESH = False` to disable the background thread. Manual `autocomplete refresh` still works.

## The AppConfig hook

When `django_completion` is in `INSTALLED_APPS`, its AppConfig wraps Django's management command execution so the cache can refresh after commands run. The shell completion scripts do not import Django; they only read the cache file.

The wrapper is idempotent. It checks for a sentinel attribute before applying so command execution is not wrapped repeatedly.

## Installed shell scripts

`autocomplete install` writes managed completion scripts to:

```text
~/.local/share/django-completion/completion.bash
~/.local/share/django-completion/completion.zsh
```

Each generated script starts with a version marker:

```sh
# django-completion version: 0.2.0
```

`autocomplete status` compares that marker with the installed package version and reports whether the script is current or outdated.

## Shell RC block

The install command adds a marker-delimited source block to `~/.bashrc` or `~/.zshrc`:

```sh
# django-completion begin
source ~/.local/share/django-completion/completion.bash
# django-completion end
```

At tab-press time, the shell script:

1. walks up from `$PWD` to find the nearest `.django-completion-cache.json`
2. serializes shell words and the current-word index
3. calls `python3 -m django_completion._complete`
4. passes returned candidates to shell-native completion primitives

If the cache is missing or unreadable, the script returns no completions silently. Use `autocomplete status --verbose` for diagnostics.

## Internal helper

The internal helper lives at `django_completion._complete`. It is intentionally not a public API.

The helper accepts a cache path, shell words, current-word index, and output format. It implements the command-aware rules for bash and zsh, including `migrate` app-label and migration-name completion.

## Uninstall cleanup

`autocomplete uninstall`:

- strips the marker-delimited source block from shell RC files
- deletes the managed script files
- removes `~/.local/share/django-completion/` if it is empty

It never touches files outside the managed path.
