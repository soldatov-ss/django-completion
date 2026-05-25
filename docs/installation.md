# Installation

Install django-completion in the same Python environment as your Django project. It is a Django app, not a global shell utility.

## 1. Install the package

```bash
pip install django-completion
# or
uv add django-completion
```

## 2. Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    ...
    "django_completion",
]
```

For teams that prefer to keep development tools out of production:

```python
if DEBUG:
    INSTALLED_APPS += ["django_completion"]
```

`DEBUG` is not always the right environment switch. Separate settings modules or a custom environment flag may be a better fit for some deployments.

## 3. Install the shell hook

```bash
python manage.py autocomplete install
```

This auto-detects bash or zsh from `$SHELL`. To specify explicitly:

```bash
python manage.py autocomplete install --shell bash
python manage.py autocomplete install --shell zsh
```

The command:

- writes a versioned completion script to `~/.local/share/django-completion/`
- appends a marker-delimited source block to `~/.bashrc` or `~/.zshrc`
- builds `.django-completion-cache.json` immediately so completion works right away

## 4. Reload your shell

```bash
source ~/.bashrc   # bash
source ~/.zshrc    # zsh
```

Opening a new terminal works too.

## 5. Check status

```bash
python manage.py autocomplete status
```

For bug reports or deeper diagnostics:

```bash
python manage.py autocomplete status --verbose
```

## Compatibility

| Area | Supported |
|---|---|
| Python | 3.10+ |
| Django | 4.2+ |
| Shells | bash, zsh |
| OS | Linux and macOS expected |
| Windows | not officially supported; WSL with bash/zsh may work |

## Uninstall

```bash
python manage.py autocomplete uninstall
```

This removes the shell hook from your RC file, deletes the managed script files, and removes the managed install directory if it is empty. It never touches files outside the managed path.

Then remove `"django_completion"` from `INSTALLED_APPS` and uninstall the package if you no longer need it:

```bash
pip uninstall django-completion
```

## Installing from source

```bash
git clone https://github.com/soldatov-ss/django-completion.git
cd django-completion
uv sync
```

---
*By [Soldatov Serhii](https://github.com/soldatov-ss) · Last updated: May 2026*
