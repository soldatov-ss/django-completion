# Troubleshooting

Start with the verbose status output:

```bash
python manage.py autocomplete status --verbose
```

It shows the cache path, schema version, migration counts, warning count, shell hook paths, installed script versions, and package version.

## "Unknown command: 'autocomplete'" error

This error means Django could not find the `autocomplete` management command. It almost always means settings are not loaded in the terminal where you ran the command.

The `autocomplete` command requires Django to be fully configured — settings loaded and `django_completion` discovered in `INSTALLED_APPS`. Without that, Django cannot see the command at all.

Tab completion works independently because it reads the `.django-completion-cache.json` file directly and never imports Django.

**Fix:** make sure your environment variables are set before running any `manage.py autocomplete` command. Typical setup:

```bash
export DJANGO_SETTINGS_MODULE=myproject.settings
export DATABASE_URL=...   # and any other required env vars
```

Or if you use a `.env` file:

```bash
source .env
python manage.py autocomplete status --verbose
```

If your project uses `python-dotenv` or similar, it only loads the `.env` file when Django starts, so you need to load it in your shell separately.

Note that `autocomplete refresh` and `autocomplete status` require the same full Django setup. Once the cache is built you can press Tab freely — those keystrokes never touch Django.

## What is the difference between a hook and a script?

`autocomplete status` reports two separate things for each shell:

- **hook** — a marker-delimited `source` block in your RC file (`~/.bashrc` or `~/.zshrc`). It tells the shell where to find the completion script at startup.
- **script** — the actual completion file at `~/.local/share/django-completion/completion.bash` (or `.zsh`). It contains the tab-completion functions and registers them with the shell.

Both must be present for completion to work. `autocomplete install` writes both. If one is missing without the other, you can re-run `autocomplete install` to restore the pair.

The script version is also tracked: after a package upgrade the script may be outdated while the hook remains valid. Running `autocomplete install` again overwrites the script with the current version — the hook does not need to change.

## Tab completion shows nothing

First, confirm you are inside the project tree. Cache lookup starts at `$PWD` and walks upward — if your terminal is open at `~`, `/tmp`, or any directory outside the project, completion silently returns nothing.

Check that the hook is installed and the script is current:

```bash
python manage.py autocomplete status
```

If the hook shows `not installed`, run:

```bash
python manage.py autocomplete install
source ~/.bashrc  # or ~/.zshrc
```

If the cache shows `not found`, build it:

```bash
python manage.py autocomplete refresh
```

Also check that you reloaded your shell. Completion scripts are not active in terminals that were already open before install.

## I upgraded but migration completion does not work

Run:

```bash
python manage.py autocomplete status
```

Look for:

- `Schema: v1 (outdated)` — run `python manage.py autocomplete refresh`
- `bash script: outdated` or `zsh script: outdated` — run `python manage.py autocomplete install --shell bash` or `--shell zsh`
- `Apps with migrations: 0` — confirm the project has migration files and inspect `status --verbose` warnings

The Python package and the generated shell script can get out of sync after an upgrade. Re-running `autocomplete install` overwrites the managed script with the current package version.

## Wrong shell was detected

`autocomplete install` detects your shell by checking `$BASH_VERSION` first (bash always sets this in the current process; `$ZSH_VERSION` can be inherited by a bash child spawned inside a zsh session), then `$ZSH_VERSION`, then `$SHELL`. If it still installs for the wrong shell, specify explicitly:

```bash
python manage.py autocomplete install --shell bash
python manage.py autocomplete install --shell zsh
```

Then reload the matching RC file.

## Cache is stale

Force a rebuild:

```bash
python manage.py autocomplete refresh
```

If auto-refresh is enabled, the cache also updates automatically within 60 seconds after the next `manage.py` command. If you set `DJANGO_COMPLETION_AUTO_REFRESH = False`, manual refresh is required.

## zsh completions are not showing

Make sure zsh's completion system is initialized. Add this before the django-completion source block if it is not already present:

```zsh
autoload -Uz compinit && compinit
```

Then reload:

```bash
source ~/.zshrc
```

If descriptions look wrong or completion is empty, run `python manage.py autocomplete status --verbose` and check the zsh hook and zsh script lines.

## I use `uv run python manage.py`

Supported invocations include:

```bash
uv run python manage.py <TAB>
uv run python ./manage.py <TAB>
```

If it does not work, check that your shell has sourced the current script and that status reports a current script. If a separate `uv` shell integration takes precedence, source order may matter.

## How do I uninstall completely?

```bash
python manage.py autocomplete uninstall
```

This removes the source block from your RC file, deletes the managed script files, and removes the managed directory if it is empty. Then remove `django_completion` from `INSTALLED_APPS` and uninstall the package:

```bash
pip uninstall django-completion
```

## Will this touch my database?

No. Tab completion reads only the local cache file. Cache refresh inspects Django's app registry, management command registry, command parsers, and migration files on disk. It does not query the database and does not inspect applied/unapplied migration state.

## Does this work with Docker?

Docker can work, but django-completion does not provide full Docker-specific integration.

The usual pattern is:

- install django-completion inside the Django environment or container
- run `python manage.py autocomplete refresh` where Django can import settings
- keep the project directory mounted so the host shell can read `.django-completion-cache.json`
- install the shell hook on the host if the host shell is where you press Tab

To rebuild the cache inside a running container:

```bash
# docker
docker exec -it <container_name> python manage.py autocomplete refresh

# docker compose
docker compose exec web python manage.py autocomplete refresh
```

The cache file is written to `BASE_DIR` inside the container. As long as that directory is mounted to the same path on the host, the host shell will find it automatically.

Installing shell hooks inside short-lived containers is usually not useful because the shell RC file and generated scripts disappear with the container.

## Does this work with WSL?

Yes, with a few things to keep in mind:

- Install the shell hook inside WSL, not in Windows or PowerShell. Run `python manage.py autocomplete install` from your WSL bash or zsh session.
- `$PWD` inside WSL must be inside the mounted project directory when you press Tab. If your project is at `/mnt/c/Users/you/project`, `cd` there before using completion.
- The completion script is written to your WSL home directory (`~/.local/share/django-completion/`). It is not accessible from Windows-native shells.

## Is it safe in production?

The package has no middleware, models, migrations, or request-time behavior. If accidentally present in production settings it should not affect requests, but the recommendation is to install it in development only:

```python
if DEBUG:
    INSTALLED_APPS += ["django_completion"]
```

Use the environment switch that matches your deployment setup.

---
*By [Soldatov Serhii](https://github.com/soldatov-ss) · Last updated: May 2026*
