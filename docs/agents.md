# For AI agents

django-completion's cache is useful beyond Tab completion: it gives coding agents a way to learn every management command, its flags, and all migration names from one file read (no Django boot at all) or one subcommand call (a single Django boot instead of one per `--help`).

An agent working in a Django repo without it typically discovers commands by running `manage.py help` and then `<command> --help` once per command (each one imports Django and your settings), or by grepping `management/commands/` (which misses commands from third-party apps). The cache already holds all of that, refreshed automatically after each `manage.py` run.

## The quick path: `autocomplete context`

```bash
python manage.py autocomplete context
```

Prints a compact markdown summary: your project's own commands first with their non-global flags and help text, migration names per local app, and a one-line list of built-in and third-party commands (`--json` includes all apps' migrations). Typical output fits well within an agent's working context:

```markdown
# manage.py — 32 commands (cache generated 2026-07-05 16:40:15 UTC)

## Project commands [local]
- import_articles — Import articles from an external feed into the blog.
    --dry-run  --limit  --since  --source

## Migrations on disk [local]
- accounts: 0001_initial, 0002_add_profile
- billing: 0001_initial, 0002_add_subscription
- blog: 0001_initial, 0002_add_slug, 0003_add_published_at

## Built-in and third-party commands
check, dumpdata, makemigrations, migrate, runserver, shell, test, …
(run `python manage.py autocomplete context --json` for flags and descriptions)
```

Flags:

- `--json` — print the full cache as JSON (all commands with flags and descriptions), for agents that want everything in one call
- `--refresh` — force a cache rebuild first, ignoring the 60-second cooldown

`context` always renders current data: it rebuilds in memory when the cache is missing or stale, so it is always safe to call. That rebuild is written back to disk unless `DJANGO_COMPLETION_AUTO_REFRESH = False` is set, in which case pass `--refresh` to persist it explicitly.

## Context-file snippet

Copy this into your project's `AGENTS.md` or `CLAUDE.md` so agents know the cache exists:

```markdown
## Django management commands

Read `.django-completion-cache.json` in the project root. It lists every
management command (built-in, third-party, and this project's own), every
flag with its help text, and all migration names — and it auto-refreshes
after every `manage.py` run, so it is always at least as fresh as `--help`
output.

- Do NOT run `manage.py help` or `<command> --help` — each invocation boots
  Django (seconds to minutes on large projects). The cache already has it.
- Do NOT grep `management/commands/` to discover commands — that misses
  built-in and third-party ones.
- First time in this repo? Run `python manage.py autocomplete context` for a
  compact orientation summary.
```

## Reading the cache file directly

The cache lives at `{BASE_DIR}/.django-completion-cache.json` — normally the project root, next to `manage.py`. To locate it, walk up from the current directory until the file is found (the same rule the shell completion scripts use).

Reading the file directly is cheaper than `context` when Django startup cost matters: it is a plain file read and works even when the project's settings are broken or dependencies are missing.

### Schema

The full field-by-field schema with a JSON example is in the [API Reference](api.md#cache-schema).

To classify a command as project-local, look up its app in `command_apps` and check that app's `origin` in `app_labels`.

### Stability policy

The cache file format is a documented contract:

- **Additive changes do not bump `schema_version`.** New fields may appear in any release; consumers must ignore fields they do not recognize.
- **Breaking changes bump `schema_version`.** If you pin behavior to the schema, check `schema_version == 2`.
- `warnings` is informational and its message texts are not part of the contract.

## Freshness semantics

- The cache refreshes in a background thread after every `manage.py` command, with a 60-second cooldown — unless `DJANGO_COMPLETION_AUTO_REFRESH = False` is set, in which case only the explicit commands (`autocomplete refresh`, `context --refresh`, `install`) write it.
- It can be stale if code changed without any `manage.py` run since — a just-added command or migration file may be missing.
- `python manage.py autocomplete refresh` (or `context --refresh`) forces a rebuild.
- `generated_at` tells you how old the snapshot is.

## What is NOT in the cache

- Applied/unapplied migration **state** — `migrations` lists files on disk; it never queries the database.
- Positional-argument semantics for arbitrary commands.
- `django-admin` commands outside the project.

---
*By [Soldatov Serhii](https://github.com/soldatov-ss) · Last updated: July 2026*
