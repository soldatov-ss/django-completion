# Agent-first repositioning of README and docs — design

**Date:** 2026-07-09
**Branch:** feature/0.3.0-agent-context
**Decision:** dual-headline positioning, agents first — not a full pivot, not a reorder-only.

## Problem

Usage is expected to skew heavily toward coding agents (Claude Code, Cursor, etc.)
reading the cache, with human tab completion the minority use. The current copy
inverts that: the PyPI description and keywords contain zero AI/agent terms, the
README's "For AI agents" section is #4 of 10 (~12 lines of 175), and docs/index.md
is 100% tab-completion framing. PyPI search, Google, and agents searching for
tooling never see the agent story.

## Rationale for dual-headline (vs. full pivot / reorder-only)

- The package name promises *completion*; a README that demotes it to a footnote
  fights the name.
- Usage may be 80/20 agent, but installation is ~100% human-approved — the README
  must still sell the person running `pip install`. That person codes with agents,
  so the agent pitch leads, and tab completion closes.
- Incremental: a full pivot also redoes demo.gif and the comparison page for
  marginal signal. Going further in 0.4 stays possible.

## Changes

### README.md

New intro (draft copy; badges unchanged above it):

> # django-completion
>
> Django `manage.py` context for coding agents — and Tab completion for you.
>
> Your agent learns every management command, its flags, and all migration names
> from one file read (no Django boot at all) or one `autocomplete context` call —
> instead of running `--help` once per command, each one booting Django. The same
> cache gives you project-aware Tab completion in bash and zsh: your own commands,
> their flags, app labels, and migration targets.

Section order: intro → Installation (unchanged) → **For AI agents** (expanded:
`context` example output reused from agents.md, the AGENTS.md/CLAUDE.md snippet,
a measured boot-savings number) → **Tab completion** (current "What Completes"
content; demo.gif moves here) → Commands → Compatibility → Safety and Privacy →
Limitations → Roadmap → Documentation → Development.

Nothing is deleted; content moves and the agent section grows.

### pyproject.toml

- `description = "Django manage.py context for coding agents + project-aware Tab
  completion — commands, flags, app labels, and migration targets from one cache"`
- keywords: add `ai`, `agents`, `coding-agents`, `llm`, `claude`, `cursor`,
  `copilot`, `agents-md`, `context`; keep all existing.

### docs/index.md

- Intro paragraph rewritten to the same dual pitch.
- "For AI agents" moves to #2 in the getting-started list (after Installation).
- Short "For AI agents" teaser section added mirroring the README's.
- Compatibility / How it works / Why-not-built-in sections stay.

### zensical.toml

Move "For AI agents" up in `nav` to directly after Installation, matching the
new index ordering.

### The measured number

During implementation, time on tests/testproject: `manage.py help` plus one
`<command> --help` subprocess per command, vs. one `autocomplete context` call,
vs. one read of the cache file. Put the honest result in the README agent
section. If the testproject is too small to be representative, state per-boot
math (N commands × measured single-boot cost) instead of a fake total.

### CHANGELOG/0.3.0.md

One bullet under Changed: README and docs repositioned to lead with the agent
use case.

## Out of scope

agents.md, usage.md, api.md, comparison.md content (already correct or
unaffected); demo.gif regeneration; package rename; any code change.

## Verification

Prose-only diff: docs build succeeds (zensical), README renders (markdown lint by
eye), existing 188-test suite untouched. Grep for anchors/links pointing at moved
README sections.
