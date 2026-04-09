from __future__ import annotations

import reflex as rx

from taskme.state.auth_state import AuthState


def _login_form() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.vstack(
                rx.text(
                    "Draw Creative",
                    font_size="2.2rem",
                    font_weight="900",
                    color="#1A1A1A",
                    letter_spacing="-0.02em",
                ),
                rx.text(
                    "Powered By TaskMe",
                    font_size="1rem",
                    color="#F97316",
                    font_weight="500",
                    letter_spacing="0.08em",
                    text_transform="uppercase",
                ),
                spacing="1",
                align="center",
                margin_bottom="1.5rem",
            ),
            rx.box(
                rx.vstack(
                    rx.text("Welcome back", font_size="1.6rem", font_weight="900", color="#1A1A1A"),
                    rx.text("Sign in to continue.", color="#6B7280"),
                    rx.input(
                        placeholder="Username",
                        value=AuthState.login_username,
                        on_change=AuthState.set_username,
                        background_color="#FFFFFF",
                    ),
                    rx.input(
                        placeholder="Password",
                        type="password",
                        value=AuthState.login_password,
                        on_change=AuthState.set_password,
                        background_color="#FFFFFF",
                    ),
                    rx.cond(
                        AuthState.login_error != "",
                        rx.text(AuthState.login_error, color="red.300", font_size="0.95rem"),
                        rx.box(),
                    ),
                    rx.button(
                        rx.cond(AuthState.is_loading, rx.spinner(size="2"), rx.text("Login")),
                        on_click=AuthState.login,
                        width="100%",
                        color_scheme="orange",
                    ),
                    spacing="3",
                    width="100%",
                ),
                width=["92vw", "420px"],
                padding="1.5rem",
                border="1px solid rgba(251,146,60,0.3)",
                border_radius="16px",
                background_color="#FFFFFF",
            ),
            align="center",
            width="100%",
        ),
        min_height="100vh",
        background_color="#FFF8F3",
        padding="1.5rem",
    )


@rx.page(route="/login", title="Taskme · Login", on_load=AuthState.redirect_if_authed)
def login_page() -> rx.Component:
    return rx.cond(
        AuthState.is_hydrated,
        rx.cond(
            AuthState.is_authed,
            rx.center(rx.spinner(), min_height="100vh", background_color="#FFF8F3"),
            _login_form(),
        ),
        rx.center(rx.spinner(), min_height="100vh", background_color="#FFF8F3"),
    )

