# Troubleshooting

## Tab completion shows nothing

**Check that the hook is installed:**

```bash
python manage.py autocomplete status
```

If the hook shows `not installed`, run:

```bash
python manage.py autocomplete install
source ~/.bashrc  # or ~/.zshrc
```

**Check that the cache exists:**

The status command will show `Cache: not found` if the cache has never been built. Run:

```bash
python manage.py autocomplete refresh
```

**Check that you reloaded your shell:**

After install, you must source your RC file or open a new terminal. The completion script is not active in shells that were open before install.

## Completion stopped working after I added an app or command

The cache may be stale. Force a rebuild:

```bash
python manage.py autocomplete refresh
```

If auto-refresh is enabled (the default), the cache updates automatically within 60 seconds after the next `manage.py` command.

## Wrong shell was detected

`autocomplete install` reads `$SHELL` to detect your shell. If it installs for the wrong one, specify explicitly:

```bash
python manage.py autocomplete install --shell zsh
```

## zsh completions are not showing

Make sure your zsh is set up to use the completion system. Add this to `~/.zshrc` before the source block if it is not already present:

```zsh
autoload -Uz compinit && compinit
```

Then reload:

```bash
source ~/.zshrc
```

## I use `uv run python manage.py`

The shell scripts match any word ending in `manage.py`, so `uv run python manage.py <TAB>` should work. If it does not, check that the completion script was sourced (`autocomplete status`) and that the cache exists.

## How do I uninstall completely?

```bash
python manage.py autocomplete uninstall
```

This removes the source block from your RC file, deletes the managed script files, and removes the managed directory if it is empty. Then remove `django_completion` from `INSTALLED_APPS` and uninstall the package:

```bash
pip uninstall django-completion
```

## Will this touch my database?

No. Tab completion reads only the local cache file. The cache builder inspects Django's app registry and management command registry — it does not query the database.

## Is it safe in production?

The package has no middleware, models, migrations, or request-time behavior. If accidentally present in production settings it will not cause harm, but the recommendation is to install it in development only:

```python
if DEBUG:
    INSTALLED_APPS += ["django_completion"]
```
