"""Member dashboard state. Ported from the original member.py."""

import reflex as rx

from .. import sheets
from .auth import AuthState


def _to_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def format_naira(amount) -> str:
    return f"₦{_to_float(amount):,.2f}"


class MemberState(AuthState):
    org_name: str = "Your Cooperative"

    total_savings_display: str = "₦0.00"
    contribution_rows: list[dict[str, str]] = []
    monthly_chart_data: list[dict] = []

    active_loans: list[dict] = []
    pending_loan_count: int = 0
    loan_history_rows: list[dict[str, str]] = []

    loan_amount: str = ""
    loan_purpose: str = ""
    loan_error: str = ""
    loan_success: str = ""

    @rx.var
    def has_pending_loan(self) -> bool:
        return self.pending_loan_count > 0

    # ── Load ─────────────────────────────────────────────────────────────

    @rx.event
    def load_dashboard(self):
        redirect = self.require_member()
        if redirect is not None:
            return redirect

        org_id = self.user.get("org_id", "").strip()
        org = sheets.get_org_by_id(org_id)
        self.org_name = org["name"] if org else "Your Cooperative"

        self._load_savings(org_id)
        self._load_loans(org_id)

    def _load_savings(self, org_id: str):
        member_id = self.user.get("user_id", "")
        contributions = sheets.get_member_contributions(org_id, member_id)

        total = sum(_to_float(c["amount"]) for c in contributions)
        self.total_savings_display = format_naira(total)

        sorted_contribs = sorted(contributions, key=lambda c: c.get("date", ""), reverse=True)
        self.contribution_rows = [
            {"date": c.get("date", ""), "amount": format_naira(c.get("amount", 0))}
            for c in sorted_contribs
        ]

        monthly: dict[str, float] = {}
        for c in contributions:
            date_str = c.get("date", "")
            month = date_str[:7] if len(date_str) >= 7 else "Unknown"
            monthly[month] = monthly.get(month, 0.0) + _to_float(c.get("amount", 0))
        self.monthly_chart_data = [{"month": m, "amount": amt} for m, amt in sorted(monthly.items())]

    def _load_loans(self, org_id: str):
        member_id = self.user.get("user_id", "")
        loans = sheets.get_member_loans(org_id, member_id)

        approved = [l for l in loans if l["status"] == "approved"]
        active = []
        for l in approved:
            balance = sheets.get_loan_balance(l["id"], l["amount"])
            amount = _to_float(l["amount"])
            paid = amount - balance
            progress = (paid / amount * 100) if amount > 0 else 0.0
            active.append({
                "amount_display": format_naira(l["amount"]),
                "purpose": l.get("purpose", ""),
                "paid_display": format_naira(paid),
                "balance_display": format_naira(balance),
                "progress": round(min(progress, 100), 0),
            })
        self.active_loans = active

        self.pending_loan_count = len([l for l in loans if l["status"] == "pending"])

        rows = []
        for l in loans:
            balance = sheets.get_loan_balance(l["id"], l["amount"])
            rows.append({
                "date": str(l.get("requested_at", ""))[:10],
                "amount": f"₦{_to_float(l['amount']):,.2f}",
                "purpose": l.get("purpose", ""),
                "status": l.get("status", "").capitalize(),
                "balance": f"₦{balance:,.2f}",
            })
        self.loan_history_rows = rows

    # ── Actions ──────────────────────────────────────────────────────────

    @rx.event
    def set_loan_amount(self, value: str):
        self.loan_amount = value

    @rx.event
    def set_loan_purpose(self, value: str):
        self.loan_purpose = value

    @rx.event
    def submit_loan_request(self):
        self.loan_error = ""
        self.loan_success = ""

        if self.pending_loan_count > 0:
            self.loan_error = "You already have a pending loan request."
            return

        amount = _to_float(self.loan_amount)
        if amount < 1000:
            self.loan_error = "Enter a valid amount (minimum ₦1,000)."
            return
        if not self.loan_purpose.strip():
            self.loan_error = "Please describe the purpose of the loan."
            return

        org_id = self.user.get("org_id", "").strip()
        member_id = self.user.get("user_id", "")
        sheets.request_loan(org_id, member_id, self.user.get("name", ""), amount, self.loan_purpose.strip())

        self.loan_success = "Loan request submitted. Your admin will review it shortly."
        self.loan_amount = ""
        self.loan_purpose = ""
        self._load_loans(org_id)
