from __future__ import annotations

import reflex as rx

from taskme.components.navbar import navbar
from taskme.components.task_card import task_card
from taskme.state.task_state import TaskState


def _progress_controls(task: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.slider(
            default_value=task["progress"],
            min_=0,
            max_=100,
            step=1,
            on_value_commit=lambda v: TaskState.update_progress(task["id"], v[0]),
            width="100%",
        ),
        rx.input(
            value=task["progress"].to_string(),
            width="90px",
            on_blur=lambda v: TaskState.update_progress(task["id"], v),
        ),
        spacing="3",
        width="100%",
        align="center",
    )


@rx.page(route="/tasks", title="Taskme · My Tasks", on_load=[TaskState.load_employee_tasks, TaskState.request_notification_permission])
def employee_tasks() -> rx.Component:
    return rx.cond(
        ~TaskState.is_hydrated,
        rx.center(rx.spinner(), min_height="100vh", background_color="#FFF8F3"),
        rx.cond(
            ~TaskState.is_employee,
            rx.center(rx.spinner(), min_height="100vh", background_color="#FFF8F3"),
            rx.box(
                navbar(),
                rx.box(
                    rx.hstack(
                        rx.text("My Tasks", font_size="1.4rem", font_weight="900", color="#1A1A1A"),
                        rx.spacer(),
                        rx.button("Refresh", variant="outline", on_click=TaskState.load_employee_tasks),
                        width="100%",
                        align="center",
                    ),
                    rx.cond(TaskState.toast != "", rx.callout(TaskState.toast, color_scheme="blue"), rx.box()),
                    rx.cond(
                        TaskState.is_loading,
                        rx.center(rx.spinner()),
                        rx.vstack(
                            rx.foreach(
                                TaskState.tasks,
                                lambda t: rx.box(
                                    task_card(t),
                                    _progress_controls(t),
                                    padding="0.75rem",
                                    border_radius="16px",
                                border="1px solid rgba(251,146,60,0.3)",
                                background_color="#FFFFFF",
                                    width="100%",
                                ),
                            ),
                            spacing="4",
                            width="100%",
                        ),
                    ),
                    # Reflex no longer exposes rx.interval; use rx.moment as a timer.
                    rx.moment(interval=10_000, on_change=TaskState.poll_notifications, display="none"),
                    padding="1.5rem",
                    max_width="900px",
                    margin_x="auto",
                ),
                background_color="#FFF8F3",
                min_height="100vh",
            ),
        ),
    )