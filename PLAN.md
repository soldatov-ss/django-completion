# django-completion — Implementation Plan

## Status

- **v1:** Quiet/internal release candidate. Code is close, but release-facing README, docs, changelog, and final safety polish must be completed before publishing `0.1.0`.
- **v2:** Public launch release. This is the release to promote on Reddit/LinkedIn and ask real Django developers to install in daily projects.
- **v3+:** Broader shell/wrapper support and expansion beyond the v2 migration-centered completion model.

This document is the source of truth for product scope, implementation decisions, release gates, and roadmap sequencing.

---

## Product Identity

- **PyPI name:** `django-completion`
- **Django app label:** `django_completion`
- **Primary user for the next 3 months:** solo and small-team Django developers who use the terminal daily and run `manage.py` commands often, especially in medium/large projects where app labels, migrations, and command options are hard to remember.
- **Core promise:** `django-completion` makes `manage.py` feel native in your shell by completing commands, apps, options, and migration targets from your actual Django project.
- **Launch positioning:** project-aware shell completion for Django's `manage.py`.
- **Subheadline:** complete commands, app labels, options, and migration targets from your actual Django project.
- **Primary trust principle:** shell completion should be fast, local, inspectable, reversible, and non-invasive.

---

## Release Strategy

### v1 — Quiet/Internal Release (`0.1.0`)

Goal: publish a credible package to PyPI and GitHub so installation, packaging, and daily internal use can be tested by the maintainer and colleagues before public promotion.

v1 should be polished enough for accidental visitors, but it is not the public launch. It should not look abandoned or placeholder-level.

Release bar:

- README has no TODO placeholders.
- README explains what works today: command completion, app-label completion, option completion, bash/zsh support.
- README includes install, setup, status, refresh, uninstall, safety/privacy, limitations, and short roadmap.
- Docs include installation, usage, how it works, troubleshooting basics, and API reference.
- Changelog `0.1.0` accurately describes the initial release.
- `pyproject.toml` metadata is complete.
- `autocomplete install/status/refresh/uninstall` are documented.
- Tests, Ruff, type check, and build pass.
- Wheel includes `py.typed` and shell templates.
- GitHub/docs links consistently use `django-completion` where the repository URL is intended.
- Runtime cache is gitignored and not committed.
- v1 limitations are explicit:
  - bash and zsh only
  - requires adding `django_completion` to `INSTALLED_APPS`
  - no migration-name completion yet
  - no native Windows/PowerShell support
  - no `django-admin` support

Recommended v1 safety improvement before quiet release:

- Add `DJANGO_COMPLETION_AUTO_REFRESH = False` setting support.
- Default remains `True`.
- When disabled, the `AppConfig` hook should not auto-refresh after commands.
- `python manage.py autocomplete refresh` should still work manually.

### v2 — Public Launch Release (`0.2.0`)

Goal: the first public, promoted release. Users should see the demo and feel the package is ready to add to real projects now, not merely something to star and revisit later.

Public launch centerpiece:

```bash
python manage.py migrate <TAB>
accounts  billing  blog

python manage.py migrate accounts <TAB>
0001_initial  0002_add_profile  zero
```

v2 must feel complete for its promise. README, docs, troubleshooting, diagnostics, migration-aware completion, shell parity, and release process are part of the v2 launch scope.

### v3+

Goal: expand compatibility and intelligence after v2 proves daily value.

Likely areas:

- Fish shell support.
- Broader wrapper support: `poetry run python manage.py`, `pipenv run python manage.py`, etc.
- Docker integration tests.
- More command-specific rules.
- Configurable custom command completion rules.
- Model-name completion.
- Settings-module/global-option completion.
- Private GitHub/package-source classification.
- Possible Django core proposal once adoption and real-world feedback justify it.

---

## Locked Design Decisions

