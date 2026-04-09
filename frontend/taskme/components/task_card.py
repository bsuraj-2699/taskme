from __future__ import annotations

import reflex as rx
from taskme.components.progress_bar import progress_bar
from taskme.components.status_badge import status_badge
from taskme.state.task_state import TaskState


def task_card(task: rx.Var) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(task["title"], font_weight="800", color="#1A1A1A", font_size="1.05rem"),
                rx.spacer(),
                status_badge(task["status"]),
                width="100%",
            ),
            rx.text(task["description"], color="#6B7280", font_size="0.95rem"),
            rx.hstack(
                rx.text("Due: " + task["deadline"].to_string(), color="#6B7280", font_size="0.9rem"),
                rx.spacer(),
                rx.text(task["progress"].to_string() + "%", color="#1A1A1A", font_size="0.9rem"),
                width="100%",
            ),
            progress_bar(task["progress"]),

            # ── Attachments section ─────────────────────────────────────
            rx.cond(
                task["attachments"].length() > 0,
                rx.vstack(
                    rx.hstack(
                        rx.icon("paperclip", size=14, color="#F97316"),
                        rx.text(
                            "Attachments (" + task["attachments"].length().to_string() + ")",
                            color="#6B7280", font_size="0.85rem", font_weight="700",
                        ),
                        spacing="1",
                        align="center",
                    ),
                    rx.foreach(
                        task["attachments"],
                        lambda a: rx.hstack(
                            # Preview button
                            rx.button(
                                rx.hstack(
                                    rx.icon("eye", size=13, color="#F97316"),
                                    rx.text(a["file_name"], font_size="0.82rem", color="#1A1A1A"),
                                    spacing="2",
                                    align="center",
                                ),
                                variant="ghost",
                                size="1",
                                on_click=TaskState.open_preview(task["id"], a["id"], a["file_name"]),
                                cursor="pointer",
                            ),
                            rx.spacer(),
                            # Download button
                            rx.icon_button(
                                rx.icon("download", size=13),
                                size="1",
                                variant="ghost",
                                color_scheme="orange",
                                on_click=TaskState.download_attachment(task["id"], a["id"], a["file_name"]),
                                cursor="pointer",
                                title="Download",
                            ),
                            width="100%",
                            align="center",
                            padding_x="0.4rem",
                            padding_y="0.2rem",
                            border="1px solid rgba(251,146,60,0.2)",
                            border_radius="6px",
                        ),
                    ),
                    spacing="2",
                    align="start",
                    width="100%",
                    padding="0.5rem",
                    border="1px dashed rgba(251,146,60,0.35)",
                    border_radius="8px",
                    background_color="rgba(249,115,22,0.04)",
                ),
                rx.box(),
            ),

            # ── Comments button ─────────────────────────────────────────
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("message-square", size=14),
                        rx.text(
                            "Comments (" + task["comment_count"].to_string() + ")",
                            font_size="0.85rem",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    variant="outline",
                    color_scheme="orange",
                    size="1",
                    on_click=TaskState.open_comments_dialog(task["id"]),
                ),
                width="100%",
            ),

            spacing="3",
            width="100%",
        ),
        padding="1rem",
        border="1px solid rgba(251,146,60,0.3)",
        border_radius="14px",
        background_color="#FFFFFF",
        width="100%",
    )
