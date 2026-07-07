import reflex as rx

from ..state.member import MemberState
from ..components.navbar import navbar
from .. import styles


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


def savings_tab() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.text("Total Savings", size="2", color="var(--gray-10)"),
            rx.heading(MemberState.total_savings_display, size="7"),
            padding="1.25em",
            border_radius="0.75em",
            border=f"1px solid {styles.BORDER}",
            background="var(--gray-2)",
            width="100%",
        ),
        rx.vstack(
            rx.heading("Contribution History", size="4", padding_top="1em"),
            _simple_table(
                ["Date", "Amount"],
                MemberState.contribution_rows,
                ["date", "amount"],
                "No contributions recorded yet. Contact your cooperative admin.",
            ),
            width="100%",
            spacing="2",
        ),
        rx.cond(
            MemberState.monthly_chart_data.length() > 1,
            rx.vstack(
                rx.heading("Monthly Contributions", size="4", padding_top="1em"),
                rx.recharts.bar_chart(
                    rx.recharts.bar(data_key="amount", fill=styles.ACCENT),
                    rx.recharts.x_axis(data_key="month"),
                    rx.recharts.y_axis(),
                    data=MemberState.monthly_chart_data,
                    width="100%",
                    height=280,
                ),
                width="100%",
                spacing="2",
            ),
        ),
        spacing="4",
        width="100%",
        padding_top="1em",
    )


def _active_loan_card(loan: rx.Var) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(loan["amount_display"], weight="bold"),
                rx.text(f"— {loan['purpose']}", color="var(--gray-10)"),
                spacing="1",
            ),
            rx.hstack(
                rx.text(f"Paid: {loan['paid_display']}", size="2"),
                rx.text(f"Balance: {loan['balance_display']}", size="2"),
                spacing="4",
            ),
            rx.progress(value=loan["progress"], width="100%"),
            rx.text(f"{loan['progress']}% repaid", size="1", color="var(--gray-9)"),
            spacing="2",
            width="100%",
        ),
        padding="1em",
        border=f"1px solid {styles.BORDER}",
        border_radius="0.75em",
        width="100%",
    )


def loans_tab() -> rx.Component:
    return rx.vstack(
        rx.cond(
            MemberState.active_loans.length() > 0,
            rx.vstack(
                rx.heading("Active Loans", size="4"),
                rx.foreach(MemberState.active_loans, _active_loan_card),
                spacing="3",
                width="100%",
            ),
        ),
        rx.box(
            rx.heading("Request a Loan", size="4"),
            rx.cond(
                MemberState.has_pending_loan,
                rx.callout(
                    "You already have a pending loan request. Wait for admin review before requesting another.",
                    icon="triangle_alert",
                    color_scheme="amber",
                    size="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.input(
                        placeholder="Loan Amount (₦, min 1,000)",
                        type="number",
                        value=MemberState.loan_amount,
                        on_change=MemberState.set_loan_amount,
                        width="100%",
                    ),
                    rx.text_area(
                        placeholder="Purpose / Reason — e.g. School fees, Business stock, Medical emergency",
                        value=MemberState.loan_purpose,
                        on_change=MemberState.set_loan_purpose,
                        width="100%",
                    ),
                    rx.cond(
                        MemberState.loan_error != "",
                        rx.callout(MemberState.loan_error, color_scheme="red", size="1", width="100%"),
                    ),
                    rx.cond(
                        MemberState.loan_success != "",
                        rx.callout(MemberState.loan_success, color_scheme="green", size="1", width="100%"),
                    ),
                    rx.button("Submit Loan Request", on_click=MemberState.submit_loan_request, width="100%", color_scheme="green"),
                    spacing="3",
                    width="100%",
                    padding_top="0.5em",
                ),
            ),
            **styles.CARD_STYLE,
            padding_top="1em",
        ),
        spacing="4",
        width="100%",
        padding_top="1em",
    )


def history_tab() -> rx.Component:
    return rx.vstack(
        rx.heading("All Loan History", size="4"),
        _simple_table(
            ["Date", "Amount", "Purpose", "Status", "Balance"],
            MemberState.loan_history_rows,
            ["date", "amount", "purpose", "status", "balance"],
            "No loan history yet.",
        ),
        spacing="3",
        width="100%",
        padding_top="1em",
    )


def member_dashboard() -> rx.Component:
    return rx.box(
        navbar(),
        rx.container(
            rx.vstack(
                rx.heading(f"👤 {MemberState.user_name}", size="7"),
                rx.text(MemberState.org_name, color="var(--gray-10)"),
                rx.tabs.root(
                    rx.tabs.list(
                        rx.tabs.trigger("💰 Savings", value="savings"),
                        rx.tabs.trigger("🏦 Loans", value="loans"),
                        rx.tabs.trigger("📋 History", value="history"),
                    ),
                    rx.tabs.content(savings_tab(), value="savings"),
                    rx.tabs.content(loans_tab(), value="loans"),
                    rx.tabs.content(history_tab(), value="history"),
                    default_value="savings",
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