| # | Area | Decision |
|---|---|---|
| 1 | Integration mechanism | Django app added to `INSTALLED_APPS` |
| 2 | Setup flow | `pip install` or `uv add` -> `INSTALLED_APPS` -> `python manage.py autocomplete install` |
| 3 | Install location | Keep `~/.local/share/django-completion/completion.bash` and `completion.zsh` |
| 4 | Shell config | Use marker-delimited source blocks in `.bashrc` / `.zshrc` |
| 5 | Runtime cache | Project-root `.django-completion-cache.json`, gitignored |
| 6 | Cache refresh | Auto-refresh after `manage.py` commands, 60-second cooldown, process-local lock |
| 7 | Manual refresh | `python manage.py autocomplete refresh` always rebuilds |
| 8 | Auto-refresh setting | Add `DJANGO_COMPLETION_AUTO_REFRESH`, default `True` |
| 9 | Tab-completion behavior | Shell completion reads only the cache; it must not import Django or rebuild cache |
| 10 | v1 completion depth | Commands + app labels + option flags |
| 11 | v2 completion depth | `migrate` app labels + migration names + `zero` |
| 12 | v2 migration source | Disk-based migration files, not database/applied migration state |
| 13 | Migration modules | v2 must respect `settings.MIGRATION_MODULES` |
| 14 | App ordering | Local apps first, then non-local apps |
| 15 | Shell support v2 | bash and zsh are both first-class |
| 16 | Shell support v3 | fish |
| 17 | Python helper | v2 moves completion decision logic into an internal Python helper |
| 18 | Helper API stability | Internal implementation detail, not public API |
| 19 | Helper output | Shell-friendly newline-delimited lines; zsh can use `candidate:description` lines |
| 20 | `django-admin` | Out of scope for v2 |
| 21 | Wrappers v2 | Support `uv run python manage.py` if straightforward; broader wrappers later |
| 22 | Path-like manage.py | Support `./manage.py`, `backend/manage.py`, etc. by matching words ending in `manage.py` |
| 23 | Global options before command | Out of scope for v2 |
| 24 | Custom wrappers/aliases | Out of scope for v2 |
| 25 | User-configured completion rules | Out of scope for v2; reserve architecture space |
| 26 | Telemetry | No telemetry |
| 27 | Windows | Not officially supported; WSL may work with bash/zsh |
| 28 | Docker | Docs-only in v2; Docker CI later |
| 29 | Public roadmap | Concise roadmap in README/docs; detailed implementation here |
| 30 | Django core path | Long-term, humble, evidence-based; no promise of core inclusion |

---

## Cache Schema

Location: `{project_root}/.django-completion-cache.json`

The cache is generated runtime state and must not be committed.

### v1 Cache Shape

```json
{
  "commands": ["migrate", "runserver", "shell"],
  "app_labels": [
    {"label": "accounts", "origin": "local"},
    {"label": "blog", "origin": "local"},
    {"label": "auth", "origin": "pip"}
  ],
  "command_help": {
    "migrate": "Updates database schema. Manages both apps with migrations and those without."
  },
  "command_options": {
    "migrate": ["--fake", "--fake-initial", "--database", "--run-syncdb", "--check"]
  },
  "command_option_descriptions": {
    "migrate": {
      "--fake": "Mark migrations as run without actually running them.",
      "--database": "Nominates a database to synchronize."
    }
  },
  "generated_at": 1714000000.0
}
```

### v2 Cache Shape

v2 adds an explicit schema version, migration data, and warning collection.

```json
{
  "schema_version": 2,
  "commands": ["migrate", "runserver", "shell"],
  "app_labels": [
    {"label": "accounts", "origin": "local"},
    {"label": "blog", "origin": "local"},
    {"label": "auth", "origin": "pip"}
  ],
  "command_help": {
    "migrate": "Updates database schema. Manages both apps with migrations and those without."
  },
  "command_options": {
    "migrate": ["--fake", "--fake-initial", "--database", "--run-syncdb", "--check"]
  },
  "command_option_descriptions": {
    "migrate": {
      "--fake": "Mark migrations as run without actually running them.",
      "--database": "Nominates a database to synchronize."
    }
  },
  "migrations": {
    "accounts": ["0001_initial", "0002_add_profile", "0003_add_avatar"],
    "blog": ["0001_initial", "0002_add_slug"]
  },
  "warnings": [
    "Could not inspect migrations for app 'legacy': No module named legacy.migrations"
  ],
  "generated_at": 1714000000.0
}
```

