from __future__ import annotations

import reflex as rx

from taskme.components.progress_bar import progress_bar
from taskme.components.status_badge import status_badge
from taskme.state.task_state import TaskState


# ── Shared dashboard chrome (tables + surfaces) ─────────────────────────────

def _ceo_table_styles() -> rx.Component:
    return rx.el.style(
        """
        .ceo-task-table tbody tr { transition: background-color 0.15s ease; }
        .ceo-task-table tbody tr:hover { background-color: rgba(26, 43, 86, 0.045); }
        .ceo-task-table th, .ceo-task-table td {
          padding: 0.9rem 1rem;
          vertical-align: middle;
        }
        .ceo-task-table thead th {
          font-weight: 700;
          font-size: 0.68rem;
          text-transform: uppercase;
          letter-spacing: 0.055em;
          color: #64748b;
        }
        .ceo-workload-table tbody tr { transition: background-color 0.15s ease; }
        .ceo-workload-table tbody tr:hover { background-color: rgba(26, 43, 86, 0.04); }
        .ceo-workload-table th, .ceo-workload-table td { padding: 0.7rem 0.85rem; }
        """
    )


def _priority_badge(priority) -> rx.Component:
    return rx.badge(
        rx.cond(
            priority == "high",
            "High",
            rx.cond(priority == "low", "Low", "Medium"),
        ),
        color_scheme=rx.cond(
            priority == "high",
            "red",
            rx.cond(priority == "low", "gray", "orange"),
        ),
        variant="solid",
        padding_x="0.65rem",
        padding_y="0.28rem",
        font_size="0.72rem",
        font_weight="600",
        border_radius="999px",
    )


# ── CEO app header (dashboard only; premium control bar) ───────────────────

def _ceo_app_header() -> rx.Component:
    """Logo, avatar, logout + page title row."""
    return rx.box(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.el.img(
                        src="/taskme-logo-header.png",
                        alt="TaskMe",
                        style={
                            "height": "64px",
                            "width": "auto",
                            "max_width": "min(100%, 280px)",
                            "display": "block",
                            "object_fit": "contain",
                        },
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.hstack(
                            rx.box(
                                rx.text(
                                    rx.cond(
                                        TaskState.name != "",
                                        TaskState.name[:1].to_string(),
                                        "?",
                                    ),
                                    color="white",
                                    font_weight="700",
                                    font_size="0.9rem",
                                    text_transform="uppercase",
                                ),
                                width="40px",
                                height="40px",
                                border_radius="50%",
                                background_color="#1A2B56",
                                display="flex",
                                align_items="center",
                                justify_content="center",
                                flex_shrink="0",
                                border="2px solid rgba(229, 163, 43, 0.45)",
                            ),
                            rx.text(
                                TaskState.name,
                                font_weight="600",
                                font_size="0.95rem",
                                color="#1A1A1A",
                                max_width="160px",
                                overflow="hidden",
                                text_overflow="ellipsis",
                                white_space="nowrap",
                            ),
                            spacing="3",
                            align="center",
                        ),
                        rx.button(
                            "Logout",
                            on_click=TaskState.logout,
                            color_scheme="orange",
                            variant="outline",
                            size="2",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    width="100%",
                    align="center",
                    padding_y="0.85rem",
                ),
                rx.divider(border_color="rgba(15, 23, 42, 0.08)"),
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            rx.Var.create("Good Morning, ") + TaskState.name,
                            font_size="1.5rem",
                            font_weight="700",
                            color="#1A1A1A",
                            letter_spacing="-0.02em",
                            line_height="1.25",
                        ),
                        rx.text(
                            "CEO Dashboard",
                            font_size="1.15rem",
                            font_weight="800",
                            color="#374151",
                            margin_top="0.5rem",
                            letter_spacing="-0.01em",
                        ),
                        spacing="0",
                        align_items="start",
                    ),
                    rx.spacer(),
                    rx.hstack(
                        rx.select(
                            ["all", "pending", "in_progress", "done", "overdue"],
                            value=TaskState.status_filter,
                            on_change=TaskState.set_status_filter,
                            width="220px",
                        ),
                        rx.button(
                            "Add Task",
                            color_scheme="orange",
                            variant="solid",
                            on_click=TaskState.open_add_dialog,
                        ),
                        spacing="3",
                        align="center",
                        align_self="start",
                        margin_top="0.15rem",
                    ),
                    width="100%",
                    align="start",
                    padding_y="1rem",
                ),
                spacing="0",
                width="100%",
            ),
            max_width="1200px",
            margin_x="auto",
            width="100%",
            padding_x="1.5rem",
        ),
        background_color="#FFFFFF",
        border_bottom="1px solid rgba(15, 23, 42, 0.06)",
        box_shadow="0 4px 24px -6px rgba(15, 23, 42, 0.1)",
        position="sticky",
        top="0",
        z_index="30",
        width="100%",
    )


# ── Summary cards ───────────────────────────────────────────────────────────

