from __future__ import annotations

import reflex as rx

from taskme.components.task_card import task_card
from taskme.state.task_state import TaskState


def _employee_page_styles() -> rx.Component:
    return rx.el.style(
        """
        @keyframes taskme-progress-gradient {
          0%, 100% { background-position: 0% 50%; }
          50% { background-position: 100% 50%; }
        }
        """
    )


def _mini_stat_card(label: str, value, icon_name: str, accent: str, bg: str) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon(icon_name, size=20, color=accent),
                padding="0.55rem",
                border_radius="12px",
                background_color=bg,
            ),
            rx.vstack(
                rx.text(value.to_string(), font_weight="900", font_size="1.35rem", color="#0F172A"),
                rx.text(label, font_size="0.72rem", color="#64748B", font_weight="600"),
                spacing="0",
                align_items="start",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        padding="0.85rem",
        border_radius="14px",
        border="1px solid rgba(15, 23, 42, 0.07)",
        background_color="#FFFFFF",
        box_shadow="0 2px 12px rgba(15, 23, 42, 0.05)",
        width="100%",
    )


def _employee_mini_stats() -> rx.Component:
    return rx.grid(
        _mini_stat_card(
            "Completed today",
            TaskState.employee_stat_completed_today,
            "check-circle",
            "#16A34A",
            "rgba(22, 163, 74, 0.14)",
        ),
        _mini_stat_card(
            "Pending tasks",
            TaskState.employee_stat_pending,
            "circle-dashed",
            "#CA8A04",
            "rgba(202, 138, 4, 0.15)",
        ),
        _mini_stat_card(
            "Overdue",
            TaskState.employee_stat_overdue,
            "alert-circle",
            "#DC2626",
            "rgba(220, 38, 38, 0.12)",
        ),
        _mini_stat_card(
            "Avg completion time",
            TaskState.employee_stat_avg_completion_days,
            "timer",
            "#2563EB",
            "rgba(37, 99, 235, 0.12)",
        ),
        columns={"initial": "1", "sm": "2"},
        spacing="3",
        width="100%",
    )


def _progress_controls(task: rx.Var) -> rx.Component:
    return rx.hstack(
        rx.slider(default_value=task["progress"], min_=0, max_=100, step=1,
                  on_value_commit=lambda v: TaskState.update_progress(task["id"], v[0]), width="100%"),
        rx.input(value=task["progress"].to_string(), width="90px",
                 on_blur=lambda v: TaskState.update_progress(task["id"], v)),
        spacing="3", width="100%", align="center",
    )


def _submission_section(task: rx.Var) -> rx.Component:
    """Per-task submission: primary CTA or submitted state (still opens dialog)."""
    return rx.hstack(
        rx.cond(
            task["submission_count"] > 0,
            rx.button(
                rx.hstack(
                    rx.icon("check-circle-2", size=16, color="white"),
                    rx.text("Submitted", font_size="0.88rem", font_weight="700", color="white"),
                    rx.text("✓", font_size="0.95rem", font_weight="800", color="white"),
                    spacing="2",
                    align="center",
                ),
                color_scheme="green",
                variant="solid",
                size="2",
                width="100%",
                on_click=TaskState.open_submissions_dialog(task["id"]),
            ),
            rx.button(
                rx.hstack(
                    rx.icon("upload-cloud", size=16),
                    rx.text("Submit Work", font_size="0.88rem", font_weight="600"),
                    spacing="2",
                    align="center",
                ),
                color_scheme="green",
                variant="outline",
                size="2",
                width="100%",
                on_click=TaskState.open_submissions_dialog(task["id"]),
            ),
        ),
        spacing="2",
        width="100%",
        align="center",
    )


# ── Pagination controls ────────────────────────────────────────────────────

def _employee_pagination() -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.hstack(rx.icon("chevron-left", size=14), rx.text("Prev"), spacing="1", align="center"),
            on_click=TaskState.go_prev_page,
            is_disabled=~TaskState.has_prev_page,
            variant="outline",
            size="2",
            color_scheme="orange",
        ),
        rx.hstack(
            rx.text("Page", color="#6B7280", font_size="0.85rem"),
            rx.text(TaskState.current_page.to_string(), font_weight="700", color="#1A1A1A", font_size="0.95rem"),
            rx.text("of", color="#6B7280", font_size="0.85rem"),
            rx.text(TaskState.total_pages.to_string(), font_weight="700", color="#1A1A1A", font_size="0.95rem"),
            spacing="2", align="center",
        ),
        rx.button(
            rx.hstack(rx.text("Next"), rx.icon("chevron-right", size=14), spacing="1", align="center"),
            on_click=TaskState.go_next_page,
            is_disabled=~TaskState.has_next_page,
            variant="outline",
            size="2",
            color_scheme="orange",
        ),
        spacing="4", justify="center", width="100%", padding_y="1rem",
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


# ── App header (aligned with CEO dashboard) ────────────────────────────────