Migration cache rules:

- Keyed by app label.
- Include only apps that have migrations.
- Include all migration targets found on disk.
- Strip `.py` suffix.
- Exclude `__init__.py`, `__pycache__`, non-Python files, private/hidden files.
- Sort migration names naturally/alphabetically.
- Include `zero` in completion output, not necessarily in cache.
- Respect `settings.MIGRATION_MODULES`:
  - custom module path -> inspect that module
  - `None` -> app has no migrations
  - missing key -> use default app `migrations` package
- If a migration module cannot be imported or inspected, skip that app and record a warning.
- Do not check database state in v2.
- Do not try to determine applied/unapplied migrations in v2.

Cache compatibility rules:

- Missing `schema_version` means v1 cache.
- v2 shell completion must degrade gracefully if `migrations` is missing.
- `autocomplete status` should report outdated cache schema.
- `autocomplete refresh` writes the current schema.

---

## Completion Behavior

### v1 Behavior

Supported invocations:

```bash
manage.py <TAB>
python manage.py <TAB>
python3 manage.py <TAB>
./manage.py <TAB>
python ./manage.py <TAB>
```

Completion rules:

- First argument after `manage.py`: command names.
- Later arguments:
  - if current word starts with `-`, complete options only.
  - otherwise complete app labels plus command options.
- zsh should show descriptions when available.
- Missing cache should return no completions silently.

### v2 Behavior

Supported v2 invocation targets:

```bash
manage.py <TAB>
./manage.py <TAB>
backend/manage.py <TAB>
python manage.py <TAB>
python3 manage.py <TAB>
python ./manage.py <TAB>
uv run python manage.py <TAB>
uv run python ./manage.py <TAB>
```

`manage.py` token detection:

- Treat any shell word ending in `manage.py` as the project command marker.
- Completion context is relative to the word after that token.
- Do not resolve paths during tab completion.

`migrate` rule:

```bash
python manage.py migrate <TAB>
```

- Complete only apps with migrations.
- Order local apps first, then non-local apps.
- Include Django contrib and third-party apps if they have migrations.

```bash
python manage.py migrate accounts <TAB>
```

- Complete all disk-discovered migration names for `accounts`.
- Include `zero`.
- Do not check database state.

```bash
python manage.py migrate --<TAB>
```

- Complete options only.

Fallback rule for all other commands:

- Keep v1 behavior: app labels plus options.
- Do not infer custom management command argument semantics.

Optional v2 stretch:

- `makemigrations <TAB>` local-app filtering if it is trivial after the helper refactor.

Out of v2 scope:

- `django-admin`.
- Global options before command, e.g. `python manage.py --settings config.settings migrate <TAB>`.
- Custom aliases like `dj migrate`.
- Model-name completion.
- Settings-module completion.
- User-configured completion rules.
- Database-aware applied/unapplied migration state.

---

## v2 Internal Completion Helper

v2 should move completion decision logic from inline shell snippets into an internal Python helper.

Motivation:

- Avoid duplicating context logic in bash and zsh templates.
- Make migration-aware completion testable with normal Python unit tests.
- Keep shell templates thin.
- Create a cleaner path to fish and future wrappers.

Suggested module:

```text
django_completion._complete
```

The helper is internal. Do not document it as a public API.

Possible CLI contract:

```bash
python -m django_completion._complete \
  --cache /path/to/.django-completion-cache.json \
  --words-json '["python", "manage.py", "migrate", "accounts", ""]' \
  --cword 4 \
  --format bash
```

