from __future__ import annotations

import reflex as rx

from taskme.components.progress_bar import employee_progress_bar
from taskme.components.status_badge import status_badge
from taskme.state.task_state import TaskState


def _employee_priority_badge(priority) -> rx.Component:
    return rx.badge(
        rx.cond(
            priority == "high",
            "High",
            rx.cond(priority == "low", "Low", "Medium"),
        ),
        color_scheme=rx.cond(
            priority == "high",
            "red",
            rx.cond(priority == "low", "green", "yellow"),
        ),
        variant="solid",
        padding_x="0.55rem",
        padding_y="0.2rem",
        font_size="0.7rem",
        font_weight="700",
        border_radius="999px",
    )


def task_card(task: rx.Var) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    _employee_priority_badge(task["priority"]),
                    rx.badge(
                        task["task_type"],
                        variant="outline",
                        color_scheme="gray",
                        size="1",
                        border_radius="8px",
                        font_weight="600",
                        font_size="0.68rem",
                    ),
                    spacing="2",
                    align="center",
                    flex_wrap="wrap",
                ),
                rx.spacer(),
                status_badge(task["status"]),
                width="100%",
                align="center",
            ),
            rx.text(
                task["title"],
                font_weight="800",
                color="#0F172A",
                font_size="1.08rem",
                line_height="1.35",
            ),
            rx.text(
                task["description"],
                color="#475569",
                font_size="0.92rem",
                line_height="1.5",
                white_space="pre-wrap",
            ),
            rx.hstack(
                rx.icon("calendar-clock", size=16, color="#94A3B8"),
                rx.text(
                    task["deadline_label"],
                    font_size="0.88rem",
                    font_weight="700",
                    color=task["deadline_label_color"],
                ),
                rx.spacer(),
                rx.text(
                    rx.Var.create("Due date: ") + task["deadline"].to_string(),
                    font_size="0.78rem",
                    color="#94A3B8",
                ),
                width="100%",
                align="center",
                padding_y="0.35rem",
                padding_x="0.5rem",
                border_radius="10px",
                background_color="rgba(15, 23, 42, 0.04)",
                border="1px solid rgba(15, 23, 42, 0.06)",
            ),
            employee_progress_bar(task["progress"]),
            rx.cond(
                task["attachments"].length() > 0,
                rx.vstack(
                    rx.hstack(
                        rx.icon("paperclip", size=14, color="#F97316"),
                        rx.text(
                            "Attachments (" + task["attachments"].length().to_string() + ")",
                            color="#64748B",
                            font_size="0.85rem",
                            font_weight="700",
                        ),
                        spacing="1",
                        align="center",
                    ),
                    rx.foreach(
                        task["attachments"],
                        lambda a: rx.hstack(
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
                            rx.icon_button(
                                rx.icon("download", size=13),
                                size="1",
                                variant="ghost",
                                color_scheme="orange",
                                on_click=TaskState.download_attachment(
                                    task["id"], a["id"], a["file_name"]
                                ),
                                cursor="pointer",
                                title="Download",
                            ),
                            width="100%",
                            align="center",
                            padding_x="0.45rem",
                            padding_y="0.25rem",
                            border="1px solid rgba(251,146,60,0.22)",
                            border_radius="10px",
                        ),
                    ),
                    spacing="2",
                    align="start",
                    width="100%",
                    padding="0.65rem",
                    border="1px dashed rgba(251,146,60,0.35)",
                    border_radius="12px",
                    background_color="rgba(249,115,22,0.04)",
                ),
                rx.box(),
            ),
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
                    size="2",
                    on_click=TaskState.open_comments_dialog(task["id"]),
                ),
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        padding="1.15rem",
        border="1px solid rgba(15, 23, 42, 0.08)",
        border_radius="16px",
        background_color="#FFFFFF",
        width="100%",
        box_shadow="0 4px 20px rgba(15, 23, 42, 0.06), 0 1px 3px rgba(15, 23, 42, 0.04)",
    )
