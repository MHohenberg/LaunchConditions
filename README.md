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

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # on macOS/Linux
# .venv\Scripts\activate   # on Windows PowerShell
```

### 3. Install dependencies

```bash
pip install textual rich
```

(If you already have `rich` from other projects, that's fine – Textual uses it under the hood.)

---

## Usage

Run the TUI and pass the path to your task file:

```bash
./launchconditions_textual.py tasks.txt
```

or explicitly via Python:

```bash
python launchconditions_textual.py tasks.txt
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

## Example workflow

### Singlular project
1. Create a `tasks.lc` file:

   ```text
   Launch day routine:OPEN:
       Coffee:DONE:
       Check LaunchConditions:OPEN:
   ```

2. Start the TUI:

   ```bash
   ./launchconditions_textual.py tasks.lc
   ```
3. Use **↑ / ↓** to select a task.
4. Press **Space** to toggle the status of a leaf task.
5. Press **a** to add a subtask under the currently selected task – you will be prompted for name and optional due date.
6. Press **s** or **q** to save.

### Template

Templates are useful for recurring subprojects, e.g. for 'packing lists' for travelling.

1. Create a 'template.lct' file. Often this is easiest by creating an lc file and filling it within the tui...

2. Start the tui
   ```bash
   ./launchconditions_textual.py template.lct
   ```
3. The system copies template.lct into something like template.20251225-180000.lc and opens that file. 


---

## Roadmap / Ideas

- Collapsible task trees (fold/unfold nested tasks)
- Filtering views (e.g. show only `OPEN` tasks)
- Configurable colors and key bindings
- Export to Markdown / JSON
- Optional autosave toggle

---

## License

This program is licensed under the **MIT License**. Use it, hack it, have fun!