Output:

- bash mode: newline-delimited plain candidates.
- zsh mode: newline-delimited candidates, optionally `candidate:description`.

Shell template responsibilities:

- Find nearest `.django-completion-cache.json` by walking upward from `$PWD`.
- Collect shell words/current index.
- Call internal Python helper.
- Render returned candidates with shell-native completion primitives.
- Stay silent if cache is missing or helper returns nothing.

---

## Management Command Behavior

### `autocomplete install`

v1/v2 behavior:

- Detect shell from `$SHELL`, defaulting to bash if unknown.
- Support explicit override:

```bash
python manage.py autocomplete install --shell bash
python manage.py autocomplete install --shell zsh
```

- Write managed script to `~/.local/share/django-completion/`.
- Add marker-delimited source block to shell rc file.
- Be idempotent.
- Overwrite the managed script file each time install runs.
- Build or refresh the cache immediately so completion works after install.
- Print the next step: restart shell or source the rc file.

v2 addition:

- Embed package/script version in generated shell scripts.

Example:

```sh
# django-completion version: 0.2.0
```

### `autocomplete status`

v1 minimum:

- cache path
- cache found/missing
- cache age
- command count
- app count
- bash/zsh hook status

v2 default status:

- cache exists/missing
- cache age
- schema version current/outdated
- commands count
- apps count
- apps-with-migrations count
- shell hook installed/missing
- installed script current/outdated
- warning count

v2 verbose status:

```bash
python manage.py autocomplete status --verbose
```

Verbose output should include:

- cache path
- schema version
- generated timestamp
- command count
- app count
- apps with migrations
- shell script paths
- installed script versions
- package version
- cache warnings

Issue templates should ask users to paste `status --verbose`.

### `autocomplete refresh`

- Force cache rebuild regardless of cooldown.
- Respect v2 cache schema.
- Record non-fatal cache build warnings.
- Continue to work even if `DJANGO_COMPLETION_AUTO_REFRESH = False`.

### `autocomplete uninstall`

Expected behavior:

- Remove marker-delimited shell rc blocks.
- Delete managed script files:
  - `~/.local/share/django-completion/completion.bash`
  - `~/.local/share/django-completion/completion.zsh`
- Remove the managed install directory if it becomes empty.
- Never delete files outside the managed path.
- Never touch user shell config outside the marker block.

---

## Safety, Privacy, and Trust

Must be stated clearly in README and docs:

- No telemetry.
- No network calls.
- Shell completion reads only the local cache.
- Tab completion does not import Django.
- Tab completion does not touch the database.
- The cache is local runtime state in the project root.
- The cache contains command names, app labels, option names/help, migration names, warnings, and timestamps.
- Shell rc edits are marker-delimited and reversible.
- `autocomplete uninstall` removes managed shell hooks and managed scripts.
- The package has no middleware, models, migrations, or request-time behavior.
- It should be safe if accidentally present in production settings, but docs should recommend development-only installation for teams that prefer strict production settings.

Development-only docs example:

```python
if DEBUG:
    INSTALLED_APPS += ["django_completion"]
```

Also mention that `DEBUG` is not always the right environment switch; teams may prefer separate settings modules or a custom environment flag.

---

## Performance Budgets

Targets:

- Cache build should stay under roughly 1 second for typical small/medium projects.
- Cached shell completion should feel instant; target under 50 ms.
- Shell completion must never import Django during tab press.
- Cache should remain human-readable JSON.
- Missing or outdated cache should fail quietly in shell completion and be diagnosed through `autocomplete status`.

---

## README and Docs Strategy

### v1 README

Polished but modest. No TODO placeholders.

Must include:

- concise promise
- what v1 does today
- install
- add to `INSTALLED_APPS`
- run `autocomplete install`
- status/refresh/uninstall
- safety/privacy
- limitations
- short roadmap to v2

Do not include a misleading v2-style GIF in v1.