def _employee_app_header() -> rx.Component:
    """Logo, avatar, logout + greeting row — matches CEO dashboard header styling."""
    return rx.box(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.el.img(
                        src="/taskme-logo-header.png",
                        alt="TaskMe",
                        style={
                            "height": "64px",
                            "width": "auto",
                            "max_width": "min(100%, 280px)",
                            "display": "block",
                            "object_fit": "contain",
                        },
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.hstack(
                            rx.box(
                                rx.text(
                                    rx.cond(TaskState.name != "", TaskState.name[:1].to_string(), "?"),
                                    color="white", font_weight="700", font_size="0.9rem", text_transform="uppercase",
                                ),
                                width="40px", height="40px", border_radius="50%",
                                background_color="#1A2B56",
                                display="flex", align_items="center", justify_content="center",
                                flex_shrink="0", border="2px solid rgba(229, 163, 43, 0.45)",
                            ),
                            rx.text(TaskState.name, font_weight="600", font_size="0.95rem", color="#1A1A1A",
                                    max_width="160px", overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
                            spacing="3", align="center",
                        ),
                        rx.button("Logout", on_click=TaskState.logout, color_scheme="orange", variant="outline", size="2"),
                        spacing="2", align="center",
                    ),
                    width="100%", align="center", padding_y="0.85rem",
                ),
                rx.divider(border_color="rgba(15, 23, 42, 0.08)"),
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            rx.Var.create("Good Morning, ") + TaskState.name,
                            font_size="1.5rem", font_weight="700", color="#1A1A1A",
                            letter_spacing="-0.02em", line_height="1.25",
                        ),
                        rx.cond(
                            TaskState.pending_tasks == 1,
                            rx.text("You have 1 task pending today", color="#6B7280", font_size="0.95rem",
                                    margin_top="0.35rem", line_height="1.4"),
                            rx.text(
                                rx.Var.create("You have ") + TaskState.pending_tasks.to_string() + " tasks pending today",
                                color="#6B7280", font_size="0.95rem", margin_top="0.35rem", line_height="1.4",
                            ),
                        ),
                        rx.text("My Tasks", font_size="1.15rem", font_weight="800", color="#374151",
                                margin_top="0.5rem", letter_spacing="-0.01em"),
                        spacing="0", align_items="start",
                    ),
                    rx.spacer(),
                    rx.button("Refresh", variant="outline", on_click=TaskState.load_employee_tasks,
                              align_self="start", margin_top="0.15rem"),
                    width="100%", align="start", padding_y="1rem",
                ),
                spacing="0", width="100%",
            ),
            max_width="900px", margin_x="auto", width="100%", padding_x="1.5rem",
        ),
        background_color="#FFFFFF",
        border_bottom="1px solid rgba(15, 23, 42, 0.06)",
        box_shadow="0 4px 24px -6px rgba(15, 23, 42, 0.1)",
        position="sticky", top="0", z_index="30", width="100%",
    )


# ── Page ────────────────────────────────────────────────────────────────────

@rx.page(route="/tasks", title="Zapp · My Tasks",
         on_load=[TaskState.load_employee_tasks, TaskState.request_notification_permission])
def employee_tasks() -> rx.Component:
    return rx.cond(
        ~TaskState.is_hydrated,
        rx.center(rx.spinner(), min_height="100vh", background_color="#ECEEF3"),
        rx.cond(
            ~TaskState.is_employee,
            rx.center(rx.spinner(), min_height="100vh", background_color="#ECEEF3"),
            rx.box(
                _employee_page_styles(),
                _employee_app_header(),
                rx.box(
                    rx.cond(TaskState.toast != "", rx.callout(TaskState.toast, color_scheme="blue"), rx.box()),
                    rx.cond(
                        TaskState.is_loading,
                        rx.center(rx.spinner()),
                        rx.vstack(
                            _employee_mini_stats(),
                            rx.foreach(
                                TaskState.tasks,
                                lambda t: rx.box(
                                    task_card(t),
                                    _progress_controls(t),
                                    _submission_section(t),
                                    padding="0.85rem",
                                    border_radius="18px",
                                    border="1px solid rgba(15, 23, 42, 0.08)",
                                    background_color="rgba(255, 255, 255, 0.92)",
                                    width="100%",
                                    box_shadow="0 6px 24px rgba(15, 23, 42, 0.06)",
                                ),
                            ),
                            # Pagination
                            _employee_pagination(),
                            spacing="4", width="100%",
                        ),
                    ),
                    _comments_dialog(),
                    _preview_dialog(),
                    _submissions_dialog(),
                    # Lightweight poll instead of full reload
                    rx.moment(interval=30_000, on_change=TaskState.poll_summary, display="none"),
                    rx.moment(interval=10_000, on_change=TaskState.poll_notifications, display="none"),
                    padding="1.5rem", max_width="900px", margin_x="auto",
                ),
                background_color="#ECEEF3", min_height="100vh",
            ),
        ),
    )
