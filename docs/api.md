# API Reference

django-completion is primarily a Django management-command integration. It does not expose a stable public Python API for applications to call.

## Django app

Add the app to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "django_completion",
]
```

The app registers the `autocomplete` management command and installs the cache-refresh hook from its `AppConfig`.

## Management command

### `autocomplete install`

```bash
python manage.py autocomplete install
python manage.py autocomplete install --shell bash
python manage.py autocomplete install --shell zsh
```

Writes a versioned shell script under `~/.local/share/django-completion/`, appends a marker-delimited source block to the selected shell RC file, and builds the cache immediately.

### `autocomplete status`

```bash
python manage.py autocomplete status
python manage.py autocomplete status --verbose
```

Default output includes cache freshness, schema freshness, command count, app count, migration-app count, warning count, hook state, and installed script currency.

Verbose output includes exact paths, generated timestamp, installed script versions, and package version.

### `autocomplete refresh`

```bash
python manage.py autocomplete refresh
```

Rebuilds `.django-completion-cache.json` immediately, regardless of the auto-refresh cooldown.

### `autocomplete uninstall`

```bash
python manage.py autocomplete uninstall
```

Removes marker-delimited shell RC blocks, deletes managed script files, and removes the managed install directory if empty.

## Settings

### `DJANGO_COMPLETION_AUTO_REFRESH`

Default: `True`

When enabled, django-completion refreshes the cache in a background thread after `manage.py` commands with a 60-second cooldown.

```python
DJANGO_COMPLETION_AUTO_REFRESH = False
```

Manual `autocomplete refresh` still works when auto-refresh is disabled.

## Cache schema

Location: `{project_root}/.django-completion-cache.json`

v0.2.0 writes schema version 2:

```json
{
  "schema_version": 2,
  "commands": ["migrate", "runserver", "shell"],
  "app_labels": [
    {"label": "accounts", "origin": "local"},
    {"label": "auth", "origin": "pip"}
  ],
  "command_help": {
    "migrate": "Updates database schema. Manages both apps with migrations and those without."
  },
  "command_options": {
    "migrate": ["--database", "--fake", "--fake-initial", "--run-syncdb"]
  },
  "command_option_descriptions": {
    "migrate": {
      "--fake": "Mark migrations as run without actually running them."
    }
  },
  "migrations": {
    "accounts": ["0001_initial", "0002_add_profile"],
    "auth": ["0001_initial"]
  },
  "warnings": [],
  "generated_at": 1714000000.0
}
```

Cache notes:

- missing `schema_version` means a v1 cache
- `migrations` is keyed by app label
- migration names do not include `.py`
- `zero` is added to completion output, not stored in the cache
- `warnings` are informational and do not prevent cache generation

## Internal helper

`django_completion._complete` is internal. Shell scripts call it with the cache path, shell words, current-word index, and output format. Its CLI and Python functions are not stable public API.

## Compatibility

| Area | Supported in v0.2.0 |
|---|---|
| Python | 3.10+ |
| Django | 4.2+ |
| Shells | bash, zsh |
| OS | Linux and macOS expected |
| Windows | not officially supported; WSL with bash/zsh may work |
| Invocations | `manage.py`, `./manage.py`, `python manage.py`, `python3 manage.py`, `uv run python manage.py` |
| Completion depth | commands, app labels, options, migrate app labels, migration names |

## Adding command-specific rules

Command-specific completion should live in the internal Python helper, not in shell templates. Shell templates should stay thin: find the cache, serialize shell words, call the helper, and render returned candidates.

Future rules should preserve these constraints:

- tab completion must not import Django
- missing or malformed cache data must fail silently in the shell
- bash and zsh behavior should be covered by shared helper tests
- shell templates should not duplicate command-context logic
