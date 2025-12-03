#!/usr/bin/env python3

# MIT License
#
# Copyright (c) 2025 Martin Hohenberg <martin@hohenberg.jp>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import re
import sys

from rich.text import Text
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label, Input, Button, Static
from textual.screen import ModalScreen
from textual.containers import Vertical, Horizontal

STATUS_CYCLE = ["OPEN", "IN_PROGRESS", "DONE"]
STATUS_DEFAULT = "OPEN"


@dataclass
class Task:
    name: str
    status: str
    due: str
    children: List["Task"] = field(default_factory=list)
    parent: Optional["Task"] = None
    depth: int = 0

    def is_leaf(self) -> bool:
        return not self.children

    def recalc_status_from_children(self):
        if not self.children:
            return

        child_statuses = [ch.status for ch in self.children]

        # 1) If everything is DONE → DONE
        if all(s == "DONE" for s in child_statuses):
            self.status = "DONE"
        # 2) If everything is OPEN → OPEN
        elif all(s == "OPEN" for s in child_statuses):
            self.status = "OPEN"
        # 3) else → IN_PROGRESS
        else:
            self.status = "IN_PROGRESS"

    def propagate_up(self) -> None:
        """Recompute this task's status based on its children and propagate to parents.

        Rules:
        - If there are no children, only propagate upward.
        - If ALL children are DONE -> this task is DONE.
        - If ALL children are OPEN -> this task is OPEN.
        - Otherwise -> this task is IN_PROGRESS.
        """

        if self.children:
            self.recalc_status_from_children()

        if self.parent is not None:
            self.parent.propagate_up()

def parse_tasks_from_file(path: str) -> List[Task]:
    tasks: List[Task] = []
    stack: List[Task] = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return []

    for line in lines:
        raw = line.rstrip("\n")
        if not raw.strip() or raw.strip().startswith("#"):
            continue

        indent_match = re.match(r"^(\s*)(.*)$", raw)
        indent = indent_match.group(1)
        content = indent_match.group(2)

        spaces = indent.replace("\t", "    ")
        depth = len(spaces) // 4

        parts = content.split(":", 2)
        if len(parts) != 3:
            raise ValueError(f"Invalid line: {raw}")
        name, status, due = parts
        name = name.strip()
        status = status.strip() or STATUS_DEFAULT
        due = due.strip()

        task = Task(name=name, status=status, due=due, depth=depth)

        if depth == 0:
            tasks.append(task)
            stack = [task]
        else:
            if depth > len(stack):
                raise ValueError(f"Nested too deeply: {raw}")
            parent = stack[depth - 1]
            task.parent = parent
            parent.children.append(task)

            if depth == len(stack):
                stack.append(task)
            else:
                stack[depth] = task
                stack = stack[: depth + 1]

    # calculate status from the bottom up
    def walk(task_to_walk: Task):
        for ch in task_to_walk.children:
            walk(ch)
        if task_to_walk.children:
            task_to_walk.recalc_status_from_children()

    for t in tasks:
        walk(t)

    return tasks

def flatten_tasks(roots: List[Task]) -> List[Task]:
    result: List[Task] = []

    def walk(task: Task):
        result.append(task)
        for ch in task.children:
            walk(ch)

    for t in roots:
        walk(t)
    return result

def save_tasks_to_file(path: str, roots: List[Task]):
    lines = []
    for t in flatten_tasks(roots):
        indent = " " * 4 * t.depth
        line = f"{indent}{t.name}:{t.status}:{t.due}"
        lines.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def status_style(status: str) -> str:
    if status == "DONE":
        return "green"
    elif status == "IN_PROGRESS":
        return "yellow"
    else:
        return "red"

def status_symbol(status: str) -> str:
    return {
        "OPEN": "○",
        "IN_PROGRESS": "◐",
        "DONE": "●",
    }.get(status, "?")

