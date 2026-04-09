import os

import reflex as rx


config = rx.Config(
    app_name="taskme",
    backend_port=int(os.getenv("REFLEX_BACKEND_PORT", "3001")),
    frontend_port=int(os.getenv("FRONTEND_PORT", "3000")),
    api_url="http://localhost:3001",   # what the browser uses to reach the backend
)

