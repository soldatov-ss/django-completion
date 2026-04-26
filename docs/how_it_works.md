# How it works

## Overview

`django-completion` has two separate parts that never interact at tab-completion time:

1. **Cache builder** — runs inside your Django process, writes a JSON file
2. **Shell scripts** — read the JSON file at tab-press time, never import Django

## The cache

Location: `{project_root}/.django-completion-cache.json`

The cache is generated runtime state. It contains:

- management command names
- app labels and their origin (`local` or `pip`)
- option flags per command
- option and command help text
- a `generated_at` timestamp

The cache is a plain JSON file. You can inspect it with any JSON viewer.

It is gitignored and must not be committed — it is machine-specific runtime state.

## Cache refresh lifecycle

The cache is built (or rebuilt) in three situations:

1. **`autocomplete install`** — always builds immediately after installing the hook
2. **`autocomplete refresh`** — always rebuilds on demand
3. **Auto-refresh** — after each `manage.py` command, a background thread checks whether the cache is older than 60 seconds and rebuilds if so

Auto-refresh uses a process-local lock so only one rebuild runs at a time. It never blocks the command that triggered it.

Set `DJANGO_COMPLETION_AUTO_REFRESH = False` to disable the background thread.

## The AppConfig hook

When `django_completion` is in `INSTALLED_APPS`, its `AppConfig.ready()` wraps Django's `BaseCommand.execute` so the cache can refresh after commands run. The patch is idempotent — it checks for a sentinel attribute before applying.

The shell completion scripts do not import Django. They only read the cache file.

## Shell scripts

`autocomplete install` writes a completion script to:

```
~/.local/share/django-completion/completion.bash
~/.local/share/django-completion/completion.zsh
```

And adds a source block to `~/.bashrc` or `~/.zshrc`:

```sh
# django-completion begin
source ~/.local/share/django-completion/completion.bash
# django-completion end
```

At tab-press time, the shell script:

1. walks up from `$PWD` to find the nearest `.django-completion-cache.json`
2. calls an inline Python snippet to read the cache and print candidates
3. passes the candidates to the shell's native completion primitives (`compgen` in bash, `_describe` in zsh)

If the cache is missing, the script returns no completions silently.

## Uninstall

`autocomplete uninstall`:

- strips the marker-delimited source block from all RC files
- deletes the managed script files
- removes `~/.local/share/django-completion/` if it is empty

It never touches files outside the managed path.
