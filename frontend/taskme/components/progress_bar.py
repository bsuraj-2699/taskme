from __future__ import annotations

import reflex as rx


def progress_bar(value: int) -> rx.Component:
    return rx.progress(
        value=value,
        max=100,
        color_scheme="orange",
        height="0.6rem",
        border_radius="999px",
        width="100%",
    )


def employee_progress_bar(value) -> rx.Component:
    """Gradient fill, animated width, percentage label (employee tasks)."""
    return rx.vstack(
        rx.hstack(
            rx.text("Progress", font_size="0.72rem", color="#64748B", font_weight="600"),
            rx.spacer(),
            rx.text(
                value.to_string() + "%",
                font_size="0.82rem",
                font_weight="800",
                color="#334155",
            ),
            width="100%",
            align="center",
        ),
        rx.box(
            rx.box(
                class_name="taskme-employee-progress-fill",
                style={
                    "width": value.to_string() + "%",
                    "min_width": "0%",
                    "max_width": "100%",
                    "height": "100%",
                    "border_radius": "999px",
                    "background": "linear-gradient(90deg, #EA580C 0%, #FACC15 50%, #22C55E 100%)",
                    "background_size": "220% 100%",
                    "transition": "width 0.75s cubic-bezier(0.22, 1, 0.36, 1)",
                    "animation": "taskme-progress-gradient 3s ease-in-out infinite",
                },
            ),
            style={
                "width": "100%",
                "height": "0.65rem",
                "border_radius": "999px",
                "background_color": "rgba(15, 23, 42, 0.09)",
                "overflow": "hidden",
            },
        ),
        spacing="1",
        width="100%",
    )
