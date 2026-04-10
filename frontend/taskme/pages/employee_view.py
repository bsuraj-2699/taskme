from __future__ import annotations

import reflex as rx

from taskme.components.navbar import navbar
from taskme.components.task_card import task_card
from taskme.state.task_state import TaskState


def _progress_controls(task: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.slider(default_value=task["progress"], min_=0, max_=100, step=1,
                  on_value_commit=lambda v: TaskState.update_progress(task["id"], v[0]), width="100%"),
        rx.input(value=task["progress"].to_string(), width="90px",
                 on_blur=lambda v: TaskState.update_progress(task["id"], v)),
        spacing="3", width="100%", align="center",
    )


def _submission_section(task: rx.Var) -> rx.Component:
    """Per-task submission buttons for employees."""
    return rx.hstack(
        rx.button(
            rx.hstack(
                rx.icon("upload-cloud", size=14),
                rx.text("Submit Work", font_size="0.85rem"),
                spacing="2", align="center",
            ),
            color_scheme="green", variant="outline", size="1",
            on_click=TaskState.open_submissions_dialog(task["id"]),
        ),
        rx.cond(
            task["submission_count"] > 0,
            rx.badge(task["submission_count"].to_string() + " submitted",
                     color_scheme="green", variant="soft", size="1"),
            rx.box(),
        ),
        spacing="2", width="100%", align="center",
    )


# ── Shared dialogs ──────────────────────────────────────────────────────────

def _comments_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(rx.icon("message-square", size=20, color="#F97316"),
                          rx.text("Comments", font_size="1.2rem", font_weight="900", color="#1A1A1A"),
                          rx.spacer(),
                          rx.text(TaskState.comments_task_title, color="#6B7280", font_size="0.85rem",
                                  max_width="200px", overflow="hidden", text_overflow="ellipsis",
                                  white_space="nowrap"),
                          width="100%", align="center"),
                rx.divider(border_color="rgba(251,146,60,0.25)"),
                rx.box(
                    rx.cond(TaskState.comments_loading, rx.center(rx.spinner(), padding="2rem"),
                            rx.cond(TaskState.comments.length() > 0,
                                    rx.vstack(rx.foreach(TaskState.comments,
                                        lambda c: rx.box(rx.hstack(
                                            rx.box(rx.text(c["author_name"][:1].to_string(), color="white",
                                                          font_weight="700", font_size="0.75rem"),
                                                   width="28px", height="28px", border_radius="50%",
                                                   background_color="#F97316", display="flex",
                                                   align_items="center", justify_content="center", flex_shrink="0"),
                                            rx.vstack(rx.hstack(rx.text(c["author_name"], font_weight="700",
                                                                        color="#1A1A1A", font_size="0.85rem"),
                                                                rx.text(c["created_at"].to_string(), color="#9CA3AF",
                                                                        font_size="0.72rem"), spacing="2", align="center"),
                                                      rx.text(c["body"], color="#374151", font_size="0.88rem",
                                                              white_space="pre-wrap"),
                                                      spacing="1", align="start", width="100%"),
                                            spacing="3", align="start", width="100%"),
                                            padding="0.6rem", border_radius="8px", background_color="#FFF8F3", width="100%")),
                                        spacing="2", width="100%"),
                                    rx.center(rx.vstack(rx.icon("message-square", size=32, color="#D1D5DB"),
                                                        rx.text("No comments yet", color="#9CA3AF"),
                                                        spacing="2", align="center"), padding="2rem"))),
                    max_height="40vh", overflow_y="auto", width="100%", padding="0.25rem"),
                rx.divider(border_color="rgba(251,146,60,0.25)"),
                rx.hstack(rx.text_area(placeholder="Write a comment...", value=TaskState.new_comment_body,
                                       on_change=TaskState.set_new_comment_body, width="100%",
                                       min_height="60px", max_height="100px"),
                          rx.button(rx.icon("send", size=16), color_scheme="orange", size="2",
                                    on_click=TaskState.post_comment),
                          spacing="2", width="100%", align="end"),
                spacing="3", padding="1.5rem", background_color="#FFFFFF", border_radius="12px", width="100%"),
            max_width="600px"),
        open=TaskState.show_comments_dialog, on_open_change=TaskState.set_comments_dialog_open)


def _preview_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(rx.icon("eye", size=18, color="#F97316"),
                          rx.text("Preview", font_size="1.1rem", font_weight="900", color="#1A1A1A"),
                          rx.spacer(), rx.text(TaskState.preview_file_name, color="#6B7280", font_size="0.85rem"),
                          width="100%", align="center"),
                rx.divider(border_color="rgba(251,146,60,0.25)"),
                rx.box(
                    rx.cond(TaskState.preview_is_image,
                            rx.el.img(id="taskme-preview-img", src="", alt=TaskState.preview_file_name,
                                      style={"max_width": "100%", "max_height": "60vh", "border_radius": "8px",
                                             "object_fit": "contain"}),
                            rx.cond(TaskState.preview_is_pdf,
                                    rx.el.iframe(id="taskme-preview-frame", src="", width="100%", height="500px",
                                                 style={"border": "none", "border_radius": "8px"}),
                                    rx.center(rx.vstack(rx.icon("file", size=48, color="#D1D5DB"),
                                                        rx.text("Preview not available for this file type.", color="#6B7280"),
                                                        rx.text("Click download to view.", color="#9CA3AF", font_size="0.82rem"),
                                                        spacing="2", align="center"), padding="3rem"))),
                    width="100%", min_height="200px", display="flex", align_items="center", justify_content="center"),
                rx.hstack(rx.button("Close", variant="outline", on_click=TaskState.close_preview),
                          justify="end", width="100%"),
                spacing="3", padding="1.5rem", background_color="#FFFFFF", border_radius="12px", width="100%"),
            max_width="720px"),
        open=TaskState.show_preview_dialog, on_open_change=TaskState.set_preview_dialog_open)


