# django-completion

Shell autocomplete for Django's `manage.py` — complete commands, app labels, and options from your actual project.

## What it does

`django-completion` adds tab completion for `manage.py` in bash and zsh. It reads a local cache built from your Django project, so completions reflect your real commands, installed apps, and option flags.

```bash
python manage.py mig<TAB>        # → migrate, makemigrations
python manage.py migrate ac<TAB> # → accounts, api, auth
python manage.py migrate --<TAB> # → --fake, --database, --run-syncdb ...
```

## Getting started

1. [Installation](installation.md) — install the package and set up shell completion
2. [Usage](usage.md) — subcommands, auto-refresh, and configuration
3. [How it works](how_it_works.md) — cache, shell hooks, and the refresh lifecycle
4. [Troubleshooting](troubleshooting.md) — common problems and fixes
5. [API Reference](api.md) — auto-generated module documentation

## Compatibility

| Area | Supported |
|---|---|
| Python | 3.10+ |
| Django | 4.2+ |
| Shells | bash, zsh |
| OS | Linux, macOS |
| Windows | not officially supported (WSL with bash/zsh may work) |
