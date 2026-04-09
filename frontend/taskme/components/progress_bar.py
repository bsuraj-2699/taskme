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

