# django-completion

![PyPI version](https://img.shields.io/pypi/v/django-completion.svg)
![Python versions](https://img.shields.io/pypi/pyversions/django-completion.svg)
![CI](https://github.com/soldatov-ss/django-completion/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/pypi/l/django-completion.svg)

Project-aware **tab completion** for Django's `manage.py`.

Press Tab to complete commands, app labels, options, and migration targets — in bash and zsh — from your actual Django project.

```bash
$ python manage.py migrate <TAB>
accounts  billing  blog

$ python manage.py migrate accounts <TAB>
0001_initial  0002_add_profile  zero

$ python manage.py runserver --<TAB>
--addrport  --ipv6  --noreload  --nothreading
```

- **GitHub:** https://github.com/soldatov-ss/django-completion/
- **PyPI:** https://pypi.org/project/django-completion/
- **Docs:** https://soldatov-ss.github.io/django-completion/
- **License:** MIT

## Installation

Install it in the same environment as your Django project:

```bash
pip install django-completion
# or
uv add django-completion
```

Add the app:

```python
INSTALLED_APPS = [
    ...
    "django_completion",
]
```

Install the shell hook:

```bash
python manage.py autocomplete install
```

Then restart your terminal or reload your shell config:

```bash
source ~/.bashrc   # bash
source ~/.zshrc    # zsh
```

## What Completes

Supported invocation styles:

```bash
manage.py <TAB>
./manage.py <TAB>
python manage.py <TAB>
python3 manage.py <TAB>
python ./manage.py <TAB>
uv run python manage.py <TAB>
```

Completion depth:

- command names after `manage.py`
- app labels and option flags for management commands
- `migrate` app labels filtered to apps that have migrations
- migration names and `zero` after `python manage.py migrate app_label`
- option descriptions in zsh where available

Django can suggest close command names after an error. django-completion prevents many of those errors by completing project-specific commands, app labels, options, and migration targets before you press Enter.

## Commands

```bash
python manage.py autocomplete status
python manage.py autocomplete status --verbose
python manage.py autocomplete refresh
python manage.py autocomplete uninstall
```

`status --verbose` is the best first diagnostic when completion behaves unexpectedly. It reports the cache path, schema version, migration counts, warning count, shell hooks, installed script versions, and package version.

`refresh` rebuilds `.django-completion-cache.json` manually. The cache also refreshes automatically after `manage.py` commands with a 60-second cooldown. To disable auto-refresh:

```python
DJANGO_COMPLETION_AUTO_REFRESH = False
```

## Compatibility

| Area | Supported |
|---|---|
| Python | 3.10+ |
| Django | 4.2+ |
| Shells | bash, zsh |
| OS | Linux and macOS expected |
| Windows | not officially supported; WSL with bash/zsh may work |
| Invocations | `manage.py`, `./manage.py`, `python manage.py`, `python3 manage.py`, `uv run python manage.py` |
| Completion depth | commands, app labels, options, migrate app labels, migration names |

## Safety and Privacy

- No telemetry.
- No network calls.
- Tab completion reads only the local cache file.
- Tab completion does not import Django.
- Tab completion does not touch the database.
- The cache is local runtime state in the project root.
- The cache contains command names, app labels, option names/help, migration names, warnings, and timestamps.
- Shell rc edits are marker-delimited and reversible.
- `autocomplete uninstall` removes managed shell hooks and managed scripts.
- The package has no middleware, models, migrations, or request-time behavior.

For teams that prefer strict production settings:

```python
if DEBUG:
    INSTALLED_APPS += ["django_completion"]
```

`DEBUG` is not always the right environment switch; separate settings modules or a custom environment flag may fit your deployment process better.

## Limitations

- bash and zsh only; fish is planned for a later release
- no `django-admin` support
- no official native Windows or PowerShell support
- no global options before command, such as `python manage.py --settings config.settings migrate`
- no custom alias support, such as `dj migrate`
- no database-aware applied/unapplied migration filtering

## Roadmap

Near-term candidates include more wrapper support, better Docker-oriented examples, fish shell support, and additional command-specific completion rules.

Long term, the goal is to learn from real-world usage and explore whether parts of this approach could inform Django's own management-command completion story.

## Documentation

Full documentation is at https://soldatov-ss.github.io/django-completion/.

## Development

```bash
git clone git@github.com:soldatov-ss/django-completion.git
cd django-completion
uv sync
uv run pytest -q
uv run ruff check .
uv run ty check
```

django-completion was created in 2026 by [Soldatov Serhii](https://github.com/soldatov-ss).
