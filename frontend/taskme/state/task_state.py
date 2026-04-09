from __future__ import annotations

import os
from typing import Any, TypedDict

import reflex as rx
import httpx

from taskme.state.auth_state import AuthState


def _api_base() -> str:
    return os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


class AttachmentDict(TypedDict):
    id: str
    file_name: str
    uploaded_at: str


class TaskDict(TypedDict):
    id: str
    title: str
    description: str
    assigned_to: str        # raw UUID — needed for edit/reassign prefill
    assigned_to_name: str
    status: str
    progress: int
    deadline: str
    attachment_name: str
    attachments: list[AttachmentDict]


class UserDict(TypedDict):
    id: str
    name: str
    username: str
    role: str


class TaskState(AuthState):
    tasks: list[TaskDict] = []
    users: list[UserDict] = []
    is_loading: bool = False
    error: str = ""

    status_filter: str = "all"
    sort_deadline_asc: bool = True

    # Add-task dialog
    show_add_dialog: bool = False
    new_title: str = ""
    new_description: str = ""
    new_assigned_to: str = ""
    new_deadline: str = ""

    toast: str = ""

    # Legacy single-attach dialog (kept for post-creation adds)
    show_attach_dialog: bool = False
    attach_task_id: str = ""

    # Staged files for add-task dialog
    pending_file_names: list[str] = []
    # Internal storage: list of {"name": str, "data": bytes-as-list} — not exposed to UI
    _pending_files_raw: list[dict] = []

    # Reassign dialog
    show_reassign_dialog: bool = False
    reassign_task_id: str = ""
    reassign_assigned_to: str = ""

    # Edit task dialog
    show_edit_dialog: bool = False
    edit_task_id: str = ""
    edit_title: str = ""
    edit_description: str = ""
    edit_assigned_to: str = ""
    edit_deadline: str = ""
    edit_attachments: list[AttachmentDict] = []

    # EOD Reports
    eod_reports: list[dict] = []
    report_schedule_time: str = "18:00"
    report_schedule_timezone: str = "Asia/Kolkata"
    report_schedule_active: bool = True
    show_report_dialog: bool = False
    selected_report_content: str = ""
    selected_report_id: str = ""
    selected_report_data: dict = {}

    @rx.var
    def filtered_sorted_tasks(self) -> list[TaskDict]:
        rows = self.tasks
        if self.status_filter != "all":
            rows = [t for t in rows if t.get("status") == self.status_filter]

        def _deadline(t: TaskDict) -> str:
            return t.get("deadline") or ""

        rows = sorted(rows, key=_deadline, reverse=not self.sort_deadline_asc)
        return rows

    @rx.var
    def total_tasks(self) -> int:
        return len(self.tasks)

    @rx.var
    def pending_tasks(self) -> int:
        return len([t for t in self.tasks if t.get("status") == "pending"])

    @rx.var
    def in_progress_tasks(self) -> int:
        return len([t for t in self.tasks if t.get("status") == "in_progress"])

    @rx.var
    def done_tasks(self) -> int:
        return len([t for t in self.tasks if t.get("status") == "done"])

    @rx.var
    def employee_users(self) -> list[UserDict]:
        return [u for u in self.users if u.get("role") == "employee"]

    @rx.var
    def pending_file_count(self) -> int:
        return len(self.pending_file_names)

    def toggle_sort_deadline(self) -> None:
        self.sort_deadline_asc = not self.sort_deadline_asc

    def open_add_dialog(self) -> None:
        self.show_add_dialog = True
        self.pending_file_names = []
        self._pending_files_raw = []

    def close_add_dialog(self) -> None:
        self.show_add_dialog = False
        self.pending_file_names = []
        self._pending_files_raw = []

    def set_add_dialog_open(self, open_: bool) -> None:
        self.show_add_dialog = bool(open_)
        if not open_:
            self.pending_file_names = []
            self._pending_files_raw = []

    def open_attach_dialog(self, task_id: str) -> None:
        self.attach_task_id = task_id
        self.show_attach_dialog = True

    def close_attach_dialog(self) -> None:
        self.show_attach_dialog = False

    def set_attach_dialog_open(self, open_: bool) -> None:
        self.show_attach_dialog = bool(open_)

    def set_status_filter(self, v: str) -> None:
        self.status_filter = v

    def set_new_title(self, v: str) -> None:
        self.new_title = v

    def set_new_description(self, v: str) -> None:
        self.new_description = v

    def set_new_assigned_to(self, v: str) -> None:
        self.new_assigned_to = v

    def set_new_task_assignee(self, v: str) -> None:
        self.set_new_assigned_to(v)

    def set_new_deadline(self, v: str) -> None:
        self.new_deadline = v

    @rx.event
    async def set_pending_file_names(self, files: list[rx.UploadFile]) -> None:
        """Read and cache file contents on drop so they're available when Create is clicked."""
        raw = []
        names = []
        for f in files:
            data = await f.read()
            raw.append({"name": f.name, "data": list(data)})
            names.append(f.name)
        self._pending_files_raw = raw
        self.pending_file_names = names

    async def load_ceo_dashboard(self):
        if self.role != "ceo":
            return rx.redirect("/login")

        self.error = ""
        self.is_loading = True
        try:
            r1 = await self.api("GET", "/api/tasks/")
            r2 = await self.api("GET", "/api/users/")
            users: list[UserDict] = []
            if r2.status_code == 200:
                raw_users: list[dict[str, Any]] = r2.json()
                users = [
                    UserDict(
                        id=str(u.get("id") or ""),
                        name=str(u.get("name") or ""),
                        username=str(u.get("username") or ""),
                        role=str(u.get("role") or ""),
                    )
                    for u in raw_users
                ]
                self.users = users
            else:
                self.error = "Failed to load users."

            user_name_by_id = {u.get("id"): u.get("name") for u in users}

            if r1.status_code == 200:
                raw_tasks: list[dict[str, Any]] = r1.json()
                self.tasks = [
                    TaskDict(
                        id=str(t.get("id") or ""),
                        title=str(t.get("title") or ""),
                        description=str(t.get("description") or ""),
                        assigned_to=str(t.get("assigned_to") or ""),
                        assigned_to_name=user_name_by_id.get(str(t.get("assigned_to") or ""), ""),
                        status=str(t.get("status") or "pending"),
                        progress=int(t.get("progress") or 0),
                        deadline=str(t.get("deadline") or ""),
                        attachment_name=str(t.get("attachment_name") or ""),
                        attachments=[
                            AttachmentDict(
                                id=str(a.get("id") or ""),
                                file_name=str(a.get("file_name") or ""),
                                uploaded_at=str(a.get("uploaded_at") or ""),
                            )
                            for a in (t.get("attachments") or [])
                        ],
                    )
                    for t in raw_tasks
                ]
            else:
                self.error = "Failed to load tasks."
        finally:
            self.is_loading = False

    async def load_employee_tasks(self):
        if self.role != "employee":
            return rx.redirect("/dashboard")

        self.error = ""
        self.is_loading = True
        try:
            r = await self.api("GET", "/api/tasks/my")
            if r.status_code == 200:
                raw_tasks: list[dict[str, Any]] = r.json()
                self.tasks = [
                    TaskDict(
                        id=str(t.get("id") or ""),
                        title=str(t.get("title") or ""),
                        description=str(t.get("description") or ""),
                        assigned_to=str(t.get("assigned_to") or ""),
                        assigned_to_name="",
                        status=str(t.get("status") or "pending"),
                        progress=int(t.get("progress") or 0),
                        deadline=str(t.get("deadline") or ""),
                        attachment_name=str(t.get("attachment_name") or ""),
                        attachments=[
                            AttachmentDict(
                                id=str(a.get("id") or ""),
                                file_name=str(a.get("file_name") or ""),
                                uploaded_at=str(a.get("uploaded_at") or ""),
                            )
                            for a in (t.get("attachments") or [])
                        ],
                    )
                    for t in raw_tasks
                ]
            else:
                self.error = "Failed to load tasks."
        finally:
            self.is_loading = False

    @rx.event
    async def create_task_with_files(self, files: list[rx.UploadFile]) -> None:
        """Create the task then upload any files that were staged on drop."""
        self.toast = ""
        try:
            # Normalize deadline: browser on Windows may send MM/DD/YYYY, API needs YYYY-MM-DD
            deadline = self.new_deadline
            if deadline and "/" in deadline:
                parts = deadline.split("/")
                if len(parts) == 3:
                    deadline = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"

            payload = {
                "title": self.new_title,
                "description": self.new_description,
                "assigned_to": self.new_assigned_to,
                "deadline": deadline,
            }
            r = await self.api("POST", "/api/tasks/", json=payload)
            if r.status_code != 200:
                try:
                    detail = r.json()
                except Exception:
                    detail = r.text
                self.toast = f"Failed to create task ({r.status_code}): {detail}"
                return

            task_id = r.json().get("id")

            # Use cached file data from on_drop (more reliable than re-reading UploadFile on click)
            raw_files = list(self._pending_files_raw)

            # Fall back to reading from the upload_files argument if cache is empty
            if not raw_files and files:
                for f in files:
                    data = await f.read()
                    raw_files.append({"name": f.name, "data": list(data)})

            if raw_files and task_id:
                headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
                file_tuples = [
                    ("files", (entry["name"], bytes(entry["data"])))
                    for entry in raw_files
                ]
                async with httpx.AsyncClient(timeout=120.0) as client:
                    upload_r = await client.post(
                        f"{_api_base()}/api/tasks/{task_id}/attach",
                        files=file_tuples,
                        headers=headers,
                    )
                if upload_r.status_code != 200:
                    self.toast = f"Task created but file upload failed ({upload_r.status_code})."

            self.show_add_dialog = False
            self.pending_file_names = []
            self._pending_files_raw = []
            self.new_title = ""
            self.new_description = ""
            self.new_assigned_to = ""
            self.new_deadline = ""
            await self.load_ceo_dashboard()
        except Exception as e:
            self.toast = f"Failed to create task: {e}"

    async def create_task(self) -> None:
        """Fallback: create task without files (called when no upload zone used)."""
        self.toast = ""
        try:
            deadline = self.new_deadline
            if deadline and "/" in deadline:
                parts = deadline.split("/")
                if len(parts) == 3:
                    deadline = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"

            payload = {
                "title": self.new_title,
                "description": self.new_description,
                "assigned_to": self.new_assigned_to,
                "deadline": deadline,
            }
            r = await self.api("POST", "/api/tasks/", json=payload)
            if r.status_code != 200:
                self.toast = "Failed to create task."
                return
            self.show_add_dialog = False
            self.new_title = ""
            self.new_description = ""
            self.new_assigned_to = ""
            self.new_deadline = ""
            await self.load_ceo_dashboard()
        except Exception:
            self.toast = "Failed to create task."

    @rx.event
    async def upload_attachment(self, files: list[rx.UploadFile]):
        """Post-creation single/multi attach from the Attach dialog."""
        if self.role != "ceo":
            return rx.noop()
        if not files:
            return rx.noop()
        if not self.attach_task_id:
            return rx.noop()

        try:
            headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
            file_tuples = []
            for f in files:
                content = await f.read()
                file_tuples.append(("files", (f.name, content)))

            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(
                    f"{_api_base()}/api/tasks/{self.attach_task_id}/attach",
                    files=file_tuples,
                    headers=headers,
                )
            if r.status_code != 200:
                self.toast = "Failed to upload attachment."
                return rx.noop()
            self.show_attach_dialog = False
            await self.load_ceo_dashboard()
        except Exception:
            self.toast = "Failed to upload attachment."

    async def mark_done(self, task_id: str) -> None:
        r = await self.api("PATCH", f"/api/tasks/{task_id}/done")
        if r.status_code == 200:
            await self.load_ceo_dashboard()
        else:
            self.toast = "Failed to mark done."

    async def update_progress(self, task_id: str, progress: int) -> None:
        r = await self.api("PATCH", f"/api/tasks/{task_id}/progress", json={"progress": int(progress)})
        if r.status_code == 200:
            await self.load_employee_tasks()
        else:
            self.toast = "Failed to update progress."

    async def download_attachment(self, task_id: str, attachment_id: str, file_name: str) -> None:
        """Fetch attachment with auth header and trigger browser download.

        IMPORTANT: _api_base() returns the Docker-internal URL (http://backend:8000)
        which the browser cannot reach. We use a separate PUBLIC_API_URL env var
        (defaults to http://localhost:8000) for browser-side JS fetches.
        """
        public_base = os.getenv("PUBLIC_API_URL", "http://localhost:8000").rstrip("/")
        url = f"{public_base}/api/tasks/{task_id}/attachments/{attachment_id}/download"
        token = self.access_token

        # Safely escape values for JS string interpolation
        safe_url = url.replace("\\", "\\\\").replace("`", "\\`")
        safe_token = token.replace("\\", "\\\\").replace("`", "\\`") if token else ""
        safe_name = file_name.replace("\\", "\\\\").replace("`", "\\`")

        script = f"""
        (async () => {{
            const url = `{safe_url}`;
            const token = `{safe_token}`;
            const fileName = `{safe_name}`;
            try {{
                const headers = {{}};
                if (token) headers['Authorization'] = 'Bearer ' + token;
                const r = await fetch(url, {{ headers }});
                if (!r.ok) {{
                    console.error('Download failed:', r.status, url);
                    return;
                }}
                const blob = await r.blob();
                const a = document.createElement('a');
                a.href = URL.createObjectURL(blob);
                a.download = fileName;
                document.body.appendChild(a);
                a.click();
                setTimeout(() => {{ URL.revokeObjectURL(a.href); a.remove(); }}, 2000);
            }} catch(e) {{
                console.error('Download error:', e, url);
            }}
        }})();
        """
        yield rx.call_script(script)

    async def poll_notifications(self) -> None:
        r = await self.api("GET", "/api/notifications/poll")
        if r.status_code != 200:
            return
        data = r.json()
        if not data:
            return

        notif_id = data.get("id")
        message = data.get("message") or "You have a new task."

        if getattr(self, "notification_permission", "") == "granted":
            yield rx.call_script(
                f"""
                try {{
                  new Notification("Taskme", {{ body: {message!r} }});
                }} catch(e) {{}}
                """
            )
        else:
            self.toast = message

        if notif_id:
            await self.api("PATCH", f"/api/notifications/{notif_id}/read")

    # NOTE: Methods appended below — reassign, EOD reports, report dialog

    def open_reassign_dialog(self, task_id: str) -> None:
        self.reassign_task_id = task_id
        self.reassign_assigned_to = ""
        self.show_reassign_dialog = True

    def close_reassign_dialog(self) -> None:
        self.show_reassign_dialog = False

    def set_reassign_dialog_open(self, open_: bool) -> None:
        self.show_reassign_dialog = bool(open_)

    def set_reassign_assigned_to(self, v: str) -> None:
        self.reassign_assigned_to = v

    async def reassign_task(self) -> None:
        if not self.reassign_task_id or not self.reassign_assigned_to:
            self.toast = "Please select an employee."
            return
        r = await self.api(
            "PATCH",
            f"/api/tasks/{self.reassign_task_id}/reassign",
            json={"assigned_to": self.reassign_assigned_to},
        )
        if r.status_code == 200:
            self.show_reassign_dialog = False
            self.reassign_task_id = ""
            self.reassign_assigned_to = ""
            await self.load_ceo_dashboard()
        else:
            self.toast = "Failed to reassign task."

    async def load_eod_reports(self) -> None:
        if self.role != "ceo":
            return
        try:
            r = await self.api("GET", "/api/reports/")
            if r.status_code == 200:
                self.eod_reports = r.json()
        except Exception:
            pass

    async def load_report_schedule(self) -> None:
        if self.role != "ceo":
            return
        try:
            r = await self.api("GET", "/api/reports/schedule")
            if r.status_code == 200:
                data = r.json()
                self.report_schedule_time = data.get("report_time", "18:00")
                self.report_schedule_timezone = data.get("timezone", "Asia/Kolkata")
                self.report_schedule_active = data.get("is_active", True)
        except Exception:
            pass

    def set_report_time(self, v: str) -> None:
        self.report_schedule_time = v

    def set_report_timezone(self, v: str) -> None:
        self.report_schedule_timezone = v

    def set_report_active(self, v: str) -> None:
        self.report_schedule_active = v == "active"

    async def save_report_schedule(self) -> None:
        r = await self.api(
            "POST",
            "/api/reports/schedule",
            json={
                "report_time": self.report_schedule_time,
                "timezone": self.report_schedule_timezone,
                "is_active": self.report_schedule_active,
            },
        )
        if r.status_code == 200:
            self.toast = "Schedule saved."
        else:
            self.toast = "Failed to save schedule."

    async def generate_report_now(self) -> None:
        r = await self.api("POST", "/api/reports/generate")
        if r.status_code == 200:
            self.toast = "Report generated."
            await self.load_eod_reports()
        else:
            self.toast = "Failed to generate report."

    async def view_report(self, report_id: str) -> None:
        self.selected_report_id = report_id
        r = await self.api("GET", f"/api/reports/{report_id}")
        if r.status_code == 200:
            data = r.json()
            self.selected_report_data = data
            self.selected_report_content = data.get("content", "")
            self.show_report_dialog = True
        else:
            self.toast = "Failed to load report."

    def close_report_dialog(self) -> None:
        self.show_report_dialog = False
        self.selected_report_content = ""
        self.selected_report_data = {}

    def set_report_dialog_open(self, open_: bool) -> None:
        self.show_report_dialog = bool(open_)
        if not open_:
            self.selected_report_content = ""
            self.selected_report_data = {}

    # ── Edit Task ────────────────────────────────────────────────────────────

    def open_edit_dialog(self, task_id: str) -> None:
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task:
            return
        self.edit_task_id = task_id
        self.edit_title = task["title"]
        self.edit_description = task["description"]
        self.edit_assigned_to = str(task.get("assigned_to") or "")
        self.edit_deadline = task["deadline"]
        self.edit_attachments = list(task.get("attachments") or [])
        self.show_edit_dialog = True

    def close_edit_dialog(self) -> None:
        self.show_edit_dialog = False
        self.edit_task_id = ""

    def set_edit_dialog_open(self, open_: bool) -> None:
        self.show_edit_dialog = bool(open_)
        if not open_:
            self.edit_task_id = ""

    def set_edit_title(self, v: str) -> None:
        self.edit_title = v

    def set_edit_description(self, v: str) -> None:
        self.edit_description = v

    def set_edit_assigned_to(self, v: str) -> None:
        self.edit_assigned_to = v

    def set_edit_deadline(self, v: str) -> None:
        self.edit_deadline = v

    async def save_edit_task(self) -> None:
        if not self.edit_task_id:
            return
        deadline = self.edit_deadline
        if deadline and "/" in deadline:
            parts = deadline.split("/")
            if len(parts) == 3:
                deadline = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
        payload = {
            "title": self.edit_title,
            "description": self.edit_description,
            "assigned_to": self.edit_assigned_to,
            "deadline": deadline,
        }
        r = await self.api("PUT", f"/api/tasks/{self.edit_task_id}", json=payload)
        if r.status_code == 200:
            self.show_edit_dialog = False
            await self.load_ceo_dashboard()
        else:
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            self.toast = f"Failed to save task ({r.status_code}): {detail}"

    async def delete_attachment_from_edit(self, attachment_id: str) -> None:
        if not self.edit_task_id:
            return
        r = await self.api(
            "DELETE",
            f"/api/tasks/{self.edit_task_id}/attachments/{attachment_id}",
        )
        if r.status_code == 200:
            self.edit_attachments = [
                a for a in self.edit_attachments if a["id"] != attachment_id
            ]
            await self.load_ceo_dashboard()
        else:
            self.toast = "Failed to delete attachment."

    @rx.event
    async def upload_edit_attachments(self, files: list[rx.UploadFile]) -> None:
        """Upload new files to an existing task from the edit dialog."""
        if not files or not self.edit_task_id:
            return
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
            file_tuples = []
            for f in files:
                content = await f.read()
                file_tuples.append(("files", (f.name, content)))
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(
                    f"{_api_base()}/api/tasks/{self.edit_task_id}/attach",
                    files=file_tuples,
                    headers=headers,
                )
            if r.status_code == 200:
                # Refresh edit_attachments from the updated task
                updated = r.json()
                self.edit_attachments = [
                    AttachmentDict(
                        id=str(a.get("id") or ""),
                        file_name=str(a.get("file_name") or ""),
                        uploaded_at=str(a.get("uploaded_at") or ""),
                    )
                    for a in (updated.get("attachments") or [])
                ]
                await self.load_ceo_dashboard()
            else:
                self.toast = "Failed to upload file(s)."
        except Exception as e:
            self.toast = f"Upload error: {e}"