def _summary_cards() -> rx.Component:
    def kpi_card(
        label: str,
        value,
        icon_name: str,
        value_color: str,
        icon_color: str,
        icon_bg: str,
        border_color: str,
    ) -> rx.Component:
        return rx.box(
            rx.hstack(
                rx.box(
                    rx.icon(icon_name, size=22, color=icon_color),
                    padding="0.7rem",
                    border_radius="12px",
                    background_color=icon_bg,
                    flex_shrink="0",
                ),
                rx.vstack(
                    rx.text(
                        label,
                        color="#64748B",
                        font_size="0.82rem",
                        font_weight="600",
                        letter_spacing="0.02em",
                    ),
                    rx.text(
                        value.to_string(),
                        color=value_color,
                        font_size="1.85rem",
                        font_weight="900",
                        letter_spacing="-0.03em",
                        line_height="1.1",
                    ),
                    spacing="1",
                    align="start",
                ),
                spacing="4",
                align="center",
                width="100%",
            ),
            padding="1.25rem",
            border=f"1px solid {border_color}",
            border_radius="16px",
            background_color="#FFFFFF",
            width="100%",
            box_shadow=(
                "0 2px 8px rgba(15, 23, 42, 0.05), "
                "0 12px 28px -8px rgba(15, 23, 42, 0.08)"
            ),
        )

    return rx.grid(
        kpi_card(
            "Total Tasks",
            TaskState.total_tasks,
            "layout-dashboard",
            "#1A1A1A",
            "#475569",
            "rgba(71, 85, 105, 0.12)",
            "rgba(71, 85, 105, 0.15)",
        ),
        kpi_card(
            "Pending",
            TaskState.pending_tasks,
            "circle-dashed",
            "#CA8A04",
            "#CA8A04",
            "rgba(202, 138, 4, 0.14)",
            "rgba(202, 138, 4, 0.28)",
        ),
        kpi_card(
            "In Progress",
            TaskState.in_progress_tasks,
            "activity",
            "#D97706",
            "#D97706",
            "rgba(217, 119, 6, 0.14)",
            "rgba(245, 158, 11, 0.35)",
        ),
        kpi_card(
            "Done",
            TaskState.done_tasks,
            "check-circle-2",
            "#16A34A",
            "#16A34A",
            "rgba(22, 163, 74, 0.14)",
            "rgba(34, 197, 94, 0.35)",
        ),
        kpi_card(
            "Overdue",
            TaskState.overdue_tasks_count,
            "alert-circle",
            "#DC2626",
            "#DC2626",
            "rgba(220, 38, 38, 0.12)",
            "rgba(239, 68, 68, 0.35)",
        ),
        columns={"initial": "1", "sm": "2", "md": "3", "xl": "5"},
        spacing="5",
        width="100%",
        margin_top="0.5rem",
    )


# ── Analytics section ───────────────────────────────────────────────────────

def _analytics_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon("bar-chart-3", size=20, color="#F97316"),
                rx.text("Analytics", font_size="1.2rem", font_weight="900", color="#1A1A1A"),
                rx.spacer(),
                rx.button("Refresh", size="1", variant="outline", on_click=TaskState.load_analytics),
                spacing="2", width="100%", align="center",
            ),

            # KPI row
            rx.grid(
                rx.box(
                    rx.vstack(
                        rx.text("Avg Completion", color="#6B7280", font_size="0.82rem"),
                        rx.hstack(
                            rx.text(TaskState.analytics_avg_completion, color="#1A1A1A",
                                    font_size="1.6rem", font_weight="900"),
                            rx.text("days", color="#6B7280", font_size="0.85rem"),
                            spacing="1", align="end",
                        ),
                        spacing="0", align="start",
                    ),
                    padding="0.85rem", border="1px solid rgba(251,146,60,0.22)",
                    border_radius="14px", background_color="#FFF8F3",
                    box_shadow="0 2px 8px rgba(15, 23, 42, 0.04)",
                ),
                rx.box(
                    rx.vstack(
                        rx.text("Overdue Tasks", color="#6B7280", font_size="0.82rem"),
                        rx.text(TaskState.analytics_overdue_count.to_string(), color="#EF4444",
                                font_size="1.6rem", font_weight="900"),
                        spacing="0", align="start",
                    ),
                    padding="0.85rem", border="1px solid rgba(239,68,68,0.22)",
                    border_radius="14px", background_color="#FEF2F2",
                    box_shadow="0 2px 8px rgba(15, 23, 42, 0.04)",
                ),
                columns="2", spacing="3", width="100%",
            ),

            # Employee workload table
            rx.cond(
                TaskState.analytics_employee_workload.length() > 0,
                rx.box(
                    rx.text("Employee Workload", font_weight="700", color="#1A1A1A",
                            font_size="0.95rem", margin_bottom="0.5rem"),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Employee"),
                                rx.table.column_header_cell("Total"),
                                rx.table.column_header_cell("Pending"),
                                rx.table.column_header_cell("In Progress"),
                                rx.table.column_header_cell("Done"),
                                rx.table.column_header_cell("Overdue"),
                            )
                        ),
                        rx.table.body(
                            rx.foreach(
                                TaskState.analytics_employee_workload,
                                lambda w: rx.table.row(
                                    rx.table.cell(rx.text(w["name"], font_weight="600")),
                                    rx.table.cell(w["total"].to_string()),
                                    rx.table.cell(rx.text(w["pending"].to_string(), color="#F97316")),
                                    rx.table.cell(rx.text(w["in_progress"].to_string(), color="#F59E0B")),
                                    rx.table.cell(rx.text(w["done"].to_string(), color="#22C55E")),
                                    rx.table.cell(
                                        rx.cond(
                                            w["overdue"] > 0,
                                            rx.badge(w["overdue"].to_string(), color_scheme="red", variant="solid"),
                                            rx.text("0", color="#6B7280"),
                                        )
                                    ),
                                ),
                            ),
                        ),
                        width="100%",
                        class_name="ceo-workload-table",
                    ),
                    width="100%",
                ),
                rx.box(),
            ),

            # Overdue tasks list
            rx.cond(
                TaskState.analytics_overdue_tasks.length() > 0,
                rx.box(
                    rx.text("Overdue Tasks", font_weight="700", color="#EF4444",
                            font_size="0.95rem", margin_bottom="0.5rem"),
                    rx.vstack(
                        rx.foreach(
                            TaskState.analytics_overdue_tasks,
                            lambda t: rx.hstack(
                                rx.badge(t["days_overdue"].to_string() + "d", color_scheme="red",
                                         variant="solid", size="1"),
                                rx.text(t["title"], font_weight="600", color="#1A1A1A", font_size="0.88rem"),
                                rx.text(t["assigned_to_name"], color="#6B7280", font_size="0.82rem"),
                                rx.spacer(),
                                rx.text("Due: " + t["deadline"].to_string(), color="#EF4444", font_size="0.82rem"),
                                width="100%", align="center", spacing="2",
                                padding="0.5rem 0.75rem",
                                border="1px solid rgba(239,68,68,0.2)", border_radius="12px",
                                background_color="#FEF2F2",
                                box_shadow="0 1px 2px rgba(15, 23, 42, 0.04)",
                            ),
                        ),
                        spacing="2", width="100%",
                    ),
                    width="100%",
                ),
                rx.box(),
            ),

            spacing="3", width="100%",
        ),
        margin_top="1rem", padding="1.25rem",
        border="1px solid rgba(15, 23, 42, 0.06)", border_radius="16px",
        background_color="#FFFFFF",
        width="100%",
        box_shadow="0 4px 24px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04)",
    )


