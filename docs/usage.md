# Usage

## Tab completion

Once installed, tab completion works for these invocation styles:

```bash
manage.py <TAB>
./manage.py <TAB>
python manage.py <TAB>
python3 manage.py <TAB>
python ./manage.py <TAB>
```

What completes:

- **First argument** — management command names
- **Later arguments** — if the current word starts with `-`, option flags only; otherwise app labels and option flags
- **zsh** — shows descriptions alongside completions when available

## Subcommands

### `autocomplete install`

Installs the shell hook and builds the cache.

```bash
python manage.py autocomplete install
python manage.py autocomplete install --shell bash
python manage.py autocomplete install --shell zsh
```

Safe to run more than once — re-running overwrites the completion script with the current version but does not add a duplicate source block to the RC file.

### `autocomplete status`

Shows the current state of the cache and shell hooks.

```bash
python manage.py autocomplete status
```

Example output:

```
Cache: /home/user/myproject/.django-completion-cache.json (age 8s, fresh)
Commands: 31
Apps: 7
bash hook: installed
zsh hook: not installed
```

### `autocomplete refresh`

Forces a full cache rebuild regardless of the auto-refresh cooldown. Run this after adding a new app or management command if completion has not updated yet.

```bash
python manage.py autocomplete refresh
```

### `autocomplete uninstall`

Removes the shell hook and managed script files.

```bash
python manage.py autocomplete uninstall
```

## Auto-refresh

After each `manage.py` command, `django-completion` refreshes the cache in a background thread with a 60-second cooldown. This means completions stay current without any manual steps.

To disable auto-refresh and manage the cache manually:

```python
# settings.py
DJANGO_COMPLETION_AUTO_REFRESH = False
```

When disabled, `autocomplete refresh` still works normally.
