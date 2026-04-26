# django-completion

![PyPI version](https://img.shields.io/pypi/v/django-completion.svg)
![Python versions](https://img.shields.io/pypi/pyversions/django-completion.svg)
![CI](https://github.com/soldatov-ss/django-completion/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/pypi/l/django-completion.svg)

Shell autocomplete for Django's `manage.py` — complete commands, app labels, and options from your actual project.

- **GitHub:** https://github.com/soldatov-ss/django-completion/
- **PyPI:** https://pypi.org/project/django-completion/
- **Docs:** https://soldatov-ss.github.io/django_completion/
- **License:** MIT

---

## What it does

`django-completion` adds tab completion for `manage.py` in bash and zsh. It reads a local cache built from your Django project, so completions reflect your actual commands, installed apps, and option flags — not a hardcoded list.

Supported invocations:

```bash
manage.py <TAB>
python manage.py <TAB>
python3 manage.py <TAB>
./manage.py <TAB>
python ./manage.py <TAB>
```

What completes in v1:

- Management command names
- App labels (for commands that accept them)
- Option flags (e.g. `--fake`, `--database`, `--verbosity`)
- zsh shows descriptions alongside completions

---

## Installation

```bash
pip install django-completion
# or
uv add django-completion
```

Add to `INSTALLED_APPS` in your Django settings:

```python
INSTALLED_APPS = [
    ...
    "django_completion",
]
```

Install the shell hook (auto-detects bash or zsh):

```bash
python manage.py autocomplete install

# or specify the shell explicitly:
python manage.py autocomplete install --shell bash
python manage.py autocomplete install --shell zsh
```

Then reload your shell:

```bash
source ~/.bashrc   # or ~/.zshrc
```

Tab completion is now active.

---

## Commands

### `autocomplete install`

Writes the completion script to `~/.local/share/django-completion/` and adds a source block to your shell RC file. Builds the cache immediately so completion works right away. Safe to run more than once.

### `autocomplete status`

Shows cache state and shell hook status:

```
Cache: /path/to/project/.django-completion-cache.json (age 12s, fresh)
Commands: 28
Apps: 6
bash hook: installed
zsh hook: not installed
```

### `autocomplete refresh`

Forces a full cache rebuild regardless of the cooldown window. Useful after adding a new app or management command.

```bash
python manage.py autocomplete refresh
```

### `autocomplete uninstall`

Removes the shell hook from your RC file, deletes the managed script files, and removes the managed install directory if empty. Never touches files outside the managed path.

```bash
python manage.py autocomplete uninstall
```

---

## Auto-refresh

The cache refreshes automatically in a background thread after each `manage.py` command, with a 60-second cooldown to avoid redundant rebuilds.

To disable auto-refresh (manual `autocomplete refresh` only):

```python
DJANGO_COMPLETION_AUTO_REFRESH = False
```

---

## Safety and privacy

- No telemetry. No network calls.
- Tab completion reads only the local cache file — it does not import Django or touch the database.
- The cache is local runtime state stored in the project root as `.django-completion-cache.json`.
- Shell RC edits are marker-delimited and fully reversible with `autocomplete uninstall`.
- The package has no middleware, models, or request-time behavior.

For teams that prefer strict production settings:

```python
if DEBUG:
    INSTALLED_APPS += ["django_completion"]
```

---

## Limitations (v1)

- bash and zsh only (fish planned for a later release)
- requires adding `django_completion` to `INSTALLED_APPS`
- no migration-name completion yet
- no `django-admin` support
- no native Windows/PowerShell support (WSL with bash/zsh may work)

---

## Roadmap

**v2** adds migration-aware completion — the most-requested feature:

```bash
python manage.py migrate <TAB>
accounts  billing  blog

python manage.py migrate accounts <TAB>
0001_initial  0002_add_profile  zero
```

v2 also brings an internal Python completion helper (replacing inline shell snippets), cache schema versioning, better `status` diagnostics, and `uv run python manage.py` support.

---

## Development

```bash
git clone git@github.com:soldatov-ss/django-completion.git
cd django-completion
uv sync
```

Run tests:

```bash
just test
```

Run all quality checks (format, lint, type check, test):

```bash
just qa
```

---

## Documentation

Full documentation is at https://soldatov-ss.github.io/django_completion/.

To preview docs locally:

```bash
just docs-serve
```

---

## Author

django-completion was created in 2026 by [Soldatov Serhii](https://github.com/soldatov-ss).