# ── Add task dialog ─────────────────────────────────────────────────────────

def _add_task_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.text("Add Task", font_size="1.2rem", font_weight="900", color="#1A1A1A"),
                rx.input(placeholder="Title", value=TaskState.new_title,
                         on_change=TaskState.set_new_title, width="100%"),
                rx.text_area(placeholder="Description", value=TaskState.new_description,
                             on_change=TaskState.set_new_description, width="100%", min_height="90px"),
                rx.select.root(
                    rx.select.trigger(placeholder="Select Employee"),
                    rx.select.content(rx.foreach(TaskState.employee_users,
                                                 lambda u: rx.select.item(u["name"], value=u["id"]))),
                    value=TaskState.new_assigned_to, on_change=TaskState.set_new_assigned_to, width="100%",
                ),
                rx.input(type="date", value=TaskState.new_deadline,
                         on_change=TaskState.set_new_deadline, width="100%"),
                rx.text("Attach Files (optional)", color="#6B7280", font_size="0.85rem", font_weight="600"),
                rx.upload(
                    rx.vstack(
                        rx.icon("upload", color="gray.400", size=24),
                        rx.text("Drag & drop files here, or click to browse",
                                color="#6B7280", font_size="0.85rem", text_align="center"),
                        rx.cond(TaskState.pending_file_count > 0,
                                rx.text(TaskState.pending_file_count.to_string() + " file(s) selected",
                                        color="#F97316", font_size="0.8rem", font_weight="600"),
                                rx.box()),
                        spacing="2", align="center", padding="1rem",
                    ),
                    id="add_task_upload", multiple=True,
                    border="2px dashed rgba(251,146,60,0.35)", border_radius="10px",
                    padding="0.5rem", width="100%",
                    on_drop=TaskState.set_pending_file_names(rx.upload_files(upload_id="add_task_upload")),
                ),
                rx.cond(
                    TaskState.pending_file_count > 0,
                    rx.vstack(
                        rx.foreach(TaskState.pending_file_names,
                                   lambda name: rx.hstack(rx.icon("file", size=14, color="gray.400"),
                                                          rx.text(name, color="#6B7280", font_size="0.8rem"),
                                                          spacing="2", align="center")),
                        spacing="1", width="100%", padding_left="0.25rem",
                    ),
                    rx.box(),
                ),
                rx.hstack(
                    rx.button("Cancel", variant="outline", on_click=TaskState.close_add_dialog),
                    rx.button(
                        "Create Task",
                        color_scheme="orange",
                        variant="solid",
                        on_click=TaskState.create_task_with_files(
                            rx.upload_files(upload_id="add_task_upload")
                        ),
                    ),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="3", padding="1.5rem", background_color="#FFFFFF",
                border_radius="12px", width="100%",
            ),
            max_width="520px",
        ),
        open=TaskState.show_add_dialog, on_open_change=TaskState.set_add_dialog_open,
    )


# ── Attach dialog ───────────────────────────────────────────────────────────

def _attach_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.text("Attach Files", font_size="1.2rem", font_weight="900", color="#1A1A1A"),
                rx.upload(
                    rx.vstack(rx.icon("upload", color="gray.400", size=24),
                              rx.text("Drag & drop or click to select files",
                                      color="#6B7280", font_size="0.85rem"),
                              spacing="2", align="center", padding="1rem"),
                    id="attach_upload", multiple=True,
                    border="2px dashed rgba(251,146,60,0.35)", border_radius="10px", width="100%",
                ),
                rx.hstack(
                    rx.button(
                        "Upload",
                        color_scheme="orange",
                        variant="outline",
                        on_click=TaskState.upload_attachment(rx.upload_files(upload_id="attach_upload")),
                    ),
                    rx.button("Cancel", variant="outline", on_click=TaskState.close_attach_dialog),
                    spacing="3",
                ),
                spacing="3", padding="1.5rem", background_color="#FFFFFF", border_radius="12px",
            )
        ),
        open=TaskState.show_attach_dialog, on_open_change=TaskState.set_attach_dialog_open,
    )


# ── Reassign dialog ────────────────────────────────────────────────────────

def _reassign_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.text("Reassign Task", font_size="1.2rem", font_weight="900", color="#1A1A1A"),
                rx.text("Select a new employee. Progress will reset to 0.",
                        color="#6B7280", font_size="0.85rem"),
                rx.select.root(
                    rx.select.trigger(placeholder="Select Employee"),
                    rx.select.content(rx.foreach(TaskState.employee_users,
                                                 lambda u: rx.select.item(u["name"], value=u["id"]))),
                    value=TaskState.reassign_assigned_to, on_change=TaskState.set_reassign_assigned_to,
                    width="100%",
                ),
                rx.hstack(
                    rx.button("Cancel", variant="outline", on_click=TaskState.close_reassign_dialog),
                    rx.button(
                        "Reassign",
                        color_scheme="orange",
                        variant="outline",
                        on_click=TaskState.reassign_task,
                    ),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="3", padding="1.5rem", background_color="#FFFFFF",
                border_radius="12px", width="100%",
            ),
            max_width="420px",
        ),
        open=TaskState.show_reassign_dialog, on_open_change=TaskState.set_reassign_dialog_open,
    )


# ── Attachment chips with preview ───────────────────────────────────────────

def _attachment_chips(task: rx.Var) -> rx.Component:
    return rx.cond(
        task["attachments"].length() > 0,
        rx.vstack(
            rx.hstack(
                rx.icon("paperclip", size=13, color="#F97316"),
                rx.text(task["attachments"].length().to_string() + " file(s)",
                        color="#F97316", font_size="0.75rem", font_weight="700"),
                spacing="1", align="center",
            ),
            rx.foreach(
                task["attachments"],
                lambda a: rx.hstack(
                    rx.button(
                        rx.hstack(rx.icon("eye", size=11, color="#F97316"),
                                  rx.text(a["file_name"], color="#F97316", font_size="0.72rem"),
                                  spacing="1", align="center"),
                        variant="ghost", size="1",
                        background_color="rgba(249,115,22,0.10)",
                        border="1px solid rgba(251,146,60,0.35)", border_radius="6px",
                        padding_x="0.4rem", padding_y="0.15rem",
                        on_click=TaskState.open_preview(task["id"], a["id"], a["file_name"]),
                        cursor="pointer",
                    ),
                    rx.icon_button(
                        rx.icon("download", size=11), size="1", variant="ghost",
                        color_scheme="orange",
                        on_click=TaskState.download_attachment(task["id"], a["id"], a["file_name"]),
                        title="Download",
                    ),
                    spacing="1", align="center",
                ),
            ),
            spacing="1", align="start",
        ),
        rx.box(),
    )


