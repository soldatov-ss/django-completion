# Installation

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

For teams that prefer to keep it out of production:

```python
if DEBUG:
    INSTALLED_APPS += ["django_completion"]
```

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

- writes a completion script to `~/.local/share/django-completion/`
- appends a marker-delimited source block to `~/.bashrc` or `~/.zshrc`
- builds the cache immediately so completion works right away

## 4. Reload your shell

```bash
source ~/.bashrc   # bash
source ~/.zshrc    # zsh
```

Tab completion is now active.

## Uninstall

```bash
python manage.py autocomplete uninstall
```

This removes the shell hook from your RC file, deletes the managed script files, and removes the managed install directory if it is empty. It never touches files outside the managed path.

## Installing from source

```bash
git clone https://github.com/soldatov-ss/django-completion.git
cd django-completion
uv sync
```
