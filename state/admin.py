"""Admin dashboard state. Ported from the original admin.py.

Streamlit reran the whole script (and re-hit Google Sheets) on every
interaction. Here we fetch once in load_dashboard (page on_load) and cache
the raw rows on the state; each action (record contribution, approve loan,
etc.) writes to Sheets and then refreshes just the slice of state it
touched.
"""

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


class AdminState(AuthState):
    org_name: str = "Your Cooperative"
    org_code: str = ""

    members: list[dict[str, str]] = []
    contributions: list[dict[str, str]] = []
    loans: list[dict[str, str]] = []

    # ── overview tab ──
    total_members: int = 0
    total_savings_display: str = "₦0.00"
    pending_loans_count: int = 0
    loans_disbursed_display: str = "₦0.00"
    recent_contributions: list[dict[str, str]] = []

    # ── members tab ──
    member_rows: list[dict[str, str]] = []

    # ── contributions tab ──
    contrib_member_id: str = ""
    contrib_amount: str = ""
    contrib_error: str = ""
    contrib_success: str = ""

    # ── loans tab ──
    pending_loans: list[dict[str, str]] = []
    approved_loans: list[dict[str, str]] = []
    all_loans_rows: list[dict[str, str]] = []
    repay_loan_id: str = ""
    repay_amount: str = ""
    repay_error: str = ""
    repay_success: str = ""

    @rx.var
    def member_options(self) -> list[str]:
        return [f"{m['name']} ({m['email']})" for m in self.members]

    @rx.var
    def approved_loan_options(self) -> list[str]:
        return [f"{l['member_name']} — {format_naira(l['amount'])} (ID: {l['id']})" for l in self.approved_loans]

    @rx.var
    def has_org(self) -> bool:
        return bool(self.user.get("org_id", "").strip())

    # ── Load ─────────────────────────────────────────────────────────────

    @rx.event
    def load_dashboard(self):
        redirect = self.require_admin()
        if redirect is not None:
            return redirect

        org_id = self.user.get("org_id", "").strip()
        if not org_id:
            return

        org = sheets.get_org_by_id(org_id)
        self.org_name = org["name"] if org else "Your Cooperative"
        self.org_code = org["org_code"] if org else ""

        self.members = sheets.get_org_members(org_id)
        self.contributions = sheets.get_org_contributions(org_id)
        self.loans = sheets.get_org_loans(org_id)

        self._recompute_overview()
        self._recompute_members()
        self._recompute_loans()

    def _recompute_overview(self):
        self.total_members = len(self.members)
        self.total_savings_display = format_naira(sum(_to_float(c["amount"]) for c in self.contributions))
        self.pending_loans_count = len([l for l in self.loans if l["status"] == "pending"])
        approved_amount = sum(_to_float(l["amount"]) for l in self.loans if l["status"] == "approved")
        self.loans_disbursed_display = format_naira(approved_amount)

        recent = sorted(self.contributions, key=lambda c: c.get("date", ""), reverse=True)[:5]
        self.recent_contributions = [
            {
                "date": c.get("date", ""),
                "member_name": c.get("member_name", ""),
                "amount": format_naira(c.get("amount", 0)),
            }
            for c in recent
        ]

    def _recompute_members(self):
        rows = []
        for m in self.members:
            total = sum(
                _to_float(c["amount"]) for c in self.contributions
                if c.get("member_id") == m.get("user_id")
            )
            rows.append({
                "name": m.get("name", ""),
                "email": m.get("email", ""),
                "total_savings": f"₦{total:,.2f}",
                "joined": m.get("created_at", "")[:10],
            })
        self.member_rows = rows

    def _recompute_loans(self):
        self.pending_loans = [
            {
                **l,
                "amount_display": format_naira(l["amount"]),
                "requested_display": str(l.get("requested_at", ""))[:10],
            }
            for l in self.loans if l["status"] == "pending"
        ]
        self.approved_loans = [l for l in self.loans if l["status"] == "approved"]

        rows = []
        for l in self.loans:
            balance = sheets.get_loan_balance(l["id"], l["amount"])
            rows.append({
                "member": l.get("member_name", ""),
                "amount": f"₦{_to_float(l['amount']):,.2f}",
                "purpose": l.get("purpose", ""),
                "status": l.get("status", "").capitalize(),
                "balance": f"₦{balance:,.2f}",
                "requested": str(l.get("requested_at", ""))[:10],
            })
        self.all_loans_rows = rows

    # ── Contributions ────────────────────────────────────────────────────

    @rx.event
    def set_contrib_amount(self, value: str):
        self.contrib_amount = value

    @rx.event
    def set_repay_amount(self, value: str):
        self.repay_amount = value

    @rx.event
    def set_contrib_member(self, label: str):
        for m in self.members:
            if f"{m['name']} ({m['email']})" == label:
                self.contrib_member_id = m["user_id"]
                return

    @rx.event
    def submit_contribution(self):
        self.contrib_error = ""
        self.contrib_success = ""

        if not self.contrib_member_id:
            self.contrib_error = "Please select a member."
            return
        amount = _to_float(self.contrib_amount)
        if amount <= 0:
            self.contrib_error = "Enter a valid amount."
            return

        member = next((m for m in self.members if m["user_id"] == self.contrib_member_id), None)
        member_name = member["name"] if member else ""
        org_id = self.user.get("org_id", "").strip()

        sheets.record_contribution(org_id, self.contrib_member_id, member_name, amount, self.user.get("name", ""))

        self.contrib_success = f"Contribution of {format_naira(amount)} recorded for {member_name}."
        self.contrib_amount = ""
        self.contrib_member_id = ""
        self.contributions = sheets.get_org_contributions(org_id)
        self._recompute_overview()
        self._recompute_members()

    # ── Loans ────────────────────────────────────────────────────────────

    @rx.event
    def approve_loan(self, loan_id: str):
        sheets.review_loan(loan_id, "approved", self.user.get("name", ""))
        org_id = self.user.get("org_id", "").strip()
        self.loans = sheets.get_org_loans(org_id)
        self._recompute_overview()
        self._recompute_loans()

    @rx.event
    def reject_loan(self, loan_id: str):
        sheets.review_loan(loan_id, "rejected", self.user.get("name", ""))
        org_id = self.user.get("org_id", "").strip()
        self.loans = sheets.get_org_loans(org_id)
        self._recompute_overview()
        self._recompute_loans()

    @rx.event
    def set_repay_loan(self, label: str):
        for l in self.approved_loans:
            if f"{l['member_name']} — {format_naira(l['amount'])} (ID: {l['id']})" == label:
                self.repay_loan_id = l["id"]
                return

    @rx.event
    def submit_repayment(self):
        self.repay_error = ""
        self.repay_success = ""

        if not self.repay_loan_id:
            self.repay_error = "Please select a loan."
            return
        amount = _to_float(self.repay_amount)
        if amount <= 0:
            self.repay_error = "Enter a valid amount."
            return

        loan = next((l for l in self.loans if l["id"] == self.repay_loan_id), None)
        if not loan:
            self.repay_error = "Loan not found."
            return

        balance = sheets.get_loan_balance(loan["id"], loan["amount"])
        if amount > balance:
            self.repay_error = f"Repayment exceeds outstanding balance of {format_naira(balance)}."
            return

        org_id = self.user.get("org_id", "").strip()
        sheets.record_repayment(loan["id"], org_id, loan["member_id"], amount)

        self.repay_success = f"Repayment of {format_naira(amount)} recorded."
        self.repay_amount = ""
        self.repay_loan_id = ""
        self.loans = sheets.get_org_loans(org_id)
        self._recompute_loans()
