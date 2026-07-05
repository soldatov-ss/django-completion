# django-completion

![PyPI version](https://img.shields.io/pypi/v/django-completion.svg)
![Python versions](https://img.shields.io/pypi/pyversions/django-completion.svg)
![CI](https://github.com/soldatov-ss/django-completion/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/pypi/l/django-completion.svg)

Project-aware **tab completion** for Django's `manage.py`.

Press Tab to complete your project's own management commands and their flags — plus app labels and migration targets — in bash and zsh. On a project with dozens of custom commands, nobody remembers every name and argument signature; django-completion introspects them from your actual project.

![django-completion demo](https://raw.githubusercontent.com/soldatov-ss/django-completion/main/demo.gif)

## Installation

> **Note:** this is the pip-installable, project-aware tool. The `django-completion` Homebrew formula is an unrelated static bash completion script.

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

The completion cache is built from your project at runtime, so it covers your custom management commands the same way it covers Django's built-ins:

```bash
python manage.py imp<TAB>                    # → import_articles
python manage.py import_articles --<TAB>     # → --dry-run  --limit  --since  --source  ...
```

Supported invocation styles:

```bash
manage.py <TAB>
python manage.py <TAB>
python3 manage.py <TAB>
python ./manage.py <TAB>
uv run python manage.py <TAB>
```

Completion depth:

- command names after `manage.py` — built-in, third-party, and your project's custom commands
- option flags for every command, introspected from each command's actual argparse parser
- app labels for `migrate`, `check`, `dumpdata`, `test`, and `makemigrations`
- `migrate` app labels filtered to apps that have migrations
- migration names and `zero` after `python manage.py migrate app_label`
- command and option descriptions in zsh where available

Django's built-in completion covers command names and option flags — it has no knowledge of your app labels, migration names, or project-specific targets. django-completion fills that gap. See [comparison with Django's built-in completion](https://soldatov-ss.github.io/django-completion/comparison/) for a full feature breakdown.

## For AI agents

The same cache that powers Tab completion gives coding agents every command, its flags, and all migration names — readable straight from `.django-completion-cache.json` with no Django boot at all, or via `python manage.py autocomplete context` for a compact markdown summary (one Django boot instead of a `--help` subprocess per command; `--json` prints the full cache). Add this to your project's `AGENTS.md` or `CLAUDE.md`:

```markdown
## Django management commands
This project maintains `.django-completion-cache.json` (django-completion).
Read it — or run `python manage.py autocomplete context` — instead of running
`manage.py help` or grepping management/commands/. It lists every command,
its flags with descriptions, and all migration names, and refreshes
automatically after each manage.py run.
```

See [For AI agents](https://soldatov-ss.github.io/django-completion/agents/) for the output format, the cache schema, and its stability policy.

## Commands

```bash
python manage.py autocomplete status
python manage.py autocomplete status --verbose
python manage.py autocomplete refresh
python manage.py autocomplete context
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
| Invocations | `manage.py`, `python manage.py`, `python3 manage.py`, `python ./manage.py`, `uv run python manage.py` |
| Completion depth | commands (including custom), option flags, app labels, migrate app labels, migration names |

## Safety and Privacy

- No telemetry.
- No network calls.
- Tab completion reads only the local cache file.
- Tab completion does not import Django.
- Tab completion does not touch the database.
- The cache is local runtime state in the project root.
- The cache contains command names, their providing apps, app labels, option names/help, migration names, warnings, and timestamps.
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
