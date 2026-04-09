from __future__ import annotations

import reflex as rx

from taskme.components.navbar import navbar
from taskme.components.progress_bar import progress_bar
from taskme.components.status_badge import status_badge
from taskme.state.task_state import TaskState


# ── Summary cards ───────────────────────────────────────────────────────────

def _summary_cards() -> rx.Component:
    def card(label: str, value, color: str = "#1A1A1A") -> rx.Component:
        return rx.box(
            rx.vstack(
                rx.text(label, color="#6B7280", font_size="0.9rem"),
                rx.text(value.to_string(), color=color, font_size="1.8rem", font_weight="900"),
                spacing="1", align="start",
            ),
            padding="1rem", border="1px solid rgba(251,146,60,0.3)",
            border_radius="14px", background_color="#FFFFFF", width="100%",
        )

    return rx.grid(
        card("Total Tasks", TaskState.total_tasks),
        card("Pending", TaskState.pending_tasks, "#F97316"),
        card("In Progress", TaskState.in_progress_tasks, "#F59E0B"),
        card("Done", TaskState.done_tasks, "#22C55E"),
        columns="4", spacing="4", width="100%",
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
                    padding="0.75rem", border="1px solid rgba(251,146,60,0.3)",
                    border_radius="12px", background_color="#FFF8F3",
                ),
                rx.box(
                    rx.vstack(
                        rx.text("Overdue Tasks", color="#6B7280", font_size="0.82rem"),
                        rx.text(TaskState.analytics_overdue_count.to_string(), color="#EF4444",
                                font_size="1.6rem", font_weight="900"),
                        spacing="0", align="start",
                    ),
                    padding="0.75rem", border="1px solid rgba(239,68,68,0.3)",
                    border_radius="12px", background_color="#FEF2F2",
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
                                padding="0.4rem 0.6rem",
                                border="1px solid rgba(239,68,68,0.2)", border_radius="8px",
                                background_color="#FEF2F2",
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
        margin_top="1rem", padding="1rem",
        border="1px solid rgba(251,146,60,0.3)", border_radius="14px",
        background_color="#FFFFFF", width="100%",
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
                    rx.button("Create Task", color_scheme="orange",
                              on_click=TaskState.create_task_with_files(
                                  rx.upload_files(upload_id="add_task_upload"))),
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
                    rx.button("Upload", color_scheme="orange",
                              on_click=TaskState.upload_attachment(rx.upload_files(upload_id="attach_upload"))),
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
                    rx.button("Reassign", color_scheme="orange", on_click=TaskState.reassign_task),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="3", padding="1.5rem",
            )
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


# ── Task table ──────────────────────────────────────────────────────────────