### v2 README

Public launch README should lead with proof.

Above-the-fold structure:

```md
# django-completion

Project-aware shell completion for Django's manage.py.

Complete commands, app labels, options, and migration targets from your actual Django project.
```

Then show a short terminal demo:

```bash
$ python manage.py migrate <TAB>
accounts  billing  blog

$ python manage.py migrate accounts <TAB>
0001_initial  0002_add_profile  zero

$ python manage.py runserver --<TAB>
--addrport  --ipv6  --noreload  --nothreading
```

Installation order:

```bash
pip install django-completion
# or
uv add django-completion
```

README should include:

- quickstart
- compatibility matrix
- why this exists / comparison to Django's built-in command suggestions
- safety/privacy
- uninstall
- troubleshooting link
- concise public roadmap
- long-term Django core ambition, phrased humbly

Comparison wording:

```md
Django can suggest close command names after an error. django-completion prevents many of those errors by completing project-specific commands, app labels, options, and migration targets before you press Enter.
```

Long-term core wording:

```md
Long term, the goal is to learn from real-world usage and explore whether parts of this approach could inform Django's own management-command completion story.
```

### v2 GIF/Demo

Create after v2 behavior is implemented and frozen.

Requirements:

- 10-20 seconds.
- Dark terminal.
- Readable font.
- Minimal prompt/theme distractions.
- Show exactly:
  - command completion
  - app-label completion
  - migration-name completion
  - option completion
- Use a tiny demo Django project with meaningful app names:
  - `accounts`
  - `billing`
  - `blog`

Use it in:

- README top section.
- docs homepage.
- Reddit/LinkedIn launch posts.

### Documentation Pages

Required before v2 public launch:

- Installation
- Quickstart / Usage
- How it works
- Troubleshooting
- Compatibility
- Safety / Privacy
- API reference
- Contributing or architecture notes for adding command-specific rules

How it works must explain:

- installed scripts under `~/.local/share/django-completion/`
- marker-delimited shell rc source block
- project-root cache path
- cache contents
- auto-refresh after `manage.py` commands
- manual refresh
- tab completion reads cache only
- uninstall cleanup
- monkey patch / management command execution wrapper

Trust-building monkey patch wording:

```md
When `django_completion` is in `INSTALLED_APPS`, its AppConfig wraps Django's management command execution so the cache can refresh after commands run. The shell completion scripts do not import Django; they only read the cache file.
```

Troubleshooting page must cover:

- Tab completion shows nothing.
- I upgraded but migration completion does not work.
- Wrong shell was detected.
- Cache is stale.
- zsh completions are not showing.
- I use `uv run python manage.py`.
- How do I uninstall completely?
- Will this touch my database?
- Does this work with Docker?

Docker docs for v2:

- Docs-only, not full support guarantee.
- Explain likely pattern:
  - install package inside the Django environment/container
  - run `python manage.py autocomplete refresh` where Django can import settings
  - host shell completion can read the cache if the project directory is mounted
  - shell-hook installation inside ephemeral containers may not be useful

Compatibility matrix:

| Area | Supported in v2 |
|---|---|
| Python | 3.10+ |
| Django | 4.2+ |
| Shells | bash, zsh |
| OS | Linux/macOS expected; Windows not officially supported |
| Windows | WSL may work with bash/zsh |
| Invocations | `manage.py`, `./manage.py`, `python manage.py`, `python3 manage.py`, `uv run python manage.py` |
| Completion depth | commands, app labels, options, migrate app labels, migration names |

Do not recommend Homebrew, pipx, or global CLI installation. This is a project-environment Django app.

---

## Testing Strategy

### v1

- Python unit tests for cache/classifier/fuzzy helpers.
- Shell subprocess tests for bash/zsh script sourcing and basic completion.
- Integration tests for `autocomplete refresh/status`.
- Verify:
  - `uv run pytest -q`
  - `uv run ruff check .`
  - `uv run ty check`
  - `uv build`
  - wheel contains `py.typed` and shell templates

