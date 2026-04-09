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
                    rx.text(
                        "Attachments",
                        color="#6B7280",
                        font_size="0.8rem",
                        font_weight="600",
                    ),
                    rx.foreach(
                        task["attachments"],
                        lambda a: rx.button(
                            rx.hstack(
                                rx.icon("paperclip", size=13),
                                rx.text(a["file_name"], font_size="0.82rem"),
                                spacing="1",
                                align="center",
                            ),
                            variant="ghost",
                            color="#F97316",
                            size="1",
                            on_click=TaskState.download_attachment(
                                task["id"], a["id"], a["file_name"]
                            ),
                            cursor="pointer",
                            _hover={"color": "#EA6C0A", "text_decoration": "underline"},
                        ),
                    ),
                    spacing="1",
                    align="start",
                    width="100%",
                ),
                rx.box(),
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