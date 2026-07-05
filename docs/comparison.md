# Comparison with Django's built-in completion

Django ships its own shell completion mechanism. This page explains what it provides, where it stops, and what django-completion adds on top.

## What Django's built-in completion provides

Django's completion support comes in two forms:

- A bash completion script ([`django-admin.bash`](https://github.com/django/django/blob/main/extras/django_bash_completion)) that system package managers may install automatically. It hooks into bash's completion system and completes command names after `django-admin` and `manage.py`.
- Argparse's built-in completion integration, available on Python 3.9+ via [`argparse.ArgumentParser`](https://docs.python.org/3/library/argparse.html). When wired up, it completes option flags for any command.

Both forms work without installing any additional package.

## Where the built-in completion stops

The built-in mechanism is generic — it reads argparse metadata at completion time but has no knowledge of your project's runtime state:

- It does not complete **app labels** because those come from `INSTALLED_APPS`, which requires Django settings to be loaded.
- It does not complete **migration names** because those live on disk inside each app's `migrations/` directory and vary per project.
- `migrate <TAB>` at position 2 shows nothing or all registered app labels regardless of which apps actually have migrations.
- `migrate accounts <TAB>` at position 3 shows nothing — there is no second-level migration name completion.
- There is no concept of **local vs pip origin** for app labels; `makemigrations` gets the same generic completion as any other command.
- Script updates require manual re-sourcing; there is no auto-refresh lifecycle.
- zsh support is not provided by the built-in script.

## Feature comparison

| Feature | Django built-in | django-completion |
|---|---|---|
| Command names after `manage.py` | Yes | Yes |
| Option flags | Yes | Yes |
| Tab completion without importing Django | No | Yes |
| App labels (from `INSTALLED_APPS`) | No | Yes |
| `migrate` — only apps that have migrations | No | Yes |
| `migrate` — migration names after app label | No | Yes |
| `migrate` — `zero` target | No | Yes |
| `sqlmigrate` — migration names (no `zero`) | No | Yes |
| `showmigrations` — apps with migrations | No | Yes |
| `makemigrations` — local apps only | No | Yes |
| zsh support with option descriptions | No | Yes |
| `uv run python manage.py` invocation | No | Yes |
| Single install command | No | Yes |
| Auto-refresh after each `manage.py` command | No | Yes |
| Script currency detection (`autocomplete status`) | No | Yes |

## When to use each

**Use Django's built-in** if you only need command-name and flag completion and prefer zero additional dependencies. It works out of the box on many Linux systems where the bash-completion package is installed.

**Use django-completion** if your project carries its own set of custom management commands — the cache is built from your project, so their names, flags, and help descriptions complete without loading Django on each Tab press. The same applies if you work with migrations regularly, manage many apps, or want zsh support with descriptions. The install is one command and the cache refreshes automatically.

**Both can coexist.** django-completion's shell hook activates when a `.django-completion-cache.json` is found in the project directory. For `django-admin` (which django-completion does not support), Django's built-in completion continues to apply.

---
*By [Soldatov Serhii](https://github.com/soldatov-ss) · Last updated: May 2026*
