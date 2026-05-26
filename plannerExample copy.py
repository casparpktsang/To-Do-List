from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DATA_FILE = APP_DIR / "planner2_data.json"
TODAY = date.today()


@dataclass
class TaskItem:
    id: int
    title: str
    due_date: str
    priority: str
    completed: bool = False
    created_at: str = ""


DEFAULT_TASKS = [
    TaskItem(1, "Plan weekly priorities", TODAY.isoformat(), "High", False, datetime.now().isoformat()),
    TaskItem(2, "Review calendar and inbox", TODAY.isoformat(), "Medium", False, datetime.now().isoformat()),
]


def _serialize(tasks: list[TaskItem], next_id: int) -> dict[str, Any]:
    return {
        "tasks": [asdict(task) for task in tasks],
        "next_id": next_id,
    }


def _deserialize(payload: dict[str, Any]) -> tuple[list[TaskItem], int]:
    raw_tasks = payload.get("tasks", [])
    tasks: list[TaskItem] = []
    for item in raw_tasks:
        tasks.append(
            TaskItem(
                id=int(item.get("id", 0)),
                title=str(item.get("title", "")).strip(),
                due_date=str(item.get("due_date", TODAY.isoformat())),
                priority=str(item.get("priority", "Medium")),
                completed=bool(item.get("completed", False)),
                created_at=str(item.get("created_at", "")),
            )
        )

    next_id = int(payload.get("next_id", 1))
    valid_tasks = [task for task in tasks if task.id > 0 and task.title]
    return valid_tasks, next_id


def load_state() -> tuple[list[TaskItem], int]:
    if DATA_FILE.exists():
        try:
            with DATA_FILE.open("r", encoding="utf-8") as file:
                tasks, next_id = _deserialize(json.load(file))
                if tasks:
                    return tasks, max(next_id, max(task.id for task in tasks) + 1)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass

    return list(DEFAULT_TASKS), 3


def save_state() -> None:
    with DATA_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            _serialize(st.session_state.tasks, st.session_state.next_task_id),
            file,
            indent=2
        )


def ensure_state() -> None:
    if "tasks" not in st.session_state or "next_task_id" not in st.session_state:
        tasks, next_id = load_state()
        st.session_state.tasks = tasks
        st.session_state.next_task_id = next_id


