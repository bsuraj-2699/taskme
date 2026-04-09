from __future__ import annotations

import reflex as rx


def status_badge(status: str) -> rx.Component:
    color = rx.cond(
        status == "done",
        "green",
        rx.cond(status == "in_progress", "amber", "orange"),
    )
    label = rx.cond(
        status == "pending",
        "Pending",
        rx.cond(
            status == "in_progress",
            "In Progress",
            rx.cond(
                status == "done",
                "Done",
                status,
            ),
        ),
    )
    return rx.badge(
        label,
        color_scheme=color,
        variant="solid",
        padding_x="0.6rem",
        padding_y="0.25rem",
        border_radius="999px",
    )

