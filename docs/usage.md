# Usage

## Tab completion

Once installed, tab completion works for these invocation styles:

```bash
manage.py <TAB>
./manage.py <TAB>
python manage.py <TAB>
python3 manage.py <TAB>
python ./manage.py <TAB>
uv run python manage.py <TAB>
uv run python ./manage.py <TAB>
```

Any shell word ending in `manage.py` is treated as the project command marker. Completion context is relative to the word after that marker.

## What completes

First argument after `manage.py`:

```bash
python manage.py <TAB>
migrate  runserver  shell  test
```

Option flags:

```bash
python manage.py migrate --<TAB>
--database  --fake  --fake-initial  --plan  --run-syncdb
```

Apps with migrations for `migrate`:

```bash
python manage.py migrate <TAB>
accounts  auth  billing  blog
```

Migration names for one app:

```bash
python manage.py migrate accounts <TAB>
0001_initial  0002_add_profile  zero
```

Other commands keep the v1 fallback behavior: app labels plus option flags. django-completion does not infer every custom command's argument semantics.

In zsh, command and option descriptions are shown when Django exposes them.

## Subcommands

### `autocomplete install`

Installs the shell hook, writes a versioned shell script, and builds the cache.

```bash
python manage.py autocomplete install
python manage.py autocomplete install --shell bash
python manage.py autocomplete install --shell zsh
```

Safe to run more than once. Re-running overwrites the managed completion script with the current package version but does not add a duplicate source block to the RC file.

### `autocomplete status`

Shows the current state of the cache, shell hooks, and installed scripts.

```bash
python manage.py autocomplete status
```

Example output:

```text
Cache: /home/user/myproject/.django-completion-cache.json (age 8s, fresh)
Schema: v2 (current)
Commands: 31
Apps: 7
Apps with migrations: 5
Warnings: 0
bash hook: installed
zsh hook: not installed
bash script: current
zsh script: not installed
```

Verbose output is intended for diagnostics and issue reports:

```bash
python manage.py autocomplete status --verbose
```

It includes the cache path, generated timestamp, schema version, migration app list, shell RC paths, installed script versions, and package version.

### `autocomplete refresh`

Forces a full cache rebuild regardless of the auto-refresh cooldown. Run this after adding a new app, migration file, or management command if completion has not updated yet.

```bash
python manage.py autocomplete refresh
```

### `autocomplete uninstall`

Removes the shell hook and managed script files.

```bash
python manage.py autocomplete uninstall
```

## Auto-refresh

After each `manage.py` command, django-completion refreshes the cache in a background thread with a 60-second cooldown. This keeps completions current without making tab completion import Django.

To disable auto-refresh and manage the cache manually:

```python
# settings.py
DJANGO_COMPLETION_AUTO_REFRESH = False
```

When disabled, `autocomplete refresh` still works normally.

## Known limits

These are out of scope for v0.2.0:

- `django-admin`
- fish shell
- native Windows/PowerShell support
- global options before command, such as `python manage.py --settings config.settings migrate`
- custom aliases such as `dj migrate`
- database-aware applied/unapplied migration filtering