def _set_page_style() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: radial-gradient(circle at top left, #f3f7ff 0%, #edf2ff 35%, #f8faff 100%);
            }
            .main .block-container {
                max-width: 900px;
                padding-top: 2rem;
                padding-bottom: 3rem;
            }
            .hero {
                background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 50%, #3b82f6 100%);
                border-radius: 18px;
                padding: 1.25rem 1.5rem;
                color: #ffffff;
                box-shadow: 0 14px 30px rgba(30, 58, 138, 0.25);
                margin-bottom: 1.2rem;
            }
            .hero h1 {
                margin: 0;
                font-size: 1.7rem;
                font-weight: 700;
            }
            .hero p {
                margin: 0.35rem 0 0;
                opacity: 0.95;
                font-size: 0.95rem;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 0.7rem;
                margin: 0.3rem 0 1rem;
            }
            .stat-card {
                background: rgba(255, 255, 255, 0.92);
                border: 1px solid #dbe7ff;
                border-radius: 14px;
                padding: 0.7rem 0.85rem;
            }            
            .stat-card .label {
                color: #4b5563;
                font-size: 0.78rem;
            }
            .stat-card .value {
                margin-top: 0.2rem;
                color: #111827;
                font-size: 1.2rem;
                font-weight: 700;
            }
            .task-card {
                background: rgba(255, 255, 255, 0.96);
                border: 1px solid #dbe7ff;
                border-radius: 14px;
                padding: 0.8rem 0.9rem;
                margin-bottom: 0.65rem;
                box-shadow: 0 3px 10px rgba(37, 99, 235, 0.06);
            }
            .task-title {
                font-weight: 600;
                font-size: 1.02rem;
                color: #0f172a;
            }
            .task-meta {
                color: #475569;
                font-size: 0.83rem;
                margin-top: 0.25rem;
            }
            .chip {
                display: inline-block;
                border-radius: 999px;
                font-size: 0.72rem;
                padding: 0.17rem 0.52rem;
                margin-left: 0.4rem;
                border: 1px solid transparent;
            }
            .chip-high {
                background: #fee2e2;
                color: #991b1b;
                border-color: #fecaca;
            }
            .chip-medium {
                background: #fef3c7;
                color: #92400e;
                border-color: #fde68a;
            }
            .chip-low {
                background: #dcfce7;
                color: #166534;
                border-color: #bbf7d0;
            }
            @media (max-width: 900px) {
                .stats-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _priority_chip(priority: str) -> str:
    lower = priority.lower()
    chip_class = "chip-medium"
    if lower == "high":
        chip_class = "chip-high"
    elif lower == "low":
        chip_class = "chip_low"
    return f"<span class='chip {chip_class}'>{priority}</span>"


def add_task(title: str, due_date: date, priority: str) -> None:
    st.session_state.tasks.append(
        TaskItem(
            id=st.session_state.next_task_id,
            title=title.strip(),
            due_date=due_date.isoformat(),
            priority=priority,
            completed=False,
            created_at=datetime.now().isoformat(timespec="seconds"),
        )
    )
    st.session_state.next_task_id += 1
    save_state()


def remove_task(task_id: int) -> None:
    st.session_state.tasks = [task for task in st.session_state.tasks if task.id != task_id]
    save_state()


def toggle_task(task_id: int, checked: bool) -> None:
    for task in st.session_state.tasks:
        if task.id == task.id:
            task.completed = checked
            break
    save_state()


def clear_completed() -> None:
    st.session_state.tasks = [task for task in st.session_state.tasks if not task.completed]
    save_state()


def render_stats(tasks: list[TaskItem]) -> None:
    total = len(tasks)
    completed = sum(1 for task in tasks if task.completed)
    pending = total - completed
    due_today = sum(1 for task in tasks if task.due_date == TODAY.isoformat() and not task.completed)

    percent = int((completed / total) * 100) if total else 0

    st.markdown(
        f"""
        <div class='stats-grid'>
            <div class='stat-card'><div class='label'>Total</div><div class='value'>{total}</div></div>
            <div class='stat-card'><div class='label'>Pending</div><div class='value'>{pending}</div></div>
            <div class='stat-card'><div class='label'>Done</div><div class='value'>{completed}</div></div>
            <div class='stat-card'><div class='label'>Progress</div><div class='value'>{percent}%</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.progress(percent / 100)
    if due_today:
        st.info(f"{due_today} task(s) are due today.")


def render_task(task: TaskItem) -> None:
    due = datetime.strptime(task.due_date, "%Y-%m-%d").strftime("%b %d, %Y")
    checkbox_col, content_col, action_col = st.columns([0.12, 0.72, 0.16], vertical_alignment="center")

    with checkbox_col:
        checked = st.checkbox(
            "Done",
            value=task.completed,
            key=f"task_check_{task.id}",
            label_visibility="collapsed",
        )
        if checked != task.completed:
            toggle_task(task.id, checked)
            st.rerun()

    with content_col:
        title_text = f"✅ {task.title}" if task.completed else task.title
        st.markdown(
            f"""
            <div class='task-card'>
                <div class='task-title'>{title_text}{_priority_chip(task.priority)}</div>
                <div class='task-meta'>Due {due}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with action_col:
        if st.button("Delete", key=f"delete_{task.id}", use_container_width=True):
            remove_task(task.id)
            st.rerun()


def sort_tasks(tasks: list[TaskItem], order: str) -> list[TaksItem]:
    priority_rank = {"High": 0, "Medium": 1, "Low": 2}

    if order == "Due date":
        return sorted(tasks, key=lambda task: (task.completed, task.due_date, priority_rank.get(task.priority, 3), task.id))
    if order == "Priority":
         return sorted(
             tasks,
             key=lambda task: (task.completed, priority_rank.get(task.priority, 3), task.due_date, task.id),
         )
    return sorted(tasks, key=lambda task: (task.completed, task.id))


def run() -> None:
    st.set_page_config(page_title="Planner 2", page_icon="✅", layout="centered")
    ensure_state()
    _set_page_style()

    st.markdown(
        """
        <div class='hero'>
            <h1>Planner 2</h1>
            <p>Organize your day with a clean, modern to-do list.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.form("new_task_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([0.52, 0.26, 0.22], vertical_alignment="bottom")
        with col1:
            title = st.text_input("Task", placeholder= "Add a new task...")
        with col2:
            due_date = st.date_input("Due", value=TODAY, min_value=date(2000, 1, 1))
        with col3:
            priority = st.selectbox("Priority", ["High", "Medium", "Low"], index=1)

        submitted = st.form_submit_button("Add Task", use_container_width=True)
        if submitted:
            if not title.strip():
                st.warning("Please enter a task title.")
            else:
                add_task(title, due_date, priority)
                st.success("Task added.")
                st.rerun()

    tasks: list[TaskItem] = st.session_state.tasks
    render_stats(tasks)

    filter_col, sort_col, clear_col = st.columns([0.38, 0.38, 0.24], vertical_alignment="bottom")
    with filter_col:
        view_filter = st.selectbox("View", ["All", "Pending", "Completed"], index=0)
    with sort_col:
        sort_order = st.selectbox("Sort by", ["Created", "Due date", "Priority"], index=1)
    with clear_col:
        if st.button("Clear done", use_container_width=True):
            clear_completed()
            st.rerun()

    visible_tasks = tasks
    if view_filter == "Pending":
        visible_tasks = [task for task in tasks if not task.completed]
    elif view_filter == "Completed":
        visible_tasks = [task for task in tasks if task.completed]

    visible_tasks = sort_tasks(visible_tasks, sort_order)

    if not visible_tasks:
        st.markdown("### No tasks in the view")
        st.caption("Add a task or switch filters to see your items.")
    else:
        for task in visible_tasks:
            render_task(task)


if __name__ == "__main__":
    run()