### v2

Mandatory Python helper tests:

- `manage.py <tab>` -> commands
- `python manage.py <tab>` -> commands
- `./manage.py <tab>` -> commands
- `uv run python manage.py <tab>` -> commands
- `manage.py migrate <tab>` -> migration app labels
- `manage.py migrate accounts <tab>` -> migration names + `zero`
- `manage.py migrate --<tab>` -> options only
- fallback non-`migrate` command -> app labels + options
- missing cache -> empty completions
- v1 cache missing `schema_version` -> graceful fallback / outdated status
- `MIGRATION_MODULES` custom module
- `MIGRATION_MODULES["app"] = None`
- warning collection for uninspectable migrations

Shell subprocess tests should become thinner:

- bash script registers and calls helper correctly
- zsh script sources successfully and calls helper correctly
- cache-missing behavior is silent
- path-like `./manage.py` works in bash if practical

CI scope for v2:

- Linux bash/zsh CI.
- macOS later if users report issues.
- Docker integration tests later, not v2.

Manual v2 release checks:

- install/uninstall manually tested in bash
- install/uninstall manually tested in zsh
- upgrade path from v1 script to v2 script checked
- `autocomplete status --verbose` output checked
- demo project completion checked before recording GIF

---

## GitHub and Community Setup

Before v2 public launch:

- Enable GitHub Discussions.
- Keep Issues for actionable work.
- Use Discussions for support, exploratory feedback, and ideas.

Discussion categories:

- Announcements
- Q&A
- Ideas
- Show and tell

Issue templates:

- Bug report
- Completion missing/wrong
- Feature request
- Shell/environment issue

Issue templates should ask for:

- OS
- shell
- Python version
- Django version
- install method
- invocation style (`python manage.py`, `uv run python manage.py`, etc.)
- relevant command line
- `python manage.py autocomplete status --verbose`

No telemetry.

Adoption signals:

- PyPI downloads
- GitHub stars
- Issues/Discussions quality
- Reddit/LinkedIn feedback
- users reporting real project usage

Do not use stars alone to choose product direction.

---

## Launch and Maintenance Strategy

### Public Launch Timing

Do not publicly promote v1.

Promote v2 only after:

- migration-aware completion works
- README/docs are launch-ready
- troubleshooting exists
- GIF/demo exists
- install/status/uninstall are reliable
- issue templates and Discussions are ready
- release checklist passes

### Launch CTA

Ask for feedback, not stars.

Suggested CTA:

```text
If you try it in a real Django project, I would love to hear where completion feels wrong or what command should become smarter next.
```

### First 4 Weeks After v2 Launch

Public maintenance promise:

- First 48 hours: respond quickly to install/shell breakage.
- First 2 weeks: prioritize bug fixes and docs clarifications.
- First 4 weeks: collect feature requests and decide v2.1/v3 scope.
- After that: normal open-source maintenance cadence.

Post-launch decision rules:

- If most feedback is install/shell confusion: v2.1 focuses on reliability, docs, and status diagnostics.
- If most feedback is "complete X command too": v2.1 adds command-specific rules such as `sqlmigrate`, `showmigrations`, or `makemigrations`.
- If most feedback is wrapper/shell compatibility: v2.1 improves invocation compatibility.
- If feedback is quiet but usage grows: v2.1 focuses on polish and fish preparation.

Badges:

- Use practical trust badges:
  - PyPI version
  - Python versions
  - Django versions
  - CI status
  - license
- Avoid early download-count badges.
- Avoid badges that are likely to go stale.

---

## Implementation Steps

### v1 Completion and Quiet Release

