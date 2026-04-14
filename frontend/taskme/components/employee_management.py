"""Employee management section and dialogs for the CEO dashboard.

This module adds the ability for the CEO to:
- View all team members in a table
- Add new employees via a dialog
- Delete employees via a confirmation dialog

No existing logic is changed — this is a purely additive component.
"""
from __future__ import annotations

import reflex as rx

from taskme.state.task_state import TaskState


def _add_employee_dialog() -> rx.Component:
    """Dialog for creating a new employee."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("user-plus", size=22, color="#F97316"),
                    rx.text("Add Employee", font_size="1.2rem", font_weight="900", color="#1A1A1A"),
                    spacing="2",
                    align="center",
                ),
                rx.divider(border_color="rgba(251,146,60,0.25)"),
                rx.vstack(
                    rx.text("Full Name", color="#6B7280", font_size="0.85rem", font_weight="600"),
                    rx.input(
                        placeholder="e.g. John Doe",
                        value=TaskState.new_emp_name,
                        on_change=TaskState.set_new_emp_name,
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Username", color="#6B7280", font_size="0.85rem", font_weight="600"),
                    rx.input(
                        placeholder="e.g. johndoe",
                        value=TaskState.new_emp_username,
                        on_change=TaskState.set_new_emp_username,
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Password", color="#6B7280", font_size="0.85rem", font_weight="600"),
                    rx.input(
                        placeholder="Min 3 characters",
                        type="password",
                        value=TaskState.new_emp_password,
                        on_change=TaskState.set_new_emp_password,
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Role", color="#6B7280", font_size="0.85rem", font_weight="600"),
                    rx.select.root(
                        rx.select.trigger(placeholder="Select Role"),
                        rx.select.content(
                            rx.select.item("Employee", value="employee"),
                            rx.select.item("CEO", value="ceo"),
                        ),
                        value=TaskState.new_emp_role,
                        on_change=TaskState.set_new_emp_role,
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.cond(
                    TaskState.employee_mgmt_toast != "",
                    rx.callout(
                        TaskState.employee_mgmt_toast,
                        color_scheme="red",
                        width="100%",
                    ),
                    rx.box(),
                ),
                rx.hstack(
                    rx.button(
                        "Cancel",
                        variant="outline",
                        on_click=TaskState.close_add_employee_dialog,
                    ),
                    rx.button(
                        rx.cond(
                            TaskState.employee_mgmt_loading,
                            rx.spinner(size="2"),
                            rx.text("Create Employee"),
                        ),
                        color_scheme="orange",
                        variant="solid",
                        on_click=TaskState.create_employee,
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="3",
                padding="1.5rem",
                background_color="#FFFFFF",
                border_radius="12px",
                width="100%",
            ),
            max_width="480px",
        ),
        open=TaskState.show_employee_mgmt_dialog,
        on_open_change=TaskState.set_add_employee_dialog_open,
    )


def _delete_employee_dialog() -> rx.Component:
    """Confirmation dialog for deleting an employee."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("triangle-alert", size=22, color="#EF4444"),
                    rx.text("Delete Employee", font_size="1.2rem", font_weight="900", color="#1A1A1A"),
                    spacing="2",
                    align="center",
                ),
                rx.divider(border_color="rgba(239,68,68,0.25)"),
                rx.text(
                    rx.Var.create("Are you sure you want to delete ") + TaskState.delete_employee_name + "?",
                    color="#374151",
                    font_size="0.95rem",
                    line_height="1.5",
                ),
                rx.text(
                    "This action cannot be undone. Any tasks assigned to this employee will lose their assignee reference.",
                    color="#6B7280",
                    font_size="0.85rem",
                    line_height="1.5",
                ),
                rx.hstack(
                    rx.button(
                        "Cancel",
                        variant="outline",
                        on_click=TaskState.close_delete_employee_dialog,
                    ),
                    rx.button(
                        rx.cond(
                            TaskState.employee_mgmt_loading,
                            rx.spinner(size="2"),
                            rx.text("Delete"),
                        ),
                        color_scheme="red",
                        variant="solid",
                        on_click=TaskState.delete_employee,
                    ),
                    spacing="3",
                    justify="end",
                    width="100%",
                ),
                spacing="3",
                padding="1.5rem",
                background_color="#FFFFFF",
                border_radius="12px",
                width="100%",
            ),
            max_width="440px",
        ),
        open=TaskState.show_delete_employee_dialog,
        on_open_change=TaskState.set_delete_employee_dialog_open,
    )


