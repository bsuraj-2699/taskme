from __future__ import annotations

import reflex as rx

from taskme.pages.ceo_dashboard import ceo_dashboard  # noqa: F401
from taskme.pages.employee_view import employee_tasks  # noqa: F401
from taskme.pages.login import login_page  # noqa: F401


@rx.page(route="/", title="Zapp")
def index() -> rx.Component:
    return rx.center(
        rx.spinner(),
        min_height="100vh",
        background_color="#FFF8F3",
        on_mount=rx.redirect("/login"),
    )

    
def _style() -> dict:
    return {
        "font_family": "Inter, ui-sans-serif, system-ui",
        ".taskme-login-submit": {
            "transition": "transform 0.2s ease, box-shadow 0.2s ease",
            "box_shadow": "0 4px 14px rgba(249, 115, 22, 0.28)",
        },
        ".taskme-login-submit:hover": {
            "transform": "translateY(-2px)",
            "box_shadow": "0 10px 28px rgba(249, 115, 22, 0.38)",
        },
    }


app = rx.App(
    theme=rx.theme(
        appearance="light",
        accent_color="orange",
    ),
    style=_style(),
)

