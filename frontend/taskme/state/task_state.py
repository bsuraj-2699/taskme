from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any, TypedDict

import reflex as rx
import httpx

from taskme.state.auth_state import AuthState


def _api_base() -> str:
    return os.getenv("API_BASE_URL", "http://localhost:8000").rstrip("/")


def _task_priority_from_api(raw: Any) -> str:
    p = str(raw or "medium").strip().lower()
    return p if p in ("low", "medium", "high") else "medium"


def _parse_iso_date(s: str) -> date | None:
    raw = (s or "").strip()
    if len(raw) < 10:
        return None
    try:
        return date(int(raw[0:4]), int(raw[5:7]), int(raw[8:10]))
    except (ValueError, TypeError):
        return None


def _deadline_label_and_color(deadline_str: str, status: str) -> tuple[str, str]:
    if status == "done":
        return ("Completed", "#16A34A")
    dl = _parse_iso_date(deadline_str)
    if dl is None:
        return ("No deadline set", "#64748B")
    today = date.today()
    days = (dl - today).days
    if days < 0:
        return ("Overdue", "#DC2626")
    if days == 0:
        return ("Due today", "#CA8A04")
    if days == 1:
        return ("Due tomorrow", "#CA8A04")
    if days <= 3:
        return (f"Due in {days} days", "#CA8A04")
    return (f"Due in {days} days", "#15803D")


class AttachmentDict(TypedDict):
    id: str
    file_name: str
    uploaded_at: str


class SubmissionDict(TypedDict):
    id: str
    file_name: str
    note: str
    uploaded_at: str
    uploaded_by: str
    uploader_name: str


class CommentDict(TypedDict):
    id: str
    task_id: str
    user_id: str
    author_name: str
    body: str
    created_at: str


class TaskDict(TypedDict):
    id: str
    title: str
    description: str
    assigned_to: str
    assigned_to_name: str
    status: str
    progress: int
    deadline: str
    attachment_name: str
    attachments: list[AttachmentDict]
    comment_count: int
    submission_count: int
    priority: str
    created_at: str
    updated_at: str
    task_type: str
    deadline_label: str
    deadline_label_color: str


class EmployeeWorkloadDict(TypedDict):
    user_id: str
    name: str
    total: int
    pending: int
    in_progress: int
    done: int
    overdue: int


class OverdueTaskDict(TypedDict):
    id: str
    title: str
    assigned_to_name: str
    deadline: str
    days_overdue: int
    progress: int


class UserDict(TypedDict):
    id: str
    name: str
    username: str
    role: str


class ReportSubmissionDict(TypedDict):
    id: str
    file_name: str
    uploaded_at: str
    task_id: str


class ReportTaskDict(TypedDict):
    id: str
    title: str
    assigned_to_name: str
    status: str
    progress: int
    deadline: str
    submissions: list[ReportSubmissionDict]


