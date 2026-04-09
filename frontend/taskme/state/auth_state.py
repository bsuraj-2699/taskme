from __future__ import annotations

import os
from typing import Any, Literal

import httpx
import reflex as rx


def _api_base() -> str:
    return os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


class AuthState(rx.State):
    access_token: str = rx.LocalStorage("", name="taskme_access_token")
    refresh_token: str = rx.LocalStorage("", name="taskme_refresh_token")
    role: str = rx.LocalStorage("", name="taskme_role")
    user_id: str = rx.LocalStorage("", name="taskme_user_id")
    name: str = rx.LocalStorage("", name="taskme_name")

    login_username: str = ""
    login_password: str = ""
    login_error: str = ""
    is_loading: bool = False

    notification_permission: str = rx.LocalStorage("", name="taskme_notification_permission")

    @rx.var
    def is_authed(self) -> bool:
        return bool(self.access_token) and bool(self.role)

    @rx.var
    def is_ceo(self) -> bool:
        return bool(self.access_token) and self.role == "ceo"

    @rx.var
    def is_employee(self) -> bool:
        return bool(self.access_token) and self.role == "employee"

    async def redirect_if_authed(self):
        if self.is_authed:
            if self.role == "ceo":
                return rx.redirect("/dashboard")
            return rx.redirect("/tasks")

    def set_username(self, v: str) -> None:
        self.login_username = v

    def set_password(self, v: str) -> None:
        self.login_password = v

    async def login(self):
        self.login_error = ""
        self.is_loading = True
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(
                    f"{_api_base()}/api/auth/login",
                    json={"username": self.login_username, "password": self.login_password},
                )
            if r.status_code != 200:
                self.login_error = "Invalid credentials"
                return rx.noop()

            data: dict[str, Any] = r.json()
            self.access_token = data.get("access_token", "")
            self.refresh_token = data.get("refresh_token", "")
            self.role = data.get("role", "")
            self.user_id = str(data.get("user_id", ""))
            self.name = data.get("name", "")

            if self.role == "ceo":
                return rx.redirect("/dashboard")
            return rx.redirect("/tasks")
        except Exception:
            self.login_error = "Login failed. Please try again."
            return rx.noop()
        finally:
            self.is_loading = False

    async def logout(self):
        self.access_token = ""
        self.refresh_token = ""
        self.role = ""
        self.user_id = ""
        self.name = ""
        return rx.redirect("/login")

    async def refresh_access_token(self) -> bool:
        if not self.refresh_token:
            return False
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.post(f"{_api_base()}/api/auth/refresh", json={"refresh_token": self.refresh_token})
            if r.status_code != 200:
                return False
            self.access_token = r.json().get("access_token", "")
            return bool(self.access_token)
        except Exception:
            return False

    async def api(
        self,
        method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
        path: str,
        json: Any | None = None,
    ) -> httpx.Response:
        headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
        url = f"{_api_base()}{path}"
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.request(method, url, json=json, headers=headers)
            if r.status_code == 401:
                ok = await self.refresh_access_token()
                if not ok:
                    await self.logout()
                    return r
                headers = {"Authorization": f"Bearer {self.access_token}"}
                r = await client.request(method, url, json=json, headers=headers)
            return r

    async def request_notification_permission(self) -> None:
        # Store permission so UI can decide how to notify.
        yield rx.call_script(
            """
            (async () => {
              if (!("Notification" in window)) return "unsupported";
              try {
                const perm = await Notification.requestPermission();
                return perm;
              } catch(e) {
                return "denied";
              }
            })();
            """,
            callback=AuthState.set_notification_permission,
        )

    @rx.event
    def set_notification_permission(self, value: str) -> None:
        self.notification_permission = value or ""