# ── Pagination controls ────────────────────────────────────────────────────

def _pagination_controls() -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.hstack(rx.icon("chevron-left", size=14), rx.text("Prev"), spacing="1", align="center"),
            on_click=TaskState.go_prev_page,
            is_disabled=~TaskState.has_prev_page,
            variant="outline",
            size="2",
            color_scheme="orange",
        ),
        rx.hstack(
            rx.text("Page", color="#6B7280", font_size="0.85rem"),
            rx.text(
                TaskState.current_page.to_string(),
                font_weight="700",
                color="#1A1A1A",
                font_size="0.95rem",
            ),
            rx.text("of", color="#6B7280", font_size="0.85rem"),
            rx.text(
                TaskState.total_pages.to_string(),
                font_weight="700",
                color="#1A1A1A",
                font_size="0.95rem",
            ),
            spacing="2",
            align="center",
        ),
        rx.button(
            rx.hstack(rx.text("Next"), rx.icon("chevron-right", size=14), spacing="1", align="center"),
            on_click=TaskState.go_next_page,
            is_disabled=~TaskState.has_next_page,
            variant="outline",
            size="2",
            color_scheme="orange",
        ),
        spacing="4",
        justify="center",
        width="100%",
        padding_y="1rem",
        padding_x="0.5rem",
    )


# ── Task table ──────────────────────────────────────────────────────────────

def _task_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Task"),
                rx.table.column_header_cell("Assigned To"),
                rx.table.column_header_cell("Priority"),
                rx.table.column_header_cell("Status"),
                rx.table.column_header_cell("Progress"),
                rx.table.column_header_cell(
                    rx.hstack(
                        rx.text("Deadline"),
                        rx.button(
                            "Sort",
                            size="1",
                            variant="ghost",
                            on_click=TaskState.toggle_sort_deadline,
                        ),
                        spacing="2",
                    )
                ),
                rx.table.column_header_cell("Files & actions"),
            )
        ),
        rx.table.body(
            rx.foreach(
                TaskState.filtered_sorted_tasks,
                lambda task: rx.table.row(
                    rx.table.cell(
                        rx.vstack(
                            rx.text(task["title"], color="#1A1A1A", font_weight="700"),
                            rx.text(
                                task["description"],
                                color="#6B7280",
                                font_size="0.82rem",
                                max_width="220px",
                                overflow="hidden",
                                text_overflow="ellipsis",
                                white_space="nowrap",
                            ),
                            spacing="1",
                        )
                    ),
                    rx.table.cell(rx.text(task["assigned_to_name"], color="#1A1A1A")),
                    rx.table.cell(_priority_badge(task["priority"])),
                    rx.table.cell(status_badge(task["status"])),
                    rx.table.cell(
                        rx.vstack(
                            rx.text(task["progress"].to_string() + "%", color="#1A1A1A"),
                            progress_bar(task["progress"]),
                            spacing="2",
                        )
                    ),
                    rx.table.cell(rx.text(task["deadline"].to_string(), color="#6B7280")),
                    rx.table.cell(
                        rx.vstack(
                            _attachment_chips(task),
                            rx.box(
                                rx.hstack(
                                    rx.hstack(
                                        rx.icon_button(
                                            rx.icon("pencil", size=14),
                                            size="2",
                                            variant="ghost",
                                            color_scheme="orange",
                                            on_click=TaskState.open_edit_dialog(task["id"]),
                                            title="Edit task",
                                        ),
                                        rx.hstack(
                                            rx.icon_button(
                                                rx.icon("message-square", size=14),
                                                size="2",
                                                variant="ghost",
                                                color_scheme="orange",
                                                on_click=TaskState.open_comments_dialog(task["id"]),
                                                title="Comments",
                                            ),
                                            rx.cond(
                                                task["comment_count"] > 0,
                                                rx.badge(
                                                    task["comment_count"].to_string(),
                                                    color_scheme="orange",
                                                    variant="solid",
                                                    size="1",
                                                ),
                                                rx.box(),
                                            ),
                                            spacing="1",
                                            align="center",
                                        ),
                                        rx.hstack(
                                            rx.icon_button(
                                                rx.icon("folder-open", size=14),
                                                size="2",
                                                variant="ghost",
                                                color_scheme="green",
                                                on_click=TaskState.open_submissions_dialog(task["id"]),
                                                title="View Submissions",
                                            ),
                                            rx.cond(
                                                task["submission_count"] > 0,
                                                rx.badge(
                                                    task["submission_count"].to_string(),
                                                    color_scheme="green",
                                                    variant="solid",
                                                    size="1",
                                                ),
                                                rx.box(),
                                            ),
                                            spacing="1",
                                            align="center",
                                        ),
                                        spacing="2",
                                        align="center",
                                    ),
                                    padding="0.4rem 0.55rem",
                                    border_radius="12px",
                                    background_color="rgba(15, 23, 42, 0.04)",
                                    border="1px solid rgba(15, 23, 42, 0.07)",
                                    width="100%",
                                ),
                                margin_top="0.35rem",
                            ),
                            rx.hstack(
                                rx.button(
                                    "Done",
                                    size="2",
                                    color_scheme="green",
                                    variant="outline",
                                    on_click=TaskState.mark_done(task["id"]),
                                    is_disabled=task["status"] == "done",
                                ),
                                rx.button(
                                    "Reassign",
                                    size="2",
                                    color_scheme="orange",
                                    variant="outline",
                                    on_click=TaskState.open_reassign_dialog(task["id"]),
                                ),
                                rx.button(
                                    "Attach",
                                    size="2",
                                    color_scheme="orange",
                                    variant="outline",
                                    on_click=TaskState.open_attach_dialog(task["id"]),
                                ),
                                spacing="3",
                                margin_top="0.65rem",
                                flex_wrap="wrap",
                                align="center",
                            ),
                            spacing="2",
                            align="start",
                        )
                    ),
                ),
            )
        ),
        width="100%",
        class_name="ceo-task-table",
    )