class TaskState(AuthState):
    tasks: list[TaskDict] = []
    users: list[UserDict] = []
    is_loading: bool = False
    error: str = ""

    status_filter: str = "all"
    employee_filter: str = "all"
    priority_filter: str = "all"
    sort_deadline_asc: bool = True

    # ── Pagination state ───────────────────────────────────────────────────
    current_page: int = 1
    page_size: int = 50
    total_tasks_count: int = 0
    total_pages: int = 1

    # Track last_updated from summary to avoid unnecessary full reloads
    _last_known_updated: str = ""

    show_add_dialog: bool = False
    new_title: str = ""
    new_description: str = ""
    new_assigned_to: str = ""
    new_deadline: str = ""
    new_priority: str = "medium"

    toast: str = ""

    show_attach_dialog: bool = False
    attach_task_id: str = ""

    pending_file_names: list[str] = []
    _pending_files_raw: list[dict] = []

    show_reassign_dialog: bool = False
    reassign_task_id: str = ""
    reassign_assigned_to: str = ""

    show_edit_dialog: bool = False
    edit_task_id: str = ""
    edit_title: str = ""
    edit_description: str = ""
    edit_assigned_to: str = ""
    edit_deadline: str = ""
    edit_priority: str = "medium"
    edit_attachments: list[AttachmentDict] = []

    eod_reports: list[dict] = []
    eod_reports_page: int = 1
    eod_reports_per_page: int = 5
    eod_reports_total_pages: int = 1
    report_schedule_time: str = "18:00"
    report_schedule_timezone: str = "Asia/Kolkata"
    report_schedule_active: bool = True
    show_report_dialog: bool = False
    selected_report_content: str = ""
    selected_report_id: str = ""
    selected_report_data: dict = {}
    report_tasks: list[ReportTaskDict] = []

    # Track which reports are expanded in the collapsible UI
    expanded_report_ids: list[str] = []

    show_comments_dialog: bool = False
    comments_task_id: str = ""
    comments_task_title: str = ""
    comments: list[CommentDict] = []
    new_comment_body: str = ""
    comments_loading: bool = False

    analytics_data: dict = {}
    analytics_loading: bool = False

    show_preview_dialog: bool = False
    preview_url: str = ""
    preview_file_name: str = ""
    preview_is_image: bool = False
    preview_is_pdf: bool = False

    # ── Submissions ─────────────────────────────────────────────────────────
    show_submissions_dialog: bool = False
    submissions_task_id: str = ""
    submissions_task_title: str = ""
    submissions: list[SubmissionDict] = []
    submissions_loading: bool = False

    # ── Employee Management (CEO) ───────────────────────────────────────────
    show_employee_mgmt_dialog: bool = False
    new_emp_name: str = ""
    new_emp_username: str = ""
    new_emp_password: str = ""
    new_emp_role: str = "employee"
    employee_mgmt_toast: str = ""
    employee_mgmt_loading: bool = False

    show_delete_employee_dialog: bool = False
    delete_employee_id: str = ""
    delete_employee_name: str = ""

    # ── Computed vars ───────────────────────────────────────────────────────

    @rx.var
    def filtered_sorted_tasks(self) -> list[TaskDict]:
        rows = self.tasks
        rows = sorted(rows, key=lambda t: t.get("deadline") or "", reverse=not self.sort_deadline_asc)
        return rows

    @rx.var
    def total_tasks(self) -> int:
        # Prefer analytics (unfiltered) when available, else fall back to paginated count
        analytics_total = int(self.analytics_data.get("total", 0))
        if analytics_total > 0:
            return analytics_total
        return self.total_tasks_count

    @rx.var
    def pending_tasks(self) -> int:
        v = int(self.analytics_data.get("pending", 0))
        if v > 0 or self.analytics_data:
            return v
        return len([t for t in self.tasks if t.get("status") == "pending"])

    @rx.var
    def in_progress_tasks(self) -> int:
        v = int(self.analytics_data.get("in_progress", 0))
        if v > 0 or self.analytics_data:
            return v
        return len([t for t in self.tasks if t.get("status") == "in_progress"])

    @rx.var
    def done_tasks(self) -> int:
        v = int(self.analytics_data.get("done", 0))
        if v > 0 or self.analytics_data:
            return v
        return len([t for t in self.tasks if t.get("status") == "done"])

    @rx.var
    def overdue_tasks_count(self) -> int:
        # Use analytics overdue (deadline-based, unfiltered) when available
        v = int(self.analytics_data.get("overdue", 0))
        if v > 0 or self.analytics_data:
            return v
        today = date.today()
        n = 0
        for t in self.tasks:
            if t.get("status") == "done":
                continue
            dl = _parse_iso_date(str(t.get("deadline") or ""))
            if dl is not None and dl < today:
                n += 1
        return n

    @rx.var
    def employee_stat_pending(self) -> int:
        return len([t for t in self.tasks if t.get("status") == "pending"])

    @rx.var
    def employee_stat_overdue(self) -> int:
        today = date.today()
        n = 0
        for t in self.tasks:
            if t.get("status") == "done":
                continue
            dl = _parse_iso_date(str(t.get("deadline") or ""))
            if dl is not None and dl < today:
                n += 1
        return n

    @rx.var
    def employee_stat_completed_today(self) -> int:
        today_s = date.today().isoformat()
        n = 0
        for t in self.tasks:
            if t.get("status") != "done":
                continue
            u = str(t.get("updated_at") or "")
            if len(u) >= 10 and u[:10] == today_s:
                n += 1
        return n

    @rx.var
    def employee_stat_avg_completion_days(self) -> str:
        deltas: list[float] = []
        for t in self.tasks:
            if t.get("status") != "done":
                continue
            c_raw, u_raw = str(t.get("created_at") or ""), str(t.get("updated_at") or "")
            if not c_raw or not u_raw:
                continue
            try:
                c = datetime.fromisoformat(c_raw.replace("Z", "+00:00"))
                u = datetime.fromisoformat(u_raw.replace("Z", "+00:00"))
                days = max(0.0, (u - c).total_seconds() / 86400.0)
                deltas.append(days)
            except (ValueError, TypeError):
                continue
        if not deltas:
            return "—"
        return f"{sum(deltas) / len(deltas):.1f} days"

    @rx.var
    def employee_users(self) -> list[UserDict]:
        return [u for u in self.users if u.get("role") == "employee"]

    @rx.var
    def employee_filter_options(self) -> list[UserDict]:
        """Employee list with an 'All' option prepended for the filter dropdown."""
        all_option = UserDict(id="all", name="All Employees", username="all", role="employee")
        return [all_option] + [u for u in self.users if u.get("role") == "employee"]

    @rx.var
    def pending_file_count(self) -> int:
        return len(self.pending_file_names)

    @rx.var
    def analytics_employee_workload(self) -> list[EmployeeWorkloadDict]:
        return self.analytics_data.get("employee_workload", [])

    @rx.var
    def analytics_overdue_tasks(self) -> list[OverdueTaskDict]:
        return self.analytics_data.get("overdue_tasks", [])

    @rx.var
    def analytics_overdue_count(self) -> int:
        return int(self.analytics_data.get("overdue", 0))

    @rx.var
    def analytics_avg_completion(self) -> str:
        return str(self.analytics_data.get("avg_completion_days", 0))

    @rx.var
    def latest_eod_generated_at_label(self) -> str:
        rows = self.eod_reports
        if not rows:
            return "—"
        g = rows[0].get("generated_at")
        return str(g) if g is not None else "—"

    @rx.var
    def has_next_page(self) -> bool:
        return self.current_page < self.total_pages

    @rx.var
    def has_prev_page(self) -> bool:
        return self.current_page > 1

    # ── Basic setters ───────────────────────────────────────────────────────

    def toggle_sort_deadline(self) -> None:
        self.sort_deadline_asc = not self.sort_deadline_asc

    def open_add_dialog(self) -> None:
        self.show_add_dialog = True
        self.new_priority = "medium"
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

    async def set_status_filter(self, v: str) -> None:
        self.status_filter = v
        self.current_page = 1
        if self.role == "ceo":
            await self._load_tasks_page()
        else:
            await self._load_employee_tasks_page()

    async def set_employee_filter(self, v: str) -> None:
        self.employee_filter = v
        self.current_page = 1
        if self.role == "ceo":
            await self._load_tasks_page()

    async def set_priority_filter(self, v: str) -> None:
        self.priority_filter = v
        self.current_page = 1
        if self.role == "employee":
            await self._load_employee_tasks_page()
        else:
            await self._load_tasks_page()

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

    def set_new_priority(self, v: str) -> None:
        self.new_priority = v

    def set_edit_priority(self, v: str) -> None:
        self.edit_priority = v

    @rx.event
    async def set_pending_file_names(self, files: list[rx.UploadFile]) -> None:
        raw, names = [], []
        for f in files:
            data = await f.read()
            raw.append({"name": f.name, "data": list(data)})
            names.append(f.name)
        self._pending_files_raw = raw
        self.pending_file_names = names

    # ── Pagination controls ─────────────────────────────────────────────────

    async def go_next_page(self) -> None:
        if self.current_page < self.total_pages:
            self.current_page += 1
            if self.role == "ceo":
                await self._load_tasks_page()
            else:
                await self._load_employee_tasks_page()

    async def go_prev_page(self) -> None:
        if self.current_page > 1:
            self.current_page -= 1
            if self.role == "ceo":
                await self._load_tasks_page()
            else:
                await self._load_employee_tasks_page()

    async def go_to_page(self, page: int) -> None:
        self.current_page = max(1, min(page, self.total_pages))
        if self.role == "ceo":
            await self._load_tasks_page()
        else:
            await self._load_employee_tasks_page()

    # ── EOD report expand/collapse ──────────────────────────────────────────

    def toggle_report_expanded(self, report_id: str) -> None:
        if report_id in self.expanded_report_ids:
            self.expanded_report_ids = [r for r in self.expanded_report_ids if r != report_id]
        else:
            self.expanded_report_ids = self.expanded_report_ids + [report_id]

    # ── Helper ──────────────────────────────────────────────────────────────

    def _build_task_dict(self, t: dict[str, Any], user_name_by_id: dict[str, str] | None = None) -> TaskDict:
        uid = str(t.get("assigned_to") or "")
        deadline_str = str(t.get("deadline") or "")
        st = str(t.get("status") or "pending")
        dlbl, dcol = _deadline_label_and_color(deadline_str, st)
        tt = str(t.get("task_type") or "").strip() or "General"
        return TaskDict(
            id=str(t.get("id") or ""),
            title=str(t.get("title") or ""),
            description=str(t.get("description") or ""),
            assigned_to=uid,
            assigned_to_name=(user_name_by_id or {}).get(uid, ""),
            status=st,
            progress=int(t.get("progress") or 0),
            deadline=deadline_str,
            attachment_name=str(t.get("attachment_name") or ""),
            attachments=[
                AttachmentDict(id=str(a.get("id") or ""), file_name=str(a.get("file_name") or ""),
                               uploaded_at=str(a.get("uploaded_at") or ""))
                for a in (t.get("attachments") or [])
            ],
            comment_count=int(t.get("comment_count") or 0),
            submission_count=int(t.get("submission_count") or 0),
            priority=_task_priority_from_api(t.get("priority")),
            created_at=str(t.get("created_at") or ""),
            updated_at=str(t.get("updated_at") or ""),
            task_type=tt,
            deadline_label=dlbl,
            deadline_label_color=dcol,
        )

    # ── Data loaders (paginated) ────────────────────────────────────────────

    async def _load_tasks_page(self) -> None:
        params = f"?page={self.current_page}&page_size={self.page_size}"
        if self.status_filter and self.status_filter != "all":
            params += f"&status={self.status_filter}"
        if self.employee_filter and self.employee_filter != "all":
            params += f"&assigned_to={self.employee_filter}"

        r1 = await self.api("GET", f"/api/tasks/{params}")
        if r1.status_code == 200:
            data = r1.json()
            user_name_by_id = {u.get("id"): u.get("name") for u in self.users}
            self.tasks = [self._build_task_dict(t, user_name_by_id) for t in data.get("items", [])]
            self.total_tasks_count = data.get("total", 0)
            self.total_pages = data.get("total_pages", 1)
        else:
            self.error = "Failed to load tasks."

    async def _load_employee_tasks_page(self) -> None:
        params = f"?page={self.current_page}&page_size={self.page_size}"
        if self.status_filter and self.status_filter != "all":
            params += f"&status={self.status_filter}"
        if self.priority_filter and self.priority_filter != "all":
            params += f"&priority={self.priority_filter}"

        r = await self.api("GET", f"/api/tasks/my{params}")
        if r.status_code == 200:
            data = r.json()
            self.tasks = [self._build_task_dict(t) for t in data.get("items", [])]
            self.total_tasks_count = data.get("total", 0)
            self.total_pages = data.get("total_pages", 1)
        else:
            self.error = "Failed to load tasks."

    async def load_ceo_dashboard(self):
        if self.role != "ceo":
            return rx.redirect("/login")
        self.error = ""
        self.is_loading = True
        try:
            r2 = await self.api("GET", "/api/users/")
            users: list[UserDict] = []
            if r2.status_code == 200:
                users = [UserDict(id=str(u.get("id") or ""), name=str(u.get("name") or ""),
                                  username=str(u.get("username") or ""), role=str(u.get("role") or ""))
                         for u in r2.json()]
                self.users = users
            else:
                self.error = "Failed to load users."

            await self._load_tasks_page()
        finally:
            self.is_loading = False

    async def load_employee_tasks(self):
        if self.role != "employee":
            return rx.redirect("/dashboard")
        self.error = ""
        self.is_loading = True
        try:
            await self._load_employee_tasks_page()
        finally:
            self.is_loading = False

    # ── Lightweight poll ────────────────────────────────────────────────────

    @rx.event
    async def poll_summary(self) -> None:
        r = await self.api("GET", "/api/summary/counts")
        if r.status_code != 200:
            return
        data = r.json()
        last_updated = data.get("last_updated") or ""

        if last_updated and last_updated != self._last_known_updated:
            self._last_known_updated = last_updated
            if self.role == "ceo":
                await self._load_tasks_page()
            else:
                await self._load_employee_tasks_page()

        self.total_tasks_count = data.get("total", self.total_tasks_count)

    # ── Create task ─────────────────────────────────────────────────────────

    @rx.event
    async def create_task_with_files(self, files: list[rx.UploadFile]) -> None:
        self.toast = ""
        try:
            deadline = self.new_deadline
            if deadline and "/" in deadline:
                p = deadline.split("/")
                if len(p) == 3:
                    deadline = f"{p[2]}-{p[0].zfill(2)}-{p[1].zfill(2)}"
            payload = {
                "title": self.new_title,
                "description": self.new_description,
                "assigned_to": self.new_assigned_to,
                "deadline": deadline,
                "priority": self.new_priority or "medium",
            }
            r = await self.api("POST", "/api/tasks/", json=payload)
            if r.status_code != 200:
                self.toast = f"Failed to create task ({r.status_code})"
                return
            task_id = r.json().get("id")
            raw_files = list(self._pending_files_raw)
            if not raw_files and files:
                for f in files:
                    raw_files.append({"name": f.name, "data": list(await f.read())})
            if raw_files and task_id:
                headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
                file_tuples = [("files", (e["name"], bytes(e["data"]))) for e in raw_files]
                async with httpx.AsyncClient(timeout=120.0) as client:
                    ur = await client.post(f"{_api_base()}/api/tasks/{task_id}/attach",
                                           files=file_tuples, headers=headers)
                if ur.status_code != 200:
                    self.toast = f"Task created but file upload failed ({ur.status_code})."
            self.show_add_dialog = False
            self.pending_file_names = []
            self._pending_files_raw = []
            self.new_title = self.new_description = self.new_assigned_to = self.new_deadline = ""
            self.new_priority = "medium"
            await self.load_ceo_dashboard()
        except Exception as e:
            self.toast = f"Failed to create task: {e}"

    # ── Attachment upload ───────────────────────────────────────────────────

    @rx.event
    async def upload_attachment(self, files: list[rx.UploadFile]):
        if self.role != "ceo" or not files or not self.attach_task_id:
            return
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
            file_tuples = [("files", (f.name, await f.read())) for f in files]
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(f"{_api_base()}/api/tasks/{self.attach_task_id}/attach",
                                      files=file_tuples, headers=headers)
            if r.status_code != 200:
                self.toast = "Failed to upload attachment."
                return
            self.show_attach_dialog = False
            await self.load_ceo_dashboard()
        except Exception:
            self.toast = "Failed to upload attachment."

    # ── Task actions ────────────────────────────────────────────────────────

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

    # ── Download attachment ─────────────────────────────────────────────────

    @rx.event
    async def download_attachment(self, task_id: str, attachment_id: str, file_name: str) -> None:
        public_base = os.getenv("PUBLIC_API_URL", "http://localhost:8000").rstrip("/")
        url = f"{public_base}/api/tasks/{task_id}/attachments/{attachment_id}/download"
        token = self.access_token
        safe_url = url.replace("\\", "\\\\").replace("`", "\\`")
        safe_token = token.replace("\\", "\\\\").replace("`", "\\`") if token else ""
        safe_name = file_name.replace("\\", "\\\\").replace("`", "\\`")
        script = f"""(async()=>{{try{{const h={{}};const t=`{safe_token}`;if(t)h['Authorization']='Bearer '+t;const r=await fetch(`{safe_url}`,{{headers:h}});if(!r.ok)return;const b=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=`{safe_name}`;document.body.appendChild(a);a.click();setTimeout(()=>{{URL.revokeObjectURL(a.href);a.remove();}},2000)}}catch(e){{console.error(e)}}}})();"""
        yield rx.call_script(script)

    # ── Download submission ─────────────────────────────────────────────────

    @rx.event
    async def download_submission(self, task_id: str, submission_id: str, file_name: str) -> None:
        public_base = os.getenv("PUBLIC_API_URL", "http://localhost:8000").rstrip("/")
        url = f"{public_base}/api/tasks/{task_id}/submissions/{submission_id}/download"
        token = self.access_token
        safe_url = url.replace("\\", "\\\\").replace("`", "\\`")
        safe_token = token.replace("\\", "\\\\").replace("`", "\\`") if token else ""
        safe_name = file_name.replace("\\", "\\\\").replace("`", "\\`")
        script = f"""(async()=>{{try{{const h={{}};const t=`{safe_token}`;if(t)h['Authorization']='Bearer '+t;const r=await fetch(`{safe_url}`,{{headers:h}});if(!r.ok)return;const b=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=`{safe_name}`;document.body.appendChild(a);a.click();setTimeout(()=>{{URL.revokeObjectURL(a.href);a.remove();}},2000)}}catch(e){{console.error(e)}}}})();"""
        yield rx.call_script(script)

    # ── File Preview ───────────────────────────────────────────────────────

    @rx.event
    async def open_preview(self, task_id: str, file_id: str, file_name: str) -> None:
        public_base = os.getenv("PUBLIC_API_URL", "http://localhost:8000").rstrip("/")
        url = f"{public_base}/api/tasks/{task_id}/attachments/{file_id}/preview"
        self._do_preview(file_name)
        token = self.access_token
        safe_url = url.replace("\\", "\\\\").replace("`", "\\`")
        safe_token = token.replace("\\", "\\\\").replace("`", "\\`") if token else ""
        script = f"""(async()=>{{try{{const h={{}};const t=`{safe_token}`;if(t)h['Authorization']='Bearer '+t;const r=await fetch(`{safe_url}`,{{headers:h}});if(!r.ok)return;const b=await r.blob();const u=URL.createObjectURL(b);const el=document.getElementById('taskme-preview-img');if(el)el.src=u;const el2=document.getElementById('taskme-preview-frame');if(el2)el2.src=u;}}catch(e){{console.error(e)}}}})();"""
        yield rx.call_script(script)

    @rx.event
    async def open_submission_preview(self, task_id: str, sub_id: str, file_name: str) -> None:
        public_base = os.getenv("PUBLIC_API_URL", "http://localhost:8000").rstrip("/")
        url = f"{public_base}/api/tasks/{task_id}/submissions/{sub_id}/preview"
        self._do_preview(file_name)
        token = self.access_token
        safe_url = url.replace("\\", "\\\\").replace("`", "\\`")
        safe_token = token.replace("\\", "\\\\").replace("`", "\\`") if token else ""
        script = f"""(async()=>{{try{{const h={{}};const t=`{safe_token}`;if(t)h['Authorization']='Bearer '+t;const r=await fetch(`{safe_url}`,{{headers:h}});if(!r.ok)return;const b=await r.blob();const u=URL.createObjectURL(b);const el=document.getElementById('taskme-preview-img');if(el)el.src=u;const el2=document.getElementById('taskme-preview-frame');if(el2)el2.src=u;}}catch(e){{console.error(e)}}}})();"""
        yield rx.call_script(script)

    def _do_preview(self, file_name: str) -> None:
        lower = file_name.lower()
        self.preview_is_image = any(lower.endswith(e) for e in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"))
        self.preview_is_pdf = lower.endswith(".pdf")
        self.preview_file_name = file_name
        self.preview_url = ""
        self.show_preview_dialog = True

    def close_preview(self) -> None:
        self.show_preview_dialog = False
        self.preview_url = ""
        self.preview_file_name = ""

    def set_preview_dialog_open(self, open_: bool) -> None:
        if not open_:
            self.close_preview()

    # ── Notifications ───────────────────────────────────────────────────────

    @rx.event
    async def poll_notifications(self) -> None:
        r = await self.api("GET", "/api/notifications/poll")
        if r.status_code != 200:
            return
        data = r.json()
        if not data:
            return
        notif_id = data.get("id")
        message = data.get("message") or "You have a notification."
        if getattr(self, "notification_permission", "") == "granted":
            yield rx.call_script(f"""try{{new Notification("Taskme",{{body:{message!r}}})}}catch(e){{}}""")
        else:
            self.toast = message
        if notif_id:
            await self.api("PATCH", f"/api/notifications/{notif_id}/read")

    # ── Reassign ────────────────────────────────────────────────────────────

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
        r = await self.api("PATCH", f"/api/tasks/{self.reassign_task_id}/reassign",
                           json={"assigned_to": self.reassign_assigned_to})
        if r.status_code == 200:
            self.show_reassign_dialog = False
            self.reassign_task_id = self.reassign_assigned_to = ""
            await self.load_ceo_dashboard()
        else:
            self.toast = "Failed to reassign task."

    # ── EOD Reports ─────────────────────────────────────────────────────────

    async def load_eod_reports(self) -> None:
        if self.role != "ceo":
            return
        try:
            r = await self.api("GET", f"/api/reports/?page={self.eod_reports_page}&page_size={self.eod_reports_per_page}")
            if r.status_code == 200:
                data = r.json()
                self.eod_reports = data.get("items", [])
                self.eod_reports_total_pages = data.get("total_pages", 1)
        except Exception:
            pass

    async def eod_reports_go_next(self) -> None:
        if self.eod_reports_page < self.eod_reports_total_pages:
            self.eod_reports_page += 1
            self.expanded_report_ids = []
            await self.load_eod_reports()

    async def eod_reports_go_prev(self) -> None:
        if self.eod_reports_page > 1:
            self.eod_reports_page -= 1
            self.expanded_report_ids = []
            await self.load_eod_reports()

    async def load_more_reports(self) -> None:
        if self.eod_reports_page < self.eod_reports_total_pages:
            self.eod_reports_page += 1
            await self.load_eod_reports()

    async def load_report_schedule(self) -> None:
        if self.role != "ceo":
            return
        try:
            r = await self.api("GET", "/api/reports/schedule")
            if r.status_code == 200:
                d = r.json()
                self.report_schedule_time = d.get("report_time", "18:00")
                self.report_schedule_timezone = d.get("timezone", "Asia/Kolkata")
                self.report_schedule_active = d.get("is_active", True)
        except Exception:
            pass

    def set_report_time(self, v: str) -> None:
        self.report_schedule_time = v

    def set_report_timezone(self, v: str) -> None:
        self.report_schedule_timezone = v

    def set_report_active(self, v: str) -> None:
        self.report_schedule_active = v == "active"

    def set_report_schedule_active_bool(self, checked: bool) -> None:
        self.report_schedule_active = bool(checked)

    async def save_report_schedule(self) -> None:
        r = await self.api("POST", "/api/reports/schedule",
                           json={"report_time": self.report_schedule_time,
                                 "timezone": self.report_schedule_timezone,
                                 "is_active": self.report_schedule_active})
        self.toast = "Schedule saved." if r.status_code == 200 else "Failed to save schedule."

    async def generate_report_now(self) -> None:
        r = await self.api("POST", "/api/reports/generate")
        if r.status_code == 200:
            self.toast = "Report generated."
            await self.load_eod_reports()
        else:
            self.toast = "Failed to generate report."

    async def view_report(self, report_id: str) -> None:
        import json
        self.selected_report_id = report_id
        r = await self.api("GET", f"/api/reports/{report_id}")
        if r.status_code == 200:
            d = r.json()
            self.selected_report_data = d
            self.selected_report_content = d.get("content", "")
            try:
                parsed = json.loads(d.get("content", "{}"))
                raw_tasks = parsed.get("tasks", [])
                self.report_tasks = [
                    ReportTaskDict(
                        id=str(t.get("id") or ""),
                        title=str(t.get("title") or ""),
                        assigned_to_name=str(t.get("assigned_to_name") or ""),
                        status=str(t.get("status") or ""),
                        progress=int(t.get("progress") or 0),
                        deadline=str(t.get("deadline") or ""),
                        submissions=[
                            ReportSubmissionDict(
                                id=str(s.get("id") or ""),
                                file_name=str(s.get("file_name") or ""),
                                uploaded_at=str(s.get("uploaded_at") or ""),
                                task_id=str(s.get("task_id") or ""),
                            )
                            for s in (t.get("submissions") or [])
                        ],
                    )
                    for t in raw_tasks
                ]
            except (json.JSONDecodeError, TypeError):
                self.report_tasks = []
            self.show_report_dialog = True
        else:
            self.toast = "Failed to load report."

    def close_report_dialog(self) -> None:
        self.show_report_dialog = False
        self.selected_report_content = ""
        self.selected_report_data = {}
        self.report_tasks = []

    def set_report_dialog_open(self, open_: bool) -> None:
        self.show_report_dialog = bool(open_)
        if not open_:
            self.selected_report_content = ""
            self.selected_report_data = {}
            self.report_tasks = []

    # ── Edit Task ───────────────────────────────────────────────────────────

    def open_edit_dialog(self, task_id: str) -> None:
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        if not task:
            return
        self.edit_task_id = task_id
        self.edit_title = task["title"]
        self.edit_description = task["description"]
        self.edit_assigned_to = str(task.get("assigned_to") or "")
        self.edit_deadline = task["deadline"]
        self.edit_priority = task.get("priority", "medium")
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
            p = deadline.split("/")
            if len(p) == 3:
                deadline = f"{p[2]}-{p[0].zfill(2)}-{p[1].zfill(2)}"
        payload = {
            "title": self.edit_title,
            "description": self.edit_description,
            "assigned_to": self.edit_assigned_to,
            "deadline": deadline,
            "priority": self.edit_priority or "medium",
        }
        r = await self.api("PUT", f"/api/tasks/{self.edit_task_id}", json=payload)
        if r.status_code == 200:
            self.show_edit_dialog = False
            await self.load_ceo_dashboard()
        else:
            self.toast = f"Failed to save task ({r.status_code})"

    async def delete_attachment_from_edit(self, attachment_id: str) -> None:
        if not self.edit_task_id:
            return
        r = await self.api("DELETE", f"/api/tasks/{self.edit_task_id}/attachments/{attachment_id}")
        if r.status_code == 200:
            self.edit_attachments = [a for a in self.edit_attachments if a["id"] != attachment_id]
            await self.load_ceo_dashboard()
        else:
            self.toast = "Failed to delete attachment."

    @rx.event
    async def upload_edit_attachments(self, files: list[rx.UploadFile]) -> None:
        if not files or not self.edit_task_id:
            return
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
            file_tuples = [("files", (f.name, await f.read())) for f in files]
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(f"{_api_base()}/api/tasks/{self.edit_task_id}/attach",
                                      files=file_tuples, headers=headers)
            if r.status_code == 200:
                updated = r.json()
                self.edit_attachments = [
                    AttachmentDict(id=str(a.get("id") or ""), file_name=str(a.get("file_name") or ""),
                                   uploaded_at=str(a.get("uploaded_at") or ""))
                    for a in (updated.get("attachments") or [])
                ]
                await self.load_ceo_dashboard()
            else:
                self.toast = "Failed to upload file(s)."
        except Exception as e:
            self.toast = f"Upload error: {e}"

    # ── Comments ────────────────────────────────────────────────────────────

    def set_new_comment_body(self, v: str) -> None:
        self.new_comment_body = v

    def set_comments_dialog_open(self, open_: bool) -> None:
        self.show_comments_dialog = bool(open_)
        if not open_:
            self.comments_task_id = ""
            self.comments = []
            self.new_comment_body = ""

    async def open_comments_dialog(self, task_id: str) -> None:
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        self.comments_task_id = task_id
        self.comments_task_title = task["title"] if task else ""
        self.new_comment_body = ""
        self.show_comments_dialog = True
        await self.load_comments()

    async def load_comments(self) -> None:
        if not self.comments_task_id:
            return
        self.comments_loading = True
        try:
            r = await self.api("GET", f"/api/tasks/{self.comments_task_id}/comments")
            if r.status_code == 200:
                self.comments = [
                    CommentDict(id=str(c.get("id") or ""), task_id=str(c.get("task_id") or ""),
                                user_id=str(c.get("user_id") or ""), author_name=str(c.get("author_name") or ""),
                                body=str(c.get("body") or ""), created_at=str(c.get("created_at") or ""))
                    for c in r.json()
                ]
        finally:
            self.comments_loading = False

    async def post_comment(self) -> None:
        if not self.comments_task_id or not self.new_comment_body.strip():
            return
        r = await self.api("POST", f"/api/tasks/{self.comments_task_id}/comments",
                           json={"body": self.new_comment_body.strip()})
        if r.status_code == 200:
            self.new_comment_body = ""
            await self.load_comments()
            if self.role == "ceo":
                await self.load_ceo_dashboard()
            else:
                await self.load_employee_tasks()
        else:
            self.toast = "Failed to post comment."

    # ── Submissions ─────────────────────────────────────────────────────────

    def set_submissions_dialog_open(self, open_: bool) -> None:
        self.show_submissions_dialog = bool(open_)
        if not open_:
            self.submissions_task_id = ""
            self.submissions = []

    async def open_submissions_dialog(self, task_id: str) -> None:
        task = next((t for t in self.tasks if t["id"] == task_id), None)
        self.submissions_task_id = task_id
        self.submissions_task_title = task["title"] if task else ""
        self.show_submissions_dialog = True
        await self.load_submissions()

    async def load_submissions(self) -> None:
        if not self.submissions_task_id:
            return
        self.submissions_loading = True
        try:
            r = await self.api("GET", f"/api/tasks/{self.submissions_task_id}/submissions")
            if r.status_code == 200:
                self.submissions = [
                    SubmissionDict(
                        id=str(s.get("id") or ""), file_name=str(s.get("file_name") or ""),
                        note=str(s.get("note") or ""), uploaded_at=str(s.get("uploaded_at") or ""),
                        uploaded_by=str(s.get("uploaded_by") or ""),
                        uploader_name=str(s.get("uploader_name") or ""),
                    )
                    for s in r.json()
                ]
        finally:
            self.submissions_loading = False

    @rx.event
    async def upload_submission(self, files: list[rx.UploadFile]) -> None:
        if not files or not self.submissions_task_id:
            return
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"} if self.access_token else {}
            file_tuples = [("files", (f.name, await f.read())) for f in files]
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(
                    f"{_api_base()}/api/tasks/{self.submissions_task_id}/submissions",
                    files=file_tuples, headers=headers)
            if r.status_code == 200:
                self.toast = "Files submitted successfully!"
                await self.load_submissions()
                await self.load_employee_tasks()
            else:
                self.toast = f"Failed to submit files ({r.status_code})."
        except Exception as e:
            self.toast = f"Submission error: {e}"

    # ── Analytics ───────────────────────────────────────────────────────────

    async def load_analytics(self) -> None:
        if self.role != "ceo":
            return
        self.analytics_loading = True
        try:
            r = await self.api("GET", "/api/analytics/")
            if r.status_code == 200:
                self.analytics_data = r.json()
        except Exception:
            pass
        finally:
            self.analytics_loading = False

    # ── Employee Management (CEO) ───────────────────────────────────────────

    def open_add_employee_dialog(self) -> None:
        self.show_employee_mgmt_dialog = True
        self.new_emp_name = ""
        self.new_emp_username = ""
        self.new_emp_password = ""
        self.new_emp_role = "employee"
        self.employee_mgmt_toast = ""

    def close_add_employee_dialog(self) -> None:
        self.show_employee_mgmt_dialog = False
        self.new_emp_name = ""
        self.new_emp_username = ""
        self.new_emp_password = ""
        self.new_emp_role = "employee"
        self.employee_mgmt_toast = ""

    def set_add_employee_dialog_open(self, open_: bool) -> None:
        self.show_employee_mgmt_dialog = bool(open_)
        if not open_:
            self.close_add_employee_dialog()

    def set_new_emp_name(self, v: str) -> None:
        self.new_emp_name = v

    def set_new_emp_username(self, v: str) -> None:
        self.new_emp_username = v

    def set_new_emp_password(self, v: str) -> None:
        self.new_emp_password = v

    def set_new_emp_role(self, v: str) -> None:
        self.new_emp_role = v

    async def create_employee(self) -> None:
        self.employee_mgmt_toast = ""
        if not self.new_emp_name.strip():
            self.employee_mgmt_toast = "Name is required."
            return
        if not self.new_emp_username.strip():
            self.employee_mgmt_toast = "Username is required."
            return
        if not self.new_emp_password.strip():
            self.employee_mgmt_toast = "Password is required."
            return
        if len(self.new_emp_password.strip()) < 3:
            self.employee_mgmt_toast = "Password must be at least 3 characters."
            return

        self.employee_mgmt_loading = True
        try:
            payload = {
                "name": self.new_emp_name.strip(),
                "username": self.new_emp_username.strip(),
                "password": self.new_emp_password.strip(),
                "role": self.new_emp_role or "employee",
            }
            r = await self.api("POST", "/api/users/", json=payload)
            if r.status_code == 200:
                self.show_employee_mgmt_dialog = False
                self.new_emp_name = ""
                self.new_emp_username = ""
                self.new_emp_password = ""
                self.new_emp_role = "employee"
                self.employee_mgmt_toast = ""
                self.toast = "Employee created successfully!"
                # Reload users list
                r2 = await self.api("GET", "/api/users/")
                if r2.status_code == 200:
                    self.users = [
                        UserDict(
                            id=str(u.get("id") or ""),
                            name=str(u.get("name") or ""),
                            username=str(u.get("username") or ""),
                            role=str(u.get("role") or ""),
                        )
                        for u in r2.json()
                    ]
            else:
                try:
                    err = r.json()
                    msg = err.get("detail", {}).get("message", "") if isinstance(err.get("detail"), dict) else str(err.get("detail", ""))
                except Exception:
                    msg = ""
                self.employee_mgmt_toast = msg or f"Failed to create employee ({r.status_code})."
        except Exception as e:
            self.employee_mgmt_toast = f"Error: {e}"
        finally:
            self.employee_mgmt_loading = False

    def open_delete_employee_dialog(self, user_id: str) -> None:
        user = next((u for u in self.users if u["id"] == user_id), None)
        if not user:
            return
        self.delete_employee_id = user_id
        self.delete_employee_name = user.get("name", "Unknown")
        self.show_delete_employee_dialog = True

    def close_delete_employee_dialog(self) -> None:
        self.show_delete_employee_dialog = False
        self.delete_employee_id = ""
        self.delete_employee_name = ""

    def set_delete_employee_dialog_open(self, open_: bool) -> None:
        self.show_delete_employee_dialog = bool(open_)
        if not open_:
            self.close_delete_employee_dialog()

    async def delete_employee(self) -> None:
        if not self.delete_employee_id:
            return
        self.employee_mgmt_loading = True
        try:
            r = await self.api("DELETE", f"/api/users/{self.delete_employee_id}")
            if r.status_code == 200:
                self.show_delete_employee_dialog = False
                self.toast = f"Employee '{self.delete_employee_name}' deleted."
                self.delete_employee_id = ""
                self.delete_employee_name = ""
                # Reload users list
                r2 = await self.api("GET", "/api/users/")
                if r2.status_code == 200:
                    self.users = [
                        UserDict(
                            id=str(u.get("id") or ""),
                            name=str(u.get("name") or ""),
                            username=str(u.get("username") or ""),
                            role=str(u.get("role") or ""),
                        )
                        for u in r2.json()
                    ]
            else:
                self.toast = f"Failed to delete employee ({r.status_code})."
        except Exception as e:
            self.toast = f"Delete error: {e}"
        finally:
            self.employee_mgmt_loading = False

    # ── Task Detail (Employee View) ─────────────────────────────────────────
    # Stub: referenced by employee_view.py table row on_click.

    def open_task_detail(self, task_id: str) -> None:
        """Placeholder for opening a task detail view from the employee table."""
        pass
