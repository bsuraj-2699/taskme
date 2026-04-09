from __future__ import annotations

import reflex as rx

from taskme.state.auth_state import AuthState


def navbar() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.text("Taskme", font_weight="800", font_size="1.1rem", color="white"),
            spacing="2",
            align="center",
        ),
        rx.spacer(),
        rx.hstack(
            rx.text(AuthState.name, color="white"),
            rx.button(
                "Logout",
                on_click=AuthState.logout,
                color_scheme="orange",
                variant="outline",
                color="white",
                border_color="white",
            ),
            spacing="3",
            align="center",
        ),
        padding_x="1.5rem",
        padding_y="1rem",
        border_bottom="none",
        background_color="#F97316",
        position="sticky",
        top="0",
        z_index="10",
    )