# ── Edit task dialog ────────────────────────────────────────────────────────

def _edit_task_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.text("Edit Task", font_size="1.2rem", font_weight="900", color="#1A1A1A"),
                rx.input(placeholder="Title", value=TaskState.edit_title,
                         on_change=TaskState.set_edit_title, width="100%"),
                rx.text_area(placeholder="Description", value=TaskState.edit_description,
                             on_change=TaskState.set_edit_description, width="100%", min_height="80px"),
                rx.select.root(
                    rx.select.trigger(placeholder="Select Employee"),
                    rx.select.content(rx.foreach(TaskState.employee_users,
                                                 lambda u: rx.select.item(u["name"], value=u["id"]))),
                    value=TaskState.edit_assigned_to, on_change=TaskState.set_edit_assigned_to, width="100%",
                ),
                rx.input(type="date", value=TaskState.edit_deadline,
                         on_change=TaskState.set_edit_deadline, width="100%"),
                rx.cond(
                    TaskState.edit_attachments.length() > 0,
                    rx.vstack(
                        rx.text("Current Attachments", color="#6B7280", font_size="0.85rem", font_weight="700"),
                        rx.foreach(
                            TaskState.edit_attachments,
                            lambda a: rx.hstack(
                                rx.icon("paperclip", size=13, color="#F97316"),
                                rx.text(a["file_name"], color="#1A1A1A", font_size="0.82rem"),
                                rx.spacer(),
                                rx.icon_button(rx.icon("trash-2", size=13), size="1", variant="ghost",
                                               color_scheme="red",
                                               on_click=TaskState.delete_attachment_from_edit(a["id"]),
                                               title="Delete attachment"),
                                width="100%", align="center", padding_x="0.5rem", padding_y="0.25rem",
                                border="1px solid rgba(251,146,60,0.2)", border_radius="6px",
                            ),
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.box(),
                ),
                rx.text("Add Attachments", color="#6B7280", font_size="0.85rem", font_weight="700"),
                rx.upload(
                    rx.vstack(rx.icon("upload", color="#6B7280", size=22),
                              rx.text("Drag & drop or click", color="#6B7280", font_size="0.85rem"),
                              spacing="2", align="center", padding="0.75rem"),
                    id="edit_upload", multiple=True,
                    border="2px dashed rgba(251,146,60,0.35)", border_radius="10px", width="100%",
                ),
                rx.hstack(
                    rx.button("Cancel", variant="outline", on_click=TaskState.close_edit_dialog),
                    rx.button("Upload Files", variant="outline", color_scheme="orange",
                              on_click=TaskState.upload_edit_attachments(rx.upload_files(upload_id="edit_upload"))),
                    rx.button("Save Changes", color_scheme="orange", on_click=TaskState.save_edit_task),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="3", padding="1.5rem", background_color="#FFFFFF",
                border_radius="12px", width="100%",
            ),
            max_width="520px",
        ),
        open=TaskState.show_edit_dialog, on_open_change=TaskState.set_edit_dialog_open,
    )


# ── Comments dialog ─────────────────────────────────────────────────────────

def _comments_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("message-square", size=20, color="#F97316"),
                    rx.text("Comments", font_size="1.2rem", font_weight="900", color="#1A1A1A"),
                    rx.spacer(),
                    rx.text(TaskState.comments_task_title, color="#6B7280", font_size="0.85rem",
                            max_width="200px", overflow="hidden", text_overflow="ellipsis",
                            white_space="nowrap"),
                    width="100%", align="center",
                ),
                rx.divider(border_color="rgba(251,146,60,0.25)"),
                rx.box(
                    rx.cond(
                        TaskState.comments_loading,
                        rx.center(rx.spinner(), padding="2rem"),
                        rx.cond(
                            TaskState.comments.length() > 0,
                            rx.vstack(
                                rx.foreach(
                                    TaskState.comments,
                                    lambda c: rx.box(
                                        rx.hstack(
                                            rx.box(
                                                rx.text(c["author_name"][:1].to_string(),
                                                        color="white", font_weight="700", font_size="0.75rem"),
                                                width="28px", height="28px", border_radius="50%",
                                                background_color="#F97316",
                                                display="flex", align_items="center", justify_content="center",
                                                flex_shrink="0",
                                            ),
                                            rx.vstack(
                                                rx.hstack(
                                                    rx.text(c["author_name"], font_weight="700",
                                                            color="#1A1A1A", font_size="0.85rem"),
                                                    rx.text(c["created_at"].to_string(),
                                                            color="#9CA3AF", font_size="0.72rem"),
                                                    spacing="2", align="center",
                                                ),
                                                rx.text(c["body"], color="#374151", font_size="0.88rem",
                                                        white_space="pre-wrap"),
                                                spacing="1", align="start", width="100%",
                                            ),
                                            spacing="3", align="start", width="100%",
                                        ),
                                        padding="0.6rem", border_radius="8px",
                                        background_color="#FFF8F3",
                                        width="100%",
                                    ),
                                ),
                                spacing="2", width="100%",
                            ),
                            rx.center(
                                rx.vstack(
                                    rx.icon("message-square", size=32, color="#D1D5DB"),
                                    rx.text("No comments yet", color="#9CA3AF", font_size="0.9rem"),
                                    spacing="2", align="center",
                                ),
                                padding="2rem",
                            ),
                        ),
                    ),
                    max_height="40vh", overflow_y="auto", width="100%",
                    padding="0.25rem",
                ),
                rx.divider(border_color="rgba(251,146,60,0.25)"),
                rx.hstack(
                    rx.text_area(
                        placeholder="Write a comment...",
                        value=TaskState.new_comment_body,
                        on_change=TaskState.set_new_comment_body,
                        width="100%", min_height="60px", max_height="100px",
                    ),
                    rx.button(
                        rx.icon("send", size=16),
                        color_scheme="orange", size="2",
                        on_click=TaskState.post_comment,
                    ),
                    spacing="2", width="100%", align="end",
                ),
                spacing="3", padding="1.5rem", background_color="#FFFFFF",
                border_radius="12px", width="100%",
            ),
            max_width="600px",
        ),
        open=TaskState.show_comments_dialog, on_open_change=TaskState.set_comments_dialog_open,
    )


