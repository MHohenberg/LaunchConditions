# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

LaunchConditions is a single-module keyboard-driven terminal task manager built on **Textual**. It tracks hierarchically nested tasks whose parent status is derived automatically from children. The entire application lives in `launchconditions.py`; `cli.py` and `__init__.py` are vestigial/broken and unused (the console script points directly at the module).

## Commands

```bash
# Install for development (creates the `lc` entry point)
pipx install -e .          # or: pip install -e .

# Run from source without installing
python launchconditions.py tasks.lc

# Run installed entry point
lc tasks.lc                # opens/creates a .lc task file
lc packing.lct             # .lct = template: copied to packing.<timestamp>.lc, then opened
```

There is no test suite, linter config, or build step beyond the standard setuptools packaging in `pyproject.toml` (version is bumped there manually). Requires Python >= 3.11.

## Task file format (`.lc` / `.lct`)

Line-based, one task per line: `Name:STATUS:DUE`. Indentation (4 spaces or a tab = one level) encodes the tree. `STATUS` is one of `OPEN` / `IN_PROGRESS` / `DONE`; `DUE` is free text and may be empty. Lines starting with `#` and blank lines are ignored on read. `:` is forbidden in names/due (enforced in the new-task dialog) because it is the field separator. `.lct` template files are the same format but statuses are reset to `OPEN` and due dates stripped when generated.

## Architecture

The code has two clean layers:

1. **Pure model + file I/O** (module-level functions, no Textual dependency):
   - `Task` dataclass — holds `children`/`parent` links and `depth`.
   - `parse_tasks_from_file` builds the tree using an indent-depth `stack`, then computes every parent's status bottom-up. `save_tasks_to_file` / `make_template` flatten via `flatten_tasks` (pre-order DFS) and re-emit.
   - **Status propagation is the core invariant**: a leaf's status is set by the user; a parent's is always derived — all children `DONE` → `DONE`, all `OPEN` → `OPEN`, otherwise `IN_PROGRESS`. After any leaf edit, `Task.propagate_up()` recomputes ancestors up the chain. Never set a parent status directly; go through `propagate_up`.

2. **Textual UI** (`LaunchConditionsApp`, `NewTaskScreen` modal). The `ListView` is a flat rendering of the tree (indent via spaces + a status symbol/color). Key handlers live in `action_*` methods wired through `BINDINGS`. `refresh_task_list` rebuilds the whole `ListView` from `self.roots` after every change and updates the summary bar; index/focus are preserved across rebuilds.

Key behaviors to preserve when editing UI:
- `space` toggles status **only on leaf tasks** (`action_toggle_status` early-returns for parents).
- Adding a subtask uses a Textual **worker** (`_add_subtask_worker`) because it awaits a modal screen (`push_screen_wait`).
- Edits autosave immediately (`save_with_handling`); `s` saves with a success toast; quitting saves first.

## Configuration

Read once at startup from `~/.launchconditions` (INI, via `configparser`). `launchconditions.dotfile` is the example to copy there. Sections: `[theme] name=` (Textual theme) and `[templates] template_dir=` / `timestamp=` (strftime for generated `.lc` filenames). Missing config falls back to defaults silently. Template lookup order: current directory first, then `template_dir`.
