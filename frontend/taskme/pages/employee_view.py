from __future__ import annotations

import reflex as rx

from taskme.components.navbar import navbar
from taskme.components.task_card import task_card
from taskme.state.task_state import TaskState


def _progress_controls(task: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.slider(
            default_value=task["progress"],
            min_=0, max_=100, step=1,
            on_value_commit=lambda v: TaskState.update_progress(task["id"], v[0]),
            width="100%",
        ),
        rx.input(
            value=task["progress"].to_string(), width="90px",
            on_blur=lambda v: TaskState.update_progress(task["id"], v),
        ),
        spacing="3", width="100%", align="center",
    )


# ── Comments dialog (shared with CEO but reused here) ──────────────────────

def _comments_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("message-square", size=20, color="#F97316"),
                    rx.text("Comments", font_size="1.2rem", font_weight="900", color="#1A1A1A"),
                    rx.spacer(),
                    rx.text(TaskState.comments_task_title, color="#6B7280", font_size="0.85rem",
                            max_width="200px", overflow="hidden", text_overflow="ellipsis",
                            white_space="nowrap"),
                    width="100%", align="center",
                ),
                rx.divider(border_color="rgba(251,146,60,0.25)"),
                rx.box(
                    rx.cond(
                        TaskState.comments_loading,
                        rx.center(rx.spinner(), padding="2rem"),
                        rx.cond(
                            TaskState.comments.length() > 0,
                            rx.vstack(
                                rx.foreach(
                                    TaskState.comments,
                                    lambda c: rx.box(
                                        rx.hstack(
                                            rx.box(
                                                rx.text(c["author_name"][:1].to_string(),
                                                        color="white", font_weight="700", font_size="0.75rem"),
                                                width="28px", height="28px", border_radius="50%",
                                                background_color="#F97316",
                                                display="flex", align_items="center",
                                                justify_content="center", flex_shrink="0",
                                            ),
                                            rx.vstack(
                                                rx.hstack(
                                                    rx.text(c["author_name"], font_weight="700",
                                                            color="#1A1A1A", font_size="0.85rem"),
                                                    rx.text(c["created_at"].to_string(),
                                                            color="#9CA3AF", font_size="0.72rem"),
                                                    spacing="2", align="center",
                                                ),
                                                rx.text(c["body"], color="#374151", font_size="0.88rem",
                                                        white_space="pre-wrap"),
                                                spacing="1", align="start", width="100%",
                                            ),
                                            spacing="3", align="start", width="100%",
                                        ),
                                        padding="0.6rem", border_radius="8px",
                                        background_color="#FFF8F3", width="100%",
                                    ),
                                ),
                                spacing="2", width="100%",
                            ),
                            rx.center(
                                rx.vstack(
                                    rx.icon("message-square", size=32, color="#D1D5DB"),
                                    rx.text("No comments yet", color="#9CA3AF", font_size="0.9rem"),
                                    spacing="2", align="center",
                                ),
                                padding="2rem",
                            ),
                        ),
                    ),
                    max_height="40vh", overflow_y="auto", width="100%", padding="0.25rem",
                ),
                rx.divider(border_color="rgba(251,146,60,0.25)"),
                rx.hstack(
                    rx.text_area(
                        placeholder="Write a comment...",
                        value=TaskState.new_comment_body,
                        on_change=TaskState.set_new_comment_body,
                        width="100%", min_height="60px", max_height="100px",
                    ),
                    rx.button(rx.icon("send", size=16), color_scheme="orange", size="2",
                              on_click=TaskState.post_comment),
                    spacing="2", width="100%", align="end",
                ),
                spacing="3", padding="1.5rem", background_color="#FFFFFF",
                border_radius="12px", width="100%",
            ),
            max_width="600px",
        ),
        open=TaskState.show_comments_dialog, on_open_change=TaskState.set_comments_dialog_open,
    )


# ── Preview dialog ──────────────────────────────────────────────────────────

def _preview_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("eye", size=18, color="#F97316"),
                    rx.text("Preview", font_size="1.1rem", font_weight="900", color="#1A1A1A"),
                    rx.spacer(),
                    rx.text(TaskState.preview_file_name, color="#6B7280", font_size="0.85rem"),
                    width="100%", align="center",
                ),
                rx.divider(border_color="rgba(251,146,60,0.25)"),
                rx.box(
                    rx.cond(
                        TaskState.preview_is_image,
                        rx.el.img(
                            id="taskme-preview-img", src="",
                            alt=TaskState.preview_file_name,
                            style={"max_width": "100%", "max_height": "60vh",
                                   "border_radius": "8px", "object_fit": "contain"},
                        ),
                        rx.cond(
                            TaskState.preview_is_pdf,
                            rx.el.iframe(
                                id="taskme-preview-frame", src="",
                                width="100%", height="500px",
                                style={"border": "none", "border_radius": "8px"},
                            ),
                            rx.center(
                                rx.vstack(
                                    rx.icon("file", size=48, color="#D1D5DB"),
                                    rx.text("Preview not available for this file type.",
                                            color="#6B7280", font_size="0.9rem"),
                                    rx.text("Click download to view the file.",
                                            color="#9CA3AF", font_size="0.82rem"),
                                    spacing="2", align="center",
                                ),
                                padding="3rem",
                            ),
                        ),
                    ),
                    width="100%", min_height="200px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.hstack(
                    rx.button("Close", variant="outline", on_click=TaskState.close_preview),
                    justify="end", width="100%",
                ),
                spacing="3", padding="1.5rem", background_color="#FFFFFF",
                border_radius="12px", width="100%",
            ),
            max_width="720px",
        ),
        open=TaskState.show_preview_dialog, on_open_change=TaskState.set_preview_dialog_open,
    )


# ── Page ────────────────────────────────────────────────────────────────────

@rx.page(route="/tasks", title="Taskme · My Tasks",
         on_load=[TaskState.load_employee_tasks, TaskState.request_notification_permission])
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
                        rx.button("Refresh", variant="outline",
                                  on_click=TaskState.load_employee_tasks),
                        width="100%", align="center",
                    ),
                    rx.cond(TaskState.toast != "",
                            rx.callout(TaskState.toast, color_scheme="blue"), rx.box()),
                    rx.cond(
                        TaskState.is_loading,
                        rx.center(rx.spinner()),
                        rx.vstack(
                            rx.foreach(
                                TaskState.tasks,
                                lambda t: rx.box(
                                    task_card(t),
                                    _progress_controls(t),
                                    padding="0.75rem", border_radius="16px",
                                    border="1px solid rgba(251,146,60,0.3)",
                                    background_color="#FFFFFF", width="100%",
                                ),
                            ),
                            spacing="4", width="100%",
                        ),
                    ),
                    # Dialogs
                    _comments_dialog(),
                    _preview_dialog(),
                    rx.moment(interval=10_000, on_change=TaskState.poll_notifications, display="none"),
                    padding="1.5rem", max_width="900px", margin_x="auto",
                ),
                background_color="#FFF8F3", min_height="100vh",
            ),
        ),
    )