# ── Preview dialog ──────────────────────────────────────────────────────────

def _preview_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("eye", size=18, color="#F97316"),
                    rx.text("Preview", font_size="1.1rem", font_weight="900", color="#1A1A1A"),
                    rx.spacer(),
                    rx.text(TaskState.preview_file_name, color="#6B7280", font_size="0.85rem"),
                    width="100%", align="center",
                ),
                rx.divider(border_color="rgba(251,146,60,0.25)"),
                rx.box(
                    rx.cond(
                        TaskState.preview_is_image,
                        rx.el.img(
                            id="taskme-preview-img",
                            src="",
                            alt=TaskState.preview_file_name,
                            style={"max_width": "100%", "max_height": "60vh", "border_radius": "8px",
                                   "object_fit": "contain"},
                        ),
                        rx.cond(
                            TaskState.preview_is_pdf,
                            rx.el.iframe(
                                id="taskme-preview-frame",
                                src="",
                                width="100%",
                                height="500px",
                                style={"border": "none", "border_radius": "8px"},
                            ),
                            rx.center(
                                rx.vstack(
                                    rx.icon("file", size=48, color="#D1D5DB"),
                                    rx.text("Preview not available for this file type.",
                                            color="#6B7280", font_size="0.9rem"),
                                    rx.text("Click download to view the file.",
                                            color="#9CA3AF", font_size="0.82rem"),
                                    spacing="2", align="center",
                                ),
                                padding="3rem",
                            ),
                        ),
                    ),
                    width="100%", min_height="200px",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.hstack(
                    rx.button("Close", variant="outline", on_click=TaskState.close_preview),
                    justify="end", width="100%",
                ),
                spacing="3", padding="1.5rem", background_color="#FFFFFF",
                border_radius="12px", width="100%",
            ),
            max_width="720px",
        ),
        open=TaskState.show_preview_dialog, on_open_change=TaskState.set_preview_dialog_open,
    )


# ── Submissions dialog (CEO views employee work files) ──────────────────────

def _submissions_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("folder-open", size=20, color="#22C55E"),
                    rx.text("Employee Submissions", font_size="1.2rem", font_weight="900", color="#1A1A1A"),
                    rx.spacer(),
                    rx.text(TaskState.submissions_task_title, color="#6B7280", font_size="0.85rem",
                            max_width="200px", overflow="hidden", text_overflow="ellipsis",
                            white_space="nowrap"),
                    width="100%", align="center",
                ),
                rx.divider(border_color="rgba(34,197,94,0.25)"),
                rx.cond(
                    TaskState.submissions_loading,
                    rx.center(rx.spinner(), padding="2rem"),
                    rx.cond(
                        TaskState.submissions.length() > 0,
                        rx.vstack(
                            rx.foreach(
                                TaskState.submissions,
                                lambda s: rx.hstack(
                                    rx.icon("file-check", size=16, color="#22C55E"),
                                    rx.vstack(
                                        rx.text(s["file_name"], font_weight="600", color="#1A1A1A",
                                                font_size="0.88rem"),
                                        rx.hstack(
                                            rx.text(s["uploader_name"], color="#F97316", font_size="0.75rem",
                                                    font_weight="600"),
                                            rx.text(s["uploaded_at"].to_string(), color="#9CA3AF",
                                                    font_size="0.72rem"),
                                            spacing="2",
                                        ),
                                        spacing="0",
                                    ),
                                    rx.spacer(),
                                    rx.icon_button(
                                        rx.icon("eye", size=13), size="1", variant="ghost",
                                        color_scheme="green",
                                        on_click=TaskState.open_submission_preview(
                                            TaskState.submissions_task_id, s["id"], s["file_name"]),
                                        title="Preview",
                                    ),
                                    rx.icon_button(
                                        rx.icon("download", size=13), size="1", variant="ghost",
                                        color_scheme="green",
                                        on_click=TaskState.download_submission(
                                            TaskState.submissions_task_id, s["id"], s["file_name"]),
                                        title="Download",
                                    ),
                                    width="100%", align="center", padding="0.6rem",
                                    border="1px solid rgba(34,197,94,0.2)", border_radius="8px",
                                    background_color="rgba(34,197,94,0.04)",
                                ),
                            ),
                            spacing="2", width="100%",
                        ),
                        rx.center(
                            rx.vstack(
                                rx.icon("inbox", size=36, color="#D1D5DB"),
                                rx.text("No submissions yet", color="#9CA3AF", font_size="0.9rem"),
                                rx.text("Employee has not uploaded any work files for this task.",
                                        color="#D1D5DB", font_size="0.82rem"),
                                spacing="2", align="center",
                            ),
                            padding="2rem",
                        ),
                    ),
                ),
                rx.hstack(
                    rx.button("Close", variant="outline",
                              on_click=lambda: TaskState.set_submissions_dialog_open(False)),
                    justify="end", width="100%",
                ),
                spacing="3", padding="1.5rem", background_color="#FFFFFF",
                border_radius="12px", width="100%",
            ),
            max_width="600px",
        ),
        open=TaskState.show_submissions_dialog,
        on_open_change=TaskState.set_submissions_dialog_open,
    )


# ── Report dialog ───────────────────────────────────────────────────────────