- [x] Project scaffolding
- [x] Cache builder
- [x] App classifier
- [x] Auto-refresh hook
- [x] Fuzzy helper / command suggestion coverage
- [x] `autocomplete` management command
- [x] bash/zsh templates
- [x] Integration tests
- [x] Package metadata
- [ ] Add `DJANGO_COMPLETION_AUTO_REFRESH`
- [ ] Ensure `autocomplete install` creates/refreshes cache immediately
- [ ] Ensure `autocomplete uninstall` removes managed script files and empty managed directory
- [ ] README: replace placeholder content
- [ ] Docs: installation, usage, how it works, troubleshooting basics
- [ ] Changelog: accurate `0.1.0`
- [ ] Verify repository/docs links
- [ ] Verify `.django-completion-cache.json` ignored and absent from git
- [ ] Run final release checks
- [ ] Publish quiet `0.1.0` to PyPI

### v2 Core Implementation

- [ ] Add `schema_version: 2`
- [ ] Add migration discovery to cache
- [ ] Respect `MIGRATION_MODULES`
- [ ] Add cache warning collection
- [ ] Add internal Python completion helper
- [ ] Refactor bash template to call helper
- [ ] Refactor zsh template to call helper
- [ ] Implement `migrate` app-label filtering
- [ ] Implement `migrate <app> <migration>` completion
- [ ] Include `zero` for migration target completion
- [ ] Preserve v1 fallback behavior for non-`migrate` commands
- [ ] Support path-like `manage.py`
- [ ] Support `uv run python manage.py` if straightforward
- [ ] Add script version metadata
- [ ] Make `status` report script current/outdated
- [ ] Add `status --verbose`
- [ ] Add outdated schema reporting
- [ ] Add v2 helper unit tests
- [ ] Thin shell subprocess tests
- [ ] Manual bash/zsh install/uninstall tests

### v2 Launch Assets

- [ ] Launch README
- [ ] Full docs
- [ ] Compatibility matrix
- [ ] Troubleshooting page
- [ ] How-it-works page
- [ ] Safety/privacy section
- [ ] Changelog `0.2.0`
- [ ] GitHub issue templates
- [ ] GitHub Discussions
- [ ] Demo project
- [ ] v2 GIF
- [ ] Reddit/LinkedIn launch copy

### v2 Release Checklist

- [ ] `uv run pytest -q`
- [ ] `uv run ruff check .`
- [ ] `uv run ty check`
- [ ] `uv build`
- [ ] wheel contains `py.typed`
- [ ] wheel contains shell templates
- [ ] README updated
- [ ] docs updated
- [ ] changelog updated
- [ ] issue templates added
- [ ] demo GIF recorded
- [ ] `autocomplete status --verbose` checked
- [ ] install/uninstall manually tested in bash
- [ ] install/uninstall manually tested in zsh
- [ ] quiet v1 lessons reviewed

---

## Roadmap

### v2 Core

- Migration-aware completion for `migrate`.
- Context-aware filtering for apps with migrations.
- Internal Python completion helper.
- Cache schema versioning.
- Script version detection.
- Better `status` diagnostics and `--verbose`.
- Launch-ready README/docs/troubleshooting/demo.

### v2 Stretch

- Local-app filtering for `makemigrations`.
- Better origin categories, e.g. `django` vs `pip`, if easy.
- `uv run python manage.py` support if not already covered by generic parser.

### v2.1 Candidates

Chosen based on post-launch feedback:

- reliability/docs/status improvements
- `sqlmigrate`
- `showmigrations`
- `makemigrations`
- wrapper compatibility
- shell edge cases

### v3

- Fish shell support.
- Broader wrappers:
  - `poetry run python manage.py`
  - `pipenv run python manage.py`
- Docker integration tests.

### Later

- Private GitHub/package-source classification.
- User-configurable command rules.
- Model-name completion.
- Settings-module completion.
- Database-aware applied/unapplied migration completion, only if there is strong demand.
- Django Enhancement Proposal exploration after adoption evidence.

---

## Known Issues / Open Questions

- No current v1 runtime issues tracked here.
- v2 decisions above are accepted design direction; implementation may still surface shell-specific details.