def _task_table() -> rx.Component:
    return rx.table.root(
        rx.table.header(
            rx.table.row(
                rx.table.column_header_cell("Task"),
                rx.table.column_header_cell("Assigned To"),
                rx.table.column_header_cell("Status"),
                rx.table.column_header_cell("Progress"),
                rx.table.column_header_cell(
                    rx.hstack(rx.text("Deadline"),
                              rx.button("Sort", size="1", variant="ghost",
                                        on_click=TaskState.toggle_sort_deadline), spacing="2")),
                rx.table.column_header_cell("Files / Action"),
            )
        ),
        rx.table.body(
            rx.foreach(
                TaskState.filtered_sorted_tasks,
                lambda task: rx.table.row(
                    rx.table.cell(
                        rx.vstack(
                            rx.text(task["title"], color="#1A1A1A", font_weight="700"),
                            rx.text(task["description"], color="#6B7280", font_size="0.82rem",
                                    max_width="200px", overflow="hidden",
                                    text_overflow="ellipsis", white_space="nowrap"),
                            spacing="1",
                        )
                    ),
                    rx.table.cell(rx.text(task["assigned_to_name"], color="#1A1A1A")),
                    rx.table.cell(status_badge(task["status"])),
                    rx.table.cell(
                        rx.vstack(
                            rx.text(task["progress"].to_string() + "%", color="#1A1A1A"),
                            progress_bar(task["progress"]), spacing="2",
                        )
                    ),
                    rx.table.cell(rx.text(task["deadline"].to_string(), color="#6B7280")),
                    rx.table.cell(
                        rx.vstack(
                            _attachment_chips(task),
                            rx.hstack(
                                rx.icon_button(
                                    rx.icon("pencil", size=14), size="2", variant="ghost",
                                    color_scheme="orange", on_click=TaskState.open_edit_dialog(task["id"]),
                                    title="Edit task",
                                ),
                                rx.icon_button(
                                    rx.icon("message-square", size=14), size="2", variant="ghost",
                                    color_scheme="orange",
                                    on_click=TaskState.open_comments_dialog(task["id"]),
                                    title="Comments",
                                ),
                                rx.cond(
                                    task["comment_count"] > 0,
                                    rx.badge(task["comment_count"].to_string(), color_scheme="orange",
                                             variant="solid", size="1"),
                                    rx.box(),
                                ),
                                rx.button("Done", size="2", color_scheme="green", variant="outline",
                                          on_click=TaskState.mark_done(task["id"]),
                                          is_disabled=task["status"] == "done"),
                                rx.button("Reassign", size="2", color_scheme="orange", variant="outline",
                                          on_click=TaskState.open_reassign_dialog(task["id"])),
                                rx.button("Attach", size="2", variant="outline",
                                          on_click=TaskState.open_attach_dialog(task["id"])),
                                spacing="2",
                            ),
                            spacing="2", align="start",
                        )
                    ),
                ),
            )
        ),
        width="100%",
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
                # Comment thread
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
                # New comment input
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
                    rx.box(rx.vstack(rx.text("Total", color="#6B7280", font_size="0.85rem"),
                                     rx.text(d["total_tasks"].to_string(), color="#1A1A1A",
                                             font_size="1.6rem", font_weight="900"),
                                     spacing="0", align="start"),
                           padding="0.75rem", border="1px solid rgba(251,146,60,0.3)",
                           border_radius="12px", background_color="#FFF8F3"),
                    rx.box(rx.vstack(rx.text("Pending", color="#6B7280", font_size="0.85rem"),
                                     rx.text(d["pending"].to_string(), color="#F97316",
                                             font_size="1.6rem", font_weight="900"),
                                     spacing="0", align="start"),
                           padding="0.75rem", border="1px solid rgba(251,146,60,0.3)",
                           border_radius="12px", background_color="#FFF8F3"),
                    rx.box(rx.vstack(rx.text("In Progress", color="#6B7280", font_size="0.85rem"),
                                     rx.text(d["in_progress"].to_string(), color="#F97316",
                                             font_size="1.6rem", font_weight="900"),
                                     spacing="0", align="start"),
                           padding="0.75rem", border="1px solid rgba(251,146,60,0.3)",
                           border_radius="12px", background_color="#FFF8F3"),
                    rx.box(rx.vstack(rx.text("Done", color="#6B7280", font_size="0.85rem"),
                                     rx.text(d["done"].to_string(), color="#22C55E",
                                             font_size="1.6rem", font_weight="900"),
                                     spacing="0", align="start"),
                           padding="0.75rem", border="1px solid rgba(251,146,60,0.3)",
                           border_radius="12px", background_color="#FFF8F3"),
                    columns="4", spacing="3", width="100%",
                ),
                rx.box(
                    rx.text("Task Details", font_weight="700", color="#1A1A1A",
                            font_size="0.95rem", margin_bottom="0.5rem"),
                    rx.box(rx.text(TaskState.selected_report_content, white_space="pre-wrap",
                                   font_size="0.82rem", color="#6B7280",
                                   font_family="ui-monospace, monospace"),
                           max_height="30vh", overflow_y="auto", padding="0.75rem",
                           border="1px solid rgba(251,146,60,0.2)", border_radius="8px",
                           background_color="#FFF8F3"),
                    width="100%",
                ),
                rx.hstack(rx.button("Close", variant="outline", on_click=TaskState.close_report_dialog),
                           justify="end", width="100%"),
                spacing="3", padding="1.5rem", background_color="#FFFFFF", border_radius="12px",
            )
        ),
        open=TaskState.show_report_dialog, on_open_change=TaskState.set_report_dialog_open,
    )


# ── EOD reports section ─────────────────────────────────────────────────────