def _report_dialog() -> rx.Component:
    d = TaskState.selected_report_data
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text("EOD Report", font_size="1.3rem", font_weight="900", color="#1A1A1A"),
                        rx.text(d["report_date"].to_string(), color="#6B7280", font_size="0.9rem"),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    rx.text(rx.Var.create("Generated: ") + d["generated_at"].to_string(),
                            color="#6B7280", font_size="0.8rem"),
                    width="100%", align="center",
                ),
                rx.divider(border_color="rgba(251,146,60,0.3)"),
                rx.grid(
                    rx.box(rx.vstack(rx.text("Total", color="#6B7280", font_size="0.82rem"),
                                     rx.text(d["total_tasks"].to_string(), color="#1A1A1A",
                                             font_size="1.5rem", font_weight="900"),
                                     spacing="0", align="start"),
                           padding="0.6rem", border="1px solid rgba(251,146,60,0.3)",
                           border_radius="10px", background_color="#FFF8F3"),
                    rx.box(rx.vstack(rx.text("Pending", color="#6B7280", font_size="0.82rem"),
                                     rx.text(d["pending"].to_string(), color="#F97316",
                                             font_size="1.5rem", font_weight="900"),
                                     spacing="0", align="start"),
                           padding="0.6rem", border="1px solid rgba(251,146,60,0.3)",
                           border_radius="10px", background_color="#FFF8F3"),
                    rx.box(rx.vstack(rx.text("In Progress", color="#6B7280", font_size="0.82rem"),
                                     rx.text(d["in_progress"].to_string(), color="#F59E0B",
                                             font_size="1.5rem", font_weight="900"),
                                     spacing="0", align="start"),
                           padding="0.6rem", border="1px solid rgba(251,146,60,0.3)",
                           border_radius="10px", background_color="#FFF8F3"),
                    rx.box(rx.vstack(rx.text("Done", color="#6B7280", font_size="0.82rem"),
                                     rx.text(d["done"].to_string(), color="#22C55E",
                                             font_size="1.5rem", font_weight="900"),
                                     spacing="0", align="start"),
                           padding="0.6rem", border="1px solid rgba(34,197,94,0.3)",
                           border_radius="10px", background_color="#F0FDF4"),
                    rx.box(rx.vstack(rx.text("Overdue", color="#6B7280", font_size="0.82rem"),
                                     rx.text(d["overdue"].to_string(), color="#EF4444",
                                             font_size="1.5rem", font_weight="900"),
                                     spacing="0", align="start"),
                           padding="0.6rem", border="1px solid rgba(239,68,68,0.3)",
                           border_radius="10px", background_color="#FEF2F2"),
                    columns="5", spacing="2", width="100%",
                ),
                rx.box(
                    rx.text("Task Details", font_weight="700", color="#1A1A1A",
                            font_size="0.95rem", margin_bottom="0.5rem"),
                    rx.cond(
                        TaskState.report_tasks.length() > 0,
                        rx.table.root(
                            rx.table.header(
                                rx.table.row(
                                    rx.table.column_header_cell("Task", style={"font_size": "0.8rem"}),
                                    rx.table.column_header_cell("Assigned To", style={"font_size": "0.8rem"}),
                                    rx.table.column_header_cell("Status", style={"font_size": "0.8rem"}),
                                    rx.table.column_header_cell("Progress", style={"font_size": "0.8rem"}),
                                    rx.table.column_header_cell("Deadline", style={"font_size": "0.8rem"}),
                                    rx.table.column_header_cell("Submissions", style={"font_size": "0.8rem"}),
                                ),
                            ),
                            rx.table.body(
                                rx.foreach(
                                    TaskState.report_tasks,
                                    lambda t: rx.table.row(
                                        rx.table.cell(rx.text(t["title"], font_weight="600", font_size="0.82rem", color="#1A1A1A")),
                                        rx.table.cell(rx.text(t["assigned_to_name"], font_size="0.82rem", color="#374151")),
                                        rx.table.cell(status_badge(t["status"])),
                                        rx.table.cell(
                                            rx.hstack(
                                                rx.text(t["progress"].to_string() + "%", font_size="0.82rem", color="#1A1A1A", font_weight="600"),
                                                progress_bar(t["progress"]),
                                                spacing="2", align="center", width="100%",
                                            ),
                                        ),
                                        rx.table.cell(rx.text(t["deadline"].to_string(), font_size="0.82rem", color="#6B7280")),
                                        rx.table.cell(
                                            rx.cond(
                                                t["submissions"].length() > 0,
                                                rx.vstack(
                                                    rx.foreach(
                                                        t["submissions"],
                                                        lambda s: rx.button(
                                                            rx.hstack(
                                                                rx.icon("download", size=11, color="#22C55E"),
                                                                rx.text(s["file_name"], font_size="0.72rem", color="#22C55E"),
                                                                spacing="1", align="center",
                                                            ),
                                                            variant="ghost", size="1",
                                                            background_color="rgba(34,197,94,0.08)",
                                                            border="1px solid rgba(34,197,94,0.25)",
                                                            border_radius="5px",
                                                            padding_x="0.3rem", padding_y="0.1rem",
                                                            on_click=TaskState.download_submission(s["task_id"], s["id"], s["file_name"]),
                                                            cursor="pointer",
                                                        ),
                                                    ),
                                                    spacing="1", align="start",
                                                ),
                                                rx.text("—", color="#D1D5DB", font_size="0.82rem"),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                            width="100%",
                        ),
                        rx.box(
                            rx.text(TaskState.selected_report_content, white_space="pre-wrap",
                                    font_size="0.82rem", color="#6B7280",
                                    font_family="ui-monospace, monospace"),
                            max_height="30vh", overflow_y="auto", padding="0.75rem",
                            border="1px solid rgba(251,146,60,0.2)", border_radius="8px",
                            background_color="#FFF8F3",
                        ),
                    ),
                    width="100%", max_height="45vh", overflow_y="auto",
                ),
                rx.hstack(rx.button("Close", variant="outline", on_click=TaskState.close_report_dialog),
                           justify="end", width="100%"),
                spacing="3", padding="1.5rem", background_color="#FFFFFF", border_radius="12px",
            ),
            max_width="900px",
        ),
        open=TaskState.show_report_dialog, on_open_change=TaskState.set_report_dialog_open,
    )


# ── EOD reports section ─────────────────────────────────────────────────────

def _eod_reports_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text("EOD Reports", font_size="1.2rem", font_weight="900", color="#1A1A1A"),
                    rx.text("Automated end-of-day summaries and history", font_size="0.85rem", color="#64748B"),
                    spacing="1", align_items="start",
                ),
                rx.spacer(),
                rx.button("Generate Now", color_scheme="orange", variant="solid",
                          on_click=TaskState.generate_report_now),
                width="100%", align="center",
            ),
            rx.box(
                rx.vstack(
                    rx.text("Schedule & automation", font_weight="800", color="#1A1A1A", font_size="0.95rem"),
                    rx.hstack(
                        rx.text("Run at", color="#64748B", font_size="0.85rem", font_weight="600"),
                        rx.input(type="time", value=TaskState.report_schedule_time,
                                 on_change=TaskState.set_report_time, max_width="140px"),
                        spacing="3", align="center", flex_wrap="wrap",
                    ),
                    rx.hstack(
                        rx.text("Timezone", color="#64748B", font_size="0.85rem", font_weight="600"),
                        rx.input(value=TaskState.report_schedule_timezone,
                                 on_change=TaskState.set_report_timezone, width="240px", max_width="100%"),
                        spacing="3", align="center", flex_wrap="wrap",
                    ),
                    rx.hstack(
                        rx.vstack(
                            rx.text("Automated reports", font_weight="700", color="#1A1A1A", font_size="0.88rem"),
                            rx.text("Turn off to pause scheduled generation.", font_size="0.78rem", color="#94A3B8"),
                            spacing="0", align_items="start",
                        ),
                        rx.spacer(),
                        rx.hstack(
                            rx.text("Inactive", font_size="0.8rem", color="#94A3B8"),
                            rx.switch(checked=TaskState.report_schedule_active,
                                      on_change=TaskState.set_report_schedule_active_bool,
                                      color_scheme="orange", size="2"),
                            rx.text("Active", font_size="0.8rem", color="#94A3B8"),
                            spacing="2", align="center",
                        ),
                        width="100%", align="center", padding_y="0.35rem",
                    ),
                    rx.hstack(
                        rx.button("Save schedule", variant="outline", color_scheme="orange",
                                  on_click=TaskState.save_report_schedule),
                        rx.spacer(),
                        rx.text(rx.Var.create("Last generated: ") + TaskState.latest_eod_generated_at_label,
                                font_size="0.82rem", color="#64748B"),
                        width="100%", align="center", flex_wrap="wrap", spacing="3",
                    ),
                    spacing="4", width="100%",
                ),
                width="100%", padding="1.35rem", border_radius="14px",
                background_color="rgba(248, 250, 252, 0.97)",
                border="1px solid rgba(15, 23, 42, 0.07)",
                box_shadow="inset 0 1px 0 rgba(255, 255, 255, 0.85)",
            ),
            rx.divider(border_color="rgba(15, 23, 42, 0.08)"),
            rx.vstack(
                rx.text("Past reports", color="#475569", font_weight="800", font_size="0.9rem"),
                rx.foreach(
                    TaskState.eod_reports,
                    lambda r: rx.box(
                        rx.hstack(
                            rx.vstack(
                                rx.text(r["report_date"].to_string(), color="#1A1A1A", font_weight="700"),
                                rx.text(
                                    rx.Var.create("Total ") + r["total_tasks"].to_string()
                                    + rx.Var.create(" · Done ") + r["done"].to_string(),
                                    color="#64748B", font_size="0.84rem",
                                ),
                                spacing="0", align_items="start",
                            ),
                            rx.spacer(),
                            rx.button("View", size="2", variant="outline", color_scheme="orange",
                                      on_click=TaskState.view_report(r["id"])),
                            width="100%", align="center",
                        ),
                        padding="0.85rem 1rem", border_radius="12px",
                        border="1px solid rgba(15, 23, 42, 0.06)",
                        background_color="#FFFFFF",
                        box_shadow="0 1px 2px rgba(15, 23, 42, 0.04)",
                    ),
                ),
                # Load more reports button
                rx.cond(
                    TaskState.eod_reports_page < TaskState.eod_reports_total_pages,
                    rx.button(
                        "Load More Reports",
                        variant="outline",
                        color_scheme="orange",
                        size="2",
                        on_click=TaskState.load_more_reports,
                        width="100%",
                    ),
                    rx.box(),
                ),
                spacing="3", width="100%",
            ),
            spacing="4", width="100%",
        ),
        margin_top="1rem", padding="1.35rem",
        border="1px solid rgba(15, 23, 42, 0.06)", border_radius="16px",
        background_color="#FFFFFF", width="100%",
        box_shadow="0 4px 24px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04)",
    )


