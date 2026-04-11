from __future__ import annotations

import reflex as rx

from taskme.state.auth_state import AuthState


def _branding_column() -> rx.Component:
    """Left panel: logo, subtle pattern and blurred dashboard motif."""
    return rx.box(
        # Dot grid pattern
        rx.box(
            position="absolute",
            inset="0",
            z_index="0",
            opacity="0.12",
            style={
                "background_image": "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.9) 1px, transparent 0)",
                "background_size": "26px 26px",
            },
        ),
        # Blurred “dashboard” preview
        rx.box(
            rx.vstack(
                rx.box(
                    width="100%",
                    height="14px",
                    background_color="rgba(255,255,255,0.2)",
                    border_radius="7px",
                ),
                rx.hstack(
                    rx.box(
                        flex="1",
                        height="96px",
                        background_color="rgba(255,255,255,0.1)",
                        border_radius="14px",
                        border="1px solid rgba(255,255,255,0.12)",
                    ),
                    rx.box(
                        flex="1",
                        height="96px",
                        background_color="rgba(255,255,255,0.08)",
                        border_radius="14px",
                        border="1px solid rgba(255,255,255,0.08)",
                    ),
                    spacing="3",
                    width="100%",
                ),
                rx.box(
                    width="100%",
                    height="72px",
                    background_color="rgba(251,146,60,0.25)",
                    border_radius="12px",
                ),
                rx.hstack(
                    rx.box(
                        flex="1",
                        height="12px",
                        background_color="rgba(255,255,255,0.15)",
                        border_radius="6px",
                    ),
                    rx.box(
                        width="28%",
                        height="12px",
                        background_color="rgba(255,255,255,0.1)",
                        border_radius="6px",
                    ),
                    spacing="3",
                    width="100%",
                ),
                spacing="4",
                width="100%",
                max_width="320px",
            ),
            position="absolute",
            bottom="10%",
            left="50%",
            style={"transform": "translateX(-50%)"},
            width="82%",
            max_width="380px",
            filter="blur(10px)",
            opacity="0.42",
            z_index="0",
            pointer_events="none",
        ),
        rx.vstack(
            rx.el.img(
                src="/zapp-login-logo.png",
                alt="ZAPP",
                style={
                    "max_width": "min(100%, 22rem)",
                    "width": "auto",
                    "height": "auto",
                    "display": "block",
                },
            ),
            spacing="6",
            align="center",
            justify="center",
            width="100%",
            min_height=["38vh", "40vh", "100vh"],
            padding_y="2.5rem",
            padding_x="2rem",
            position="relative",
            z_index="1",
        ),
        position="relative",
        overflow="hidden",
        width=["100%", "100%", "46%"],
        flex_shrink="0",
        background="linear-gradient(145deg, #0f172a 0%, #1e3a8f 46%, #b45309 100%)",
    )


def _login_card() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                "Welcome back",
                font_size="1.75rem",
                font_weight="800",
                color="#1A1A1A",
                letter_spacing="-0.03em",
                line_height="1.2",
            ),
            rx.text(
                "Sign in to continue.",
                color="#64748B",
                font_size="1rem",
                line_height="1.5",
            ),
            rx.input(
                placeholder="Username",
                value=AuthState.login_username,
                on_change=AuthState.set_username,
                background_color="#FAFAFA",
                border="1px solid rgba(148,163,184,0.35)",
                border_radius="12px",
                size="3",
                width="100%",
            ),
            rx.input(
                placeholder="Password",
                type="password",
                value=AuthState.login_password,
                on_change=AuthState.set_password,
                background_color="#FAFAFA",
                border="1px solid rgba(148,163,184,0.35)",
                border_radius="12px",
                size="3",
                width="100%",
            ),
            rx.cond(
                AuthState.login_error != "",
                rx.text(AuthState.login_error, color="red", font_size="0.95rem"),
                rx.box(),
            ),
            rx.button(
                rx.cond(AuthState.is_loading, rx.spinner(size="2"), rx.text("Login")),
                on_click=AuthState.login,
                width="100%",
                color_scheme="orange",
                size="3",
                border_radius="12px",
                font_weight="600",
                class_name="taskme-login-submit",
            ),
            spacing="4",
            width="100%",
        ),
        width="100%",
        max_width="26rem",
        padding="2.35rem",
        border_radius="20px",
        background_color="#FFFFFF",
        border="1px solid rgba(251,146,60,0.22)",
        box_shadow=(
            "0 4px 6px -1px rgba(15, 23, 42, 0.06), "
            "0 22px 44px -12px rgba(249, 115, 22, 0.16), "
            "0 0 0 1px rgba(255,255,255,0.8) inset"
        ),
    )


def _form_column() -> rx.Component:
    """Right panel: beige→orange gradient, subtle pattern, login card."""
    return rx.box(
        rx.box(
            position="absolute",
            inset="0",
            z_index="0",
            opacity="0.35",
            style={
                "background_image": (
                    "linear-gradient(120deg, transparent 0%, rgba(249,115,22,0.06) 45%, transparent 70%), "
                    "radial-gradient(circle at 80% 20%, rgba(249,115,22,0.12) 0%, transparent 45%)"
                ),
            },
        ),
        rx.box(
            position="absolute",
            inset="0",
            z_index="0",
            opacity="0.2",
            style={
                "background_image": "radial-gradient(circle at 1px 1px, rgba(180,83,9,0.2) 1px, transparent 0)",
                "background_size": "20px 20px",
            },
        ),
        rx.box(
            rx.vstack(
                _login_card(),
                spacing="0",
                align="center",
                width="100%",
                max_width="26rem",
            ),
            width="100%",
            flex="1",
            min_height=["auto", "auto", "100vh"],
            display="flex",
            align_items="center",
            justify_content="center",
            padding_x="1.75rem",
            padding_y="2rem",
            position="relative",
            z_index="1",
        ),
        width=["100%", "100%", "54%"],
        flex="1",
        min_width="0",
        position="relative",
        overflow="hidden",
        display="flex",
        flex_direction="column",
        background="linear-gradient(168deg, #FAF7F2 0%, #FFF8F3 38%, #FFE8D5 72%, #FED7AA 100%)",
    )


def _login_shell() -> rx.Component:
    return rx.flex(
        _branding_column(),
        _form_column(),
        direction={"initial": "column", "md": "row"},
        spacing="0",
        width="100%",
        min_height="100vh",
        align="stretch",
    )


@rx.page(route="/login", title="Zapp · Login", on_load=AuthState.redirect_if_authed)
def login_page() -> rx.Component:
    return rx.cond(
        AuthState.is_hydrated,
        rx.cond(
            AuthState.is_authed,
            rx.center(rx.spinner(), min_height="100vh", background_color="#FFF8F3"),
            _login_shell(),
        ),
        rx.center(rx.spinner(), min_height="100vh", background_color="#FFF8F3"),
    )
