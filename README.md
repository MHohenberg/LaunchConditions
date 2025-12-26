# LaunchConditions – Terminal Task Manager with Nested Tasks

`LaunchConditions` is a lightweight terminal application (TUI) built with **Python** and **Textual**. It is designed for people who prefer fast, keyboard-driven workflows and want a clean way to track tasks – including nested subtasks whose parent status updates automatically.

This tool reads and writes a simple text-based task file and presents it in an interactive terminal UI with color-coded statuses.

LaunchConditions takes its name from classic go/no‑go sequences in Space Age mission control scenes, where each subsystem confirms readiness before launch. The tool mirrors that spirit: a structured, hierarchical readiness check you can run for your own projects, routines, or daily liftoff.

---

## Features

### Nested tasks
- Tasks can have arbitrarily deep subtasks (children, grandchildren, etc.).
- A parent task automatically derives its status from its children:
  - If **any child is OPEN** → parent is **OPEN**
  - Else if **any child is IN_PROGRESS** → parent is **IN_PROGRESS**
  - Else → parent is **DONE**

### Color-coded status display
- **Red** = `OPEN`
- **Yellow/Orange** = `IN_PROGRESS`
- **Green** = `DONE`

### Keyboard-driven TUI
- Navigate and edit everything via the keyboard.
- Minimal, focused interface – ideal for a "launch checklist" or daily start routine.

### Persistent storage
- All changes are written back to the same text file the program was started with.
- Simple, diff-friendly format – works well with Git.

### Status summary bar
- A live overview at the top shows how many tasks are `OPEN`, `IN_PROGRESS` and `DONE`.

---

## Task file format

The task file uses a simple, line-based syntax:

```text
Task name : STATUS : DUE_DATE
    Subtask name : STATUS : DUE_DATE
        Sub-subtask : STATUS : DUE_DATE
```

Indentation determines hierarchy. Each indentation level is four spaces (or one tab, which will be treated as four spaces).

Example:

```text
Morning Routine:OPEN:
    Make Coffee:DONE:
    Check Launch Conditions:IN_PROGRESS:

Project X:OPEN:2025-12-31
    Write concept:OPEN:2025-12-10
```

- `Task name` – free text
- `STATUS` – one of `OPEN`, `IN_PROGRESS`, `DONE`
- `DUE_DATE` – optional (free text, e.g. `2025-12-10` or empty)

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourname/LaunchConditions.git
cd LaunchConditions
```

### 2. install with pipx

```bash
pipx install -e .
```

(If you already have `rich` from other projects, that's fine – Textual uses it under the hood.)

---

## Usage

Run the TUI and pass the path to your task file:

```bash
lc tasks.lc
```

or explicitly via Python:

```bash
python launchconditions.py tasks.txt
```

> **Note:** The task file must exist or be creatable in the given path. The program will read existing tasks and write back all changes to the same file.

---

## Key bindings

| Key           | Action                                      |
|---------------|---------------------------------------------|
| **↑ / ↓**     | Move cursor between tasks                   |
| **Space**     | Toggle status of the selected *leaf* task   |
| **a**         | Add a subtask (prompts for name and due)    |
| **s**         | Save tasks back to the file                 |
| **q**         | Save and quit                               |

---

## Status logic

Leaf tasks (tasks without children) can have their status manually changed using the **Space** key. Parent tasks never toggle directly; instead they derive their status from their children:

- If **any child is `OPEN`** → parent is `OPEN`
- Else if **any child is `IN_PROGRESS`** → parent is `IN_PROGRESS`
- Else (all children `DONE`) → parent is `DONE`

This makes the application very suitable for checklists like:

- daily launch conditions
- project readiness
- pre-flight / deployment / release checks

---

### Template

Templates are useful for recurring subprojects, e.g. for 'packing lists' for travelling.

1. Create a 'template.lct' file. Often this is easiest by creating an lc file and filling it within the tui... alternatively you can create a template file from any lc file inside launchcontrol

2. Start the tui
   ```bash
   ./launchconditions_textual.py template.lct
   ```
3. The system copies template.lct into something like template.20251225-180000.lc and opens that file. 

## Configuration (`~/.launchconditions`)

LaunchConditions can be customized via a simple INI-style config file located at  
`~/.launchconditions`.

```ini
[theme]
name=textual-dark

[templates]
template_dir=./lc_templates/
timestamp=%Y%m%d
```

#### [theme]
* name sets the Textual color theme (e.g. textual-dark, textual-light, dracula, tokyo-night).

#### [templates]
* template_dir specifies where .lct template files are searched if they are not found in the current directory.
* timestamp controls how new .lc files created from templates are named, using Python strftime syntax.

If the config file does not exist, LaunchConditions falls back to sensible defaults.

## Roadmap / Ideas

- Collapsible task trees (fold/unfold nested tasks)
- Filtering views (e.g. show only `OPEN` tasks)
- Configurable colors and key bindings
- Export to Markdown / JSON
- Optional autosave toggle

---

## License

This program is licensed under the **MIT License**. Use it, hack it, have fun!