# ── Page ────────────────────────────────────────────────────────────────────

@rx.page(
    route="/dashboard",
    title="Zapp · Dashboard",
    on_load=[TaskState.load_ceo_dashboard, TaskState.load_eod_reports,
             TaskState.load_report_schedule, TaskState.load_analytics,
             TaskState.request_notification_permission],
)
def ceo_dashboard() -> rx.Component:
    return rx.cond(
        ~TaskState.is_hydrated,
        rx.center(rx.spinner(), min_height="100vh", background_color="#ECEEF3"),
        rx.cond(
            ~TaskState.is_ceo,
            rx.center(rx.spinner(), min_height="100vh", background_color="#ECEEF3"),
            rx.box(
                _ceo_table_styles(),
                _ceo_app_header(),
                rx.box(
                    rx.cond(TaskState.toast != "",
                            rx.callout(TaskState.toast, color_scheme="red"), rx.box()),
                    rx.cond(TaskState.is_loading, rx.center(rx.spinner()), _summary_cards()),
                    # Analytics
                    _analytics_section(),
                    # Task table with pagination
                    rx.box(
                        rx.cond(TaskState.is_loading, rx.center(rx.spinner()), _task_table()),
                        _pagination_controls(),
                        margin_top="1rem",
                        padding="1.25rem",
                        border="1px solid rgba(15, 23, 42, 0.06)",
                        border_radius="16px",
                        background_color="#FFFFFF",
                        box_shadow="0 4px 24px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04)",
                    ),
                    _eod_reports_section(),
                    # Dialogs
                    _add_task_dialog(),
                    _attach_dialog(),
                    _reassign_dialog(),
                    _edit_task_dialog(),
                    _comments_dialog(),
                    _preview_dialog(),
                    _submissions_dialog(),
                    _report_dialog(),
                    # Lightweight poll instead of full reload every 30s
                    rx.moment(interval=30_000, on_change=TaskState.poll_summary, display="none"),
                    rx.moment(interval=15_000, on_change=TaskState.poll_notifications, display="none"),
                    padding="1.5rem", max_width="1200px", margin_x="auto",
                ),
                background_color="#ECEEF3", min_height="100vh",
            ),
        ),
    )
