import reflex as rx

from ..state.admin import AdminState
from ..components.navbar import navbar
from .. import styles


def _stat_card(label: str, value) -> rx.Component:
    return rx.box(
        rx.text(label, size="2", color="var(--gray-10)"),
        rx.heading(value, size="6"),
        padding="1.25em",
        border_radius="0.75em",
        border=f"1px solid {styles.BORDER}",
        background="var(--gray-2)",
        width="100%",
    )


def _simple_table(headers: list[str], rows: rx.Var, cell_keys: list[str], empty_message: str) -> rx.Component:
    return rx.cond(
        rows.length() > 0,
        rx.table.root(
            rx.table.header(
                rx.table.row(*[rx.table.column_header_cell(h) for h in headers]),
            ),
            rx.table.body(
                rx.foreach(
                    rows,
                    lambda row: rx.table.row(*[rx.table.cell(row[k]) for k in cell_keys]),
                ),
            ),
            width="100%",
            variant="surface",
        ),
        rx.callout(empty_message, icon="info", size="1", width="100%"),
    )


def overview_tab() -> rx.Component:
    return rx.vstack(
        rx.grid(
            _stat_card("Total Members", AdminState.total_members),
            _stat_card("Total Savings", AdminState.total_savings_display),
            _stat_card("Pending Loans", AdminState.pending_loans_count),
            _stat_card("Loans Disbursed", AdminState.loans_disbursed_display),
            columns=rx.breakpoints(initial="1", sm="2", lg="4"),
            spacing="3",
            width="100%",
        ),
        rx.vstack(
            rx.heading("Recent Contributions", size="4", padding_top="1em"),
            _simple_table(
                ["Date", "Member", "Amount"],
                AdminState.recent_contributions,
                ["date", "member_name", "amount"],
                "No contributions recorded yet.",
            ),
            width="100%",
            spacing="2",
        ),
        spacing="4",
        width="100%",
        padding_top="1em",
    )


def members_tab() -> rx.Component:
    return rx.vstack(
        rx.heading("Members", size="4"),
        _simple_table(
            ["Name", "Email", "Total Savings", "Joined"],
            AdminState.member_rows,
            ["name", "email", "total_savings", "joined"],
            "No members yet. Share the organization code with your members so they can sign up.",
        ),
        spacing="3",
        width="100%",
        padding_top="1em",
    )


def contributions_tab() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.heading("Record Contribution", size="4"),
            rx.cond(
                AdminState.members.length() > 0,
                rx.vstack(
                    rx.select(
                        AdminState.member_options,
                        placeholder="Select member",
                        on_change=AdminState.set_contrib_member,
                        width="100%",
                    ),
                    rx.input(
                        placeholder="Amount (₦)",
                        type="number",
                        value=AdminState.contrib_amount,
                        on_change=AdminState.set_contrib_amount,
                        width="100%",
                    ),
                    rx.cond(
                        AdminState.contrib_error != "",
                        rx.callout(AdminState.contrib_error, color_scheme="red", size="1", width="100%"),
                    ),
                    rx.cond(
                        AdminState.contrib_success != "",
                        rx.callout(AdminState.contrib_success, color_scheme="green", size="1", width="100%"),
                    ),
                    rx.button("Record Contribution", on_click=AdminState.submit_contribution, width="100%", color_scheme="green"),
                    spacing="3",
                    width="100%",
                    padding_top="0.5em",
                ),
                rx.callout("No members yet to record contributions for.", icon="info", size="1", width="100%"),
            ),
            **styles.CARD_STYLE,
        ),
        rx.vstack(
            rx.heading("All Contributions", size="4", padding_top="1em"),
            _simple_table(
                ["Date", "Member", "Amount"],
                AdminState.recent_contributions,
                ["date", "member_name", "amount"],
                "No contributions recorded yet.",
            ),
            width="100%",
            spacing="2",
        ),
        spacing="4",
        width="100%",
        padding_top="1em",
    )


