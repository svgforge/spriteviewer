# AGENTS.md — Binding working rules for the Sprite-Viewer

This file is binding. Every agent working in this repository MUST have read
and understood these rules before taking any action.

## 1. Language — EVERYTHING IN ENGLISH (non-negotiable)

All code, comments, identifiers, documentation (including this file, README,
CHANGELOG, docs/), commit messages, issue/PR titles and descriptions, and any
communication with the human are written in English — no other language in any
repository artifact. Existing non-English content (e.g. this file) is
translated to English and stays English.

## 2. Confirmation duty (BEFORE every operation)

**Standard procedure for every action that changes something (deletes, moves,
overwrites, writes, installs, cleans up): first present the human a concrete
list of the affected paths/files showing the exactly named action steps, and
wait for their explicit "yes" BEFORE execution begins. No confirming "in the
same breath" as executing. Exception only for purely read-only actions that do
not change state.

## 3. Working area (non-negotiable)

- Work **EXCLUSIVELY** inside the project folder `sprite-viewer/`. Never
  outside — not even to "help", "search" or "restore".
- Searching, reading or modifying paths outside this project folder (trash,
  home, history folders of other apps, etc.) is **forbidden**, unless the
  human grants it **explicitly and repeatedly** for a **concretely named**
  path.
- If a rescue/cleanup action would require access outside the project: **stop
  and ask the human.** Do NOTHING without their consent.

## 4. Destructive actions (deleting, moving, rewriting)

- **Never** delete files or directories unless the human has **explicitly
  ordered** it — neither in the project nor elsewhere.
- **Gitignored directories are absolutely off-limits**, unless the human says
  so explicitly. They belong to the human (e.g. temporary scripts). This
  includes in particular here: `WORKX/` (see `.gitignore`).
- No `rm -r`, no `mv` into foreign areas, no renaming that loses content. When
  in doubt: do NOTHING and ask.
- An irreversible mistake (deleted, private files) does not justify aimless
  rummaging through the system — worse: such rummaging breaks the same rule
  again. Stop and communicate honestly.

## 5. Project architecture (conventions to keep)

- **src-layout (PEP 517)**: The package lives in `src/spriteviewer/`.
  Development entry point is `main.py` (adds `src/` to `sys.path`); the
  installed entry point is the console-script function in
  `src/spriteviewer/app.py:main`.
- **CLI = GNU getopt** (stdlib `getopt.gnu_getopt`), deliberately NO argparse:
  - Options and the sprite may interleave.
  - `-S 32`, `-S32`, `--size 32`, `--size=32` are all equivalent.
  - `--` ends option parsing.
  - **There is NO `--sprite`/`-s`**: The sprite file path is purely positional
    (first operand; default: bundled sprite).
- **SVG assets**: The only source is the bundled copies in
  `src/spriteviewer/{icons,spriteviewer}.svg` (installed via
  `install.py`/`sync_assets`). No duplicate SVG representations in the project
  root (do not create duplicates).

## 6. Handling assets and history

- Do not blindly "resync" asset files from `build/` artifacts, history folders
  or foreign copies — the source of truth is `src/spriteviewer/`.

## 7. Behaviour

- Never secretly, never without asking back, never more than the human asks
  for.
- Always do only what the human currently requests — no overzealous own
  initiative, no "cleanup actions" without a commission.
- Admit mistakes, do not cover them up; in case of damage report immediately
  and make the next action dependent on the human's approval.