def _eod_reports_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("EOD Reports", font_size="1.2rem", font_weight="900", color="#1A1A1A"),
                rx.spacer(),
                rx.button("Generate Now", color_scheme="orange", on_click=TaskState.generate_report_now),
                spacing="3", width="100%", align="center",
            ),
            rx.hstack(
                rx.hstack(rx.text("Schedule:", color="#6B7280", font_weight="700"),
                           rx.input(type="time", value=TaskState.report_schedule_time,
                                    on_change=TaskState.set_report_time),
                           spacing="2", align="center"),
                rx.hstack(rx.text("Timezone:", color="#6B7280", font_weight="700"),
                           rx.input(value=TaskState.report_schedule_timezone,
                                    on_change=TaskState.set_report_timezone, width="220px"),
                           spacing="2", align="center"),
                rx.hstack(rx.text("Status:", color="#6B7280", font_weight="700"),
                           rx.select(["active", "inactive"],
                                     value=rx.cond(TaskState.report_schedule_active, "active", "inactive"),
                                     on_change=TaskState.set_report_active, width="150px"),
                           spacing="2", align="center"),
                rx.button("Save", variant="outline", on_click=TaskState.save_report_schedule),
                spacing="3", width="100%", flex_wrap="wrap",
            ),
            rx.divider(border_color="rgba(251,146,60,0.25)"),
            rx.vstack(
                rx.text("Past Reports", color="#6B7280", font_weight="800", font_size="0.95rem"),
                rx.foreach(
                    TaskState.eod_reports,
                    lambda r: rx.hstack(
                        rx.text(r["report_date"].to_string(), color="#1A1A1A", font_weight="700"),
                        rx.text(rx.Var.create("Total: ") + r["total_tasks"].to_string()
                                + rx.Var.create("  Done: ") + r["done"].to_string(),
                                color="#6B7280", font_size="0.9rem"),
                        rx.spacer(),
                        rx.button("View", size="2", variant="outline",
                                  on_click=TaskState.view_report(r["id"])),
                        width="100%", align="center",
                    ),
                ),
                spacing="2", width="100%",
            ),
            spacing="3", width="100%",
        ),
        margin_top="1rem", padding="1rem", border="1px solid rgba(251,146,60,0.3)",
        border_radius="14px", background_color="#FFFFFF", width="100%",
    )


# ── Page ────────────────────────────────────────────────────────────────────

@rx.page(
    route="/dashboard",
    title="Taskme · Dashboard",
    on_load=[TaskState.load_ceo_dashboard, TaskState.load_eod_reports,
             TaskState.load_report_schedule, TaskState.load_analytics],
)
def ceo_dashboard() -> rx.Component:
    return rx.cond(
        ~TaskState.is_hydrated,
        rx.center(rx.spinner(), min_height="100vh", background_color="#FFF8F3"),
        rx.cond(
            ~TaskState.is_ceo,
            rx.center(rx.spinner(), min_height="100vh", background_color="#FFF8F3"),
            rx.box(
                navbar(),
                rx.box(
                    rx.hstack(
                        rx.text("CEO Dashboard", font_size="1.4rem", font_weight="900", color="#1A1A1A"),
                        rx.spacer(),
                        rx.select(["all", "pending", "in_progress", "done"],
                                  value=TaskState.status_filter,
                                  on_change=TaskState.set_status_filter, width="220px"),
                        rx.button("Add Task", color_scheme="orange",
                                  on_click=TaskState.open_add_dialog),
                        spacing="3", width="100%", align="center",
                    ),
                    rx.cond(TaskState.toast != "",
                            rx.callout(TaskState.toast, color_scheme="red"), rx.box()),
                    rx.cond(TaskState.is_loading, rx.center(rx.spinner()), _summary_cards()),
                    # Analytics
                    _analytics_section(),
                    # Task table
                    rx.box(
                        rx.cond(TaskState.is_loading, rx.center(rx.spinner()), _task_table()),
                        margin_top="1rem", padding="1rem",
                        border="1px solid rgba(251,146,60,0.3)",
                        border_radius="14px", background_color="#FFFFFF",
                    ),
                    _eod_reports_section(),
                    # Dialogs
                    _add_task_dialog(),
                    _attach_dialog(),
                    _reassign_dialog(),
                    _edit_task_dialog(),
                    _comments_dialog(),
                    _preview_dialog(),
                    _report_dialog(),
                    rx.moment(interval=30_000, on_change=TaskState.load_ceo_dashboard, display="none"),
                    padding="1.5rem", max_width="1200px", margin_x="auto",
                ),
                background_color="#FFF8F3", min_height="100vh",
            ),
        ),
    )
