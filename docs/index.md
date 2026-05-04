# django-completion

Project-aware shell completion for Django's `manage.py`.

Complete commands, app labels, options, and migration targets from your actual Django project.

```bash
$ python manage.py migrate <TAB>
accounts  billing  blog

$ python manage.py migrate accounts <TAB>
0001_initial  0002_add_profile  zero

$ python manage.py runserver --<TAB>
--addrport  --ipv6  --noreload  --nothreading
```

## Getting started

1. [Installation](installation.md) — install the package and set up shell completion
2. [Usage](usage.md) — completion behavior, subcommands, and auto-refresh
3. [How it works](how_it_works.md) — cache, shell hooks, helper process, and refresh lifecycle
4. [Troubleshooting](troubleshooting.md) — common problems and fixes
5. [API Reference](api.md) — supported commands, cache schema, and compatibility notes

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

## Why it exists

Django can suggest close command names after an error. django-completion prevents many of those errors by completing project-specific commands, app labels, options, and migration targets before you press Enter.