def _employee_row(user: rx.Var) -> rx.Component:
    """A single row in the employee table."""
    return rx.table.row(
        rx.table.cell(
            rx.hstack(
                rx.box(
                    rx.text(
                        user["name"][:1].to_string(),
                        color="white",
                        font_weight="700",
                        font_size="0.75rem",
                        text_transform="uppercase",
                    ),
                    width="32px",
                    height="32px",
                    border_radius="50%",
                    background_color=rx.cond(
                        user["role"] == "ceo",
                        "#1A2B56",
                        "#F97316",
                    ),
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    flex_shrink="0",
                ),
                rx.text(
                    user["name"],
                    font_weight="700",
                    color="#1A1A1A",
                    font_size="0.9rem",
                ),
                spacing="3",
                align="center",
            ),
        ),
        rx.table.cell(
            rx.text(user["username"], color="#374151", font_size="0.88rem"),
        ),
        rx.table.cell(
            rx.badge(
                rx.cond(user["role"] == "ceo", "CEO", "Employee"),
                color_scheme=rx.cond(user["role"] == "ceo", "blue", "orange"),
                variant="solid",
                padding_x="0.55rem",
                padding_y="0.2rem",
                font_size="0.72rem",
                font_weight="600",
                border_radius="999px",
            ),
        ),
        rx.table.cell(
            rx.cond(
                user["role"] != "ceo",
                rx.icon_button(
                    rx.icon("trash-2", size=14),
                    size="2",
                    variant="ghost",
                    color_scheme="red",
                    on_click=TaskState.open_delete_employee_dialog(user["id"]),
                    title="Delete employee",
                ),
                rx.box(),
            ),
        ),
    )


def employee_management_section() -> rx.Component:
    """Team management section with employee table, add/delete capabilities."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon("users", size=20, color="#F97316"),
                    rx.text(
                        "Team Management",
                        font_size="1.2rem",
                        font_weight="900",
                        color="#1A1A1A",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.button(
                    rx.hstack(
                        rx.icon("user-plus", size=14),
                        rx.text("Add Employee", font_size="0.85rem"),
                        spacing="2",
                        align="center",
                    ),
                    color_scheme="orange",
                    variant="solid",
                    size="2",
                    on_click=TaskState.open_add_employee_dialog,
                ),
                width="100%",
                align="center",
            ),
            rx.text(
                "Manage your team members. Add new employees or remove existing ones.",
                color="#64748B",
                font_size="0.88rem",
            ),
            rx.cond(
                TaskState.users.length() > 0,
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell(
                                "Name",
                                style={
                                    "font_weight": "700",
                                    "font_size": "0.7rem",
                                    "text_transform": "uppercase",
                                    "letter_spacing": "0.05em",
                                    "color": "#64748b",
                                },
                            ),
                            rx.table.column_header_cell(
                                "Username",
                                style={
                                    "font_weight": "700",
                                    "font_size": "0.7rem",
                                    "text_transform": "uppercase",
                                    "letter_spacing": "0.05em",
                                    "color": "#64748b",
                                },
                            ),
                            rx.table.column_header_cell(
                                "Role",
                                style={
                                    "font_weight": "700",
                                    "font_size": "0.7rem",
                                    "text_transform": "uppercase",
                                    "letter_spacing": "0.05em",
                                    "color": "#64748b",
                                },
                            ),
                            rx.table.column_header_cell(
                                "Actions",
                                style={
                                    "font_weight": "700",
                                    "font_size": "0.7rem",
                                    "text_transform": "uppercase",
                                    "letter_spacing": "0.05em",
                                    "color": "#64748b",
                                },
                            ),
                        ),
                    ),
                    rx.table.body(
                        rx.foreach(TaskState.users, _employee_row),
                    ),
                    width="100%",
                    class_name="ceo-workload-table",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon("users", size=36, color="#D1D5DB"),
                        rx.text("No team members found.", color="#94A3B8", font_size="0.9rem"),
                        spacing="2",
                        align="center",
                    ),
                    padding="2rem",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        # Dialogs
        _add_employee_dialog(),
        _delete_employee_dialog(),
        # Container styling
        margin_top="1rem",
        padding="1.25rem",
        border="1px solid rgba(15, 23, 42, 0.06)",
        border_radius="16px",
        background_color="#FFFFFF",
        width="100%",
        box_shadow="0 4px 24px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15, 23, 42, 0.04)",
    )