def _pending_loan_card(loan: rx.Var) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(loan["member_name"], weight="bold"),
                rx.text(f"{loan['amount_display']} · requested {loan['requested_display']}", size="2", color="var(--gray-10)"),
                rx.text(loan["purpose"], size="2"),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.icon("check", size=16),
                    "Approve",
                    on_click=AdminState.approve_loan(loan["id"]),
                    color_scheme="green",
                    size="2",
                ),
                rx.button(
                    rx.icon("x", size=16),
                    "Reject",
                    on_click=AdminState.reject_loan(loan["id"]),
                    color_scheme="red",
                    variant="soft",
                    size="2",
                ),
                spacing="2",
            ),
            width="100%",
            align="start",
        ),
        padding="1em",
        border=f"1px solid {styles.BORDER}",
        border_radius="0.75em",
        width="100%",
    )


def loans_tab() -> rx.Component:
    return rx.vstack(
        rx.vstack(
            rx.heading("Pending Loan Requests", size="4"),
            rx.cond(
                AdminState.pending_loans.length() > 0,
                rx.vstack(
                    rx.foreach(AdminState.pending_loans, _pending_loan_card),
                    spacing="3",
                    width="100%",
                ),
                rx.callout("No pending loan requests.", icon="info", size="1", width="100%"),
            ),
            spacing="3",
            width="100%",
        ),
        rx.box(
            rx.heading("Record Repayment", size="4"),
            rx.cond(
                AdminState.approved_loans.length() > 0,
                rx.vstack(
                    rx.select(
                        AdminState.approved_loan_options,
                        placeholder="Select loan",
                        on_change=AdminState.set_repay_loan,
                        width="100%",
                    ),
                    rx.input(
                        placeholder="Repayment Amount (₦)",
                        type="number",
                        value=AdminState.repay_amount,
                        on_change=AdminState.set_repay_amount,
                        width="100%",
                    ),
                    rx.cond(
                        AdminState.repay_error != "",
                        rx.callout(AdminState.repay_error, color_scheme="red", size="1", width="100%"),
                    ),
                    rx.cond(
                        AdminState.repay_success != "",
                        rx.callout(AdminState.repay_success, color_scheme="green", size="1", width="100%"),
                    ),
                    rx.button("Record Repayment", on_click=AdminState.submit_repayment, width="100%", color_scheme="green"),
                    spacing="3",
                    width="100%",
                    padding_top="0.5em",
                ),
                rx.callout("No approved loans to record repayments against.", icon="info", size="1", width="100%"),
            ),
            **styles.CARD_STYLE,
            padding_top="1em",
        ),
        rx.vstack(
            rx.heading("All Loans", size="4", padding_top="1em"),
            _simple_table(
                ["Member", "Amount", "Purpose", "Status", "Balance", "Requested"],
                AdminState.all_loans_rows,
                ["member", "amount", "purpose", "status", "balance", "requested"],
                "No loans yet.",
            ),
            width="100%",
            spacing="2",
        ),
        spacing="4",
        width="100%",
        padding_top="1em",
    )


def admin_dashboard() -> rx.Component:
    return rx.box(
        navbar(),
        rx.container(
            rx.vstack(
                rx.heading(f"🏛️ {AdminState.org_name}", size="7"),
                rx.text(
                    f"Organization Code: {AdminState.org_code} · Admin: {AdminState.user_name}",
                    color="var(--gray-10)",
                ),
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("📊 Overview", value="overview"),
                        rx.tabs.trigger("👥 Members", value="members"),
                        rx.tabs.trigger("💰 Contributions", value="contributions"),
                        rx.tabs.trigger("🏦 Loans", value="loans"),
                    ),
                    rx.tabs.content(overview_tab(), value="overview"),
                    rx.tabs.content(members_tab(), value="members"),
                    rx.tabs.content(contributions_tab(), value="contributions"),
                    rx.tabs.content(loans_tab(), value="loans"),
                    default_value="overview",
                    width="100%",
                ),
                spacing="4",
                width="100%",
                padding="2em 0",
            ),
            max_width="1000px",
        ),
        **styles.PAGE_STYLE,
    )