def _submissions_dialog() -> rx.Component:
    """View past submissions for a task."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(rx.icon("folder-open", size=20, color="#22C55E"),
                          rx.text("Submissions", font_size="1.2rem", font_weight="900", color="#1A1A1A"),
                          rx.spacer(),
                          rx.text(TaskState.submissions_task_title, color="#6B7280", font_size="0.85rem"),
                          width="100%", align="center"),
                rx.divider(border_color="rgba(34,197,94,0.25)"),

                # ── Upload zone ─────────────────────────────────────────
                rx.vstack(
                    rx.text("Upload Your Work", color="#1A1A1A", font_size="0.88rem", font_weight="700"),
                    rx.upload(
                        rx.vstack(
                            rx.icon("file-up", color="#9CA3AF", size=20),
                            rx.text("Drop files or click to select", color="#6B7280", font_size="0.82rem"),
                            spacing="2", align="center", padding="0.75rem",
                        ),
                        id="submission_upload",
                        multiple=True,
                        border="2px dashed rgba(34,197,94,0.35)",
                        border_radius="10px", width="100%",
                    ),
                    rx.button(
                        rx.hstack(rx.icon("send", size=14), rx.text("Submit Files", font_size="0.85rem"),
                                  spacing="2", align="center"),
                        color_scheme="green", size="2", width="100%",
                        on_click=TaskState.upload_submission(
                            rx.upload_files(upload_id="submission_upload")
                        ),
                    ),
                    spacing="2", width="100%", padding="0.6rem",
                    border="1px solid rgba(34,197,94,0.25)", border_radius="10px",
                    background_color="rgba(34,197,94,0.04)",
                ),

                rx.divider(border_color="rgba(34,197,94,0.15)"),

                # ── Past submissions list ───────────────────────────────
                rx.cond(
                    TaskState.submissions_loading,
                    rx.center(rx.spinner(), padding="2rem"),
                    rx.cond(
                        TaskState.submissions.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                TaskState.submissions,
                                lambda s: rx.hstack(
                                    rx.icon("file-check", size=16, color="#22C55E"),
                                    rx.vstack(
                                        rx.text(s["file_name"], font_weight="600", color="#1A1A1A", font_size="0.88rem"),
                                        rx.text(s["uploaded_at"].to_string(), color="#9CA3AF", font_size="0.72rem"),
                                        spacing="0",
                                    ),
                                    rx.spacer(),
                                    rx.icon_button(rx.icon("eye", size=13), size="1", variant="ghost", color_scheme="green",
                                                   on_click=TaskState.open_submission_preview(
                                                       TaskState.submissions_task_id, s["id"], s["file_name"]),
                                                   title="Preview"),
                                    rx.icon_button(rx.icon("download", size=13), size="1", variant="ghost", color_scheme="green",
                                                   on_click=TaskState.download_submission(
                                                       TaskState.submissions_task_id, s["id"], s["file_name"]),
                                                   title="Download"),
                                    width="100%", align="center", padding="0.5rem",
                                    border="1px solid rgba(34,197,94,0.2)", border_radius="8px",
                                ),
                            ),
                            spacing="2", width="100%",
                        ),
                        rx.center(rx.text("No submissions yet.", color="#9CA3AF"), padding="2rem"),
                    ),
                ),
                rx.hstack(rx.button("Close", variant="outline",
                                    on_click=lambda: TaskState.set_submissions_dialog_open(False)),
                          justify="end", width="100%"),
                spacing="3", padding="1.5rem", background_color="#FFFFFF", border_radius="12px", width="100%",
            ),
            max_width="600px",
        ),
        open=TaskState.show_submissions_dialog, on_open_change=TaskState.set_submissions_dialog_open,
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
                    rx.hstack(rx.text("My Tasks", font_size="1.4rem", font_weight="900", color="#1A1A1A"),
                              rx.spacer(),
                              rx.button("Refresh", variant="outline", on_click=TaskState.load_employee_tasks),
                              width="100%", align="center"),
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
                                    _submission_section(t),
                                    padding="0.75rem", border_radius="16px",
                                    border="1px solid rgba(251,146,60,0.3)",
                                    background_color="#FFFFFF", width="100%",
                                ),
                            ),
                            spacing="4", width="100%",
                        ),
                    ),
                    _comments_dialog(),
                    _preview_dialog(),
                    _submissions_dialog(),
                    rx.moment(interval=10_000, on_change=TaskState.poll_notifications, display="none"),
                    padding="1.5rem", max_width="900px", margin_x="auto",
                ),
                background_color="#FFF8F3", min_height="100vh",
            ),
        ),
    )