class NewTaskScreen(ModalScreen[Optional[tuple[str, str]]]):
    """Modular dialog for adding a new task."""

    def compose(self) -> ComposeResult:
        yield Vertical(
            Static("Add new task", id="title"),
            Input(placeholder="Name", id="name"),
            Input(placeholder="Due (optional)", id="due"),
            Horizontal(
                Button("OK", id="ok"),
                Button("Cancel", id="cancel"),
                id="buttons",
            ),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ok":
            name = self.query_one("#name", Input).value.strip()
            due = self.query_one("#due", Input).value.strip()

            if not name:
                # No name? No task!
                return

            # Verhindere kaputte Dateiformate
            if ":" in name or ":" in due:
                # Kleine Rückmeldung an den Nutzer
                self.app.notify(
                    "':' is not allowed in task name or due field.",
                    severity="warning",
                )
                return

            self.dismiss((name, due))
        else:
            self.dismiss(None)

class LaunchConditionsApp(App):
    CSS = """
    Screen {
        align: center middle;
    }

    #summary {
        width: 100%;
        padding: 0 1;
    }

    ListView {
        width: 100%;
        height: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("s", "save", "Save"),
        ("a", "add_subtask", "Add subtask"),
        ("space", "toggle_status", "Toggle status"),
    ]

    def __init__(self, task_file: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self.task_file = task_file
        self.title = "Launch Conditions [{}]".format(task_file)
        self.roots: List[Task] = []

    def save_with_handling(self, show_success: bool = False) -> bool:
        """Save tasks to file with error handling.

        Returns:
            True if save succeeded, False if there was an error.
        """
        try:
            save_tasks_to_file(self.task_file, self.roots)
        except OSError as e:
            # Show Error in UI and log to std.err
            self.notify(
                f"ERROR saving {self.task_file}: {e}",
                severity="error",
            )
            print(f"[launchconditions] ERROR saving {self.task_file}: {e}", file=sys.stderr)
            return False
        else:
            if show_success:
                self.notify(f"Saved to {self.task_file}", severity="information")
            return True

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static("", id="summary")
        yield ListView(id="task_list")
        yield Footer()

    def on_mount(self) -> None:
        self.roots = parse_tasks_from_file(self.task_file)
        self.refresh_task_list(keep_selection=False)

        list_view = self.get_task_list()
        if list_view.children:
            list_view.index = 0
            list_view.focus()

    # --- Helper functions ---

    def get_task_list(self) -> ListView:
        return self.query_one("#task_list", ListView)

    def visible_tasks(self) -> List[Task]:
        return flatten_tasks(self.roots)

    def update_summary(self, tasks: Optional[List[Task]] = None) -> None:
        """Update the summary line with counts of tasks by status."""
        if tasks is None:
            tasks = self.visible_tasks()

        open_count = sum(1 for t in tasks if t.status == "OPEN")
        in_progress_count = sum(1 for t in tasks if t.status == "IN_PROGRESS")
        done_count = sum(1 for t in tasks if t.status == "DONE")

        summary_text = f"OPEN: {open_count}  |  IN_PROGRESS: {in_progress_count}  |  DONE: {done_count}"
        summary = self.query_one("#summary", Static)
        summary.update(summary_text)

    def refresh_task_list(self, keep_selection: bool = True) -> None:
        """Refresh ListView from current model."""
        task_list_view = self.get_task_list()
        had_focus = task_list_view.has_focus
        old_index = task_list_view.index if keep_selection else None

        task_list_view.clear()

        tasks = self.visible_tasks()
        self.update_summary(tasks)

        for task in tasks:
            prefix = "  " * task.depth
            sym = status_symbol(task.status)
            text = f"{prefix}{sym} {task.name}"
            if task.due:
                text += f"  (due: {task.due})"
            style = status_style(task.status)
            rich_text = Text(text, style=style)
            task_list_view.append(ListItem(Label(rich_text)))

        if tasks:
            if keep_selection and old_index is not None:
                task_list_view.index = min(old_index, len(tasks) - 1)
            else:
                task_list_view.index = 0

            if had_focus:
                task_list_view.focus()
        else:
            # No tasks → no index, no focus
            task_list_view.index = None

            if had_focus and task_list_view.index is not None:
                task_list_view.focus()

    def get_selected_task(self) -> Optional[Task]:
        list_view = self.get_task_list()
        idx = list_view.index
        if idx is None:
            return None
        tasks = self.visible_tasks()
        if not (0 <= idx < len(tasks)):
            return None
        return tasks[idx]

    # --- Actions ---

    def action_toggle_status(self) -> None:
        task = self.get_selected_task()
        if task is None:
            return
        if not task.is_leaf():
            return

        try:
            idx = STATUS_CYCLE.index(task.status)
        except ValueError:
            idx = 0

        task.status = STATUS_CYCLE[(idx + 1) % len(STATUS_CYCLE)]

        task.propagate_up()

        self.refresh_task_list()
        self.save_with_handling()

    def action_add_subtask(self) -> None:
        """Create a new (sub)task – starts Worker."""
        parent = self.get_selected_task()
        self.run_worker(self._add_subtask_worker(parent), exclusive=True)

    async def _add_subtask_worker(self, parent: Optional[Task]) -> None:
        """Worker, shows a modal dialogue, adds task."""
        result = await self.push_screen_wait(NewTaskScreen())
        if result is None:
            return

        name, due = result

        if parent is None:
            # First Root-Task
            new_root = Task(name=name, status="OPEN", due=due, depth=0)
            self.roots.append(new_root)
            new_root.propagate_up()
        else:
            # Subtask under current Task
            new = Task(
                name=name,
                status="OPEN",
                due=due,
                depth=parent.depth + 1,
                parent=parent,
            )
            parent.children.append(new)
            new.propagate_up()

        self.refresh_task_list()
        self.save_with_handling()

    def action_save(self) -> None:
        self.save_with_handling(show_success=True)
        self.notify(f"Saved to {self.task_file}", severity="information")

    def action_quit(self) -> None:
        # Save before quitting
        self.save_with_handling()
        self.exit()

def main():
    if len(sys.argv) != 2:
        print("Usage: launchconditions_textual.py <task_file.lc>")
        print("       No task_file? just create an empty text file")
        sys.exit(1)
    task_file = sys.argv[1]
    app = LaunchConditionsApp(task_file)
    app.run()

if __name__ == "__main__":
    main()