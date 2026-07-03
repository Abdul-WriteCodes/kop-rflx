"""Google Sheets data layer.

Ported from the original Streamlit app's sheets.py. Two changes from the
original:
  1. No `st.cache_resource` / `st.secrets` — Reflex apps read config from
     environment variables instead, cached with functools.lru_cache.
  2. No pandas — everything is plain list[dict] / dict, since those are the
     types Reflex state vars serialize cleanly to the frontend.
"""

import functools
import json
import os
import uuid
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_TABS = ["organizations", "users", "contributions", "loans", "repayments"]

HEADERS = {
    "organizations": ["org_id", "name", "org_code", "admin_email", "created_at"],
    "users": ["user_id", "org_id", "email", "password_hash", "role", "name", "created_at"],
    "contributions": ["id", "org_id", "member_id", "member_name", "amount", "date", "recorded_by"],
    "loans": ["id", "org_id", "member_id", "member_name", "amount", "purpose", "status", "requested_at", "reviewed_at", "reviewed_by"],
    "repayments": ["id", "loan_id", "org_id", "member_id", "amount", "date"],
}


def _to_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


# ── Connection ──────────────────────────────────────────────────────────────

@functools.lru_cache(maxsize=1)
def get_client():
    service_account_info = os.environ.get("GCP_SERVICE_ACCOUNT_INFO")
    if service_account_info:
        creds_dict = json.loads(service_account_info)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        service_account_file = os.environ.get("GCP_SERVICE_ACCOUNT_FILE", "service_account.json")
        creds = Credentials.from_service_account_file(service_account_file, scopes=SCOPES)
    return gspread.authorize(creds)


@functools.lru_cache(maxsize=1)
def get_spreadsheet():
    client = get_client()
    sheet_id = os.environ.get("SHEET_ID")
    if not sheet_id:
        raise ValueError("SHEET_ID not set in the environment (.env file).")
    return client.open_by_key(sheet_id)


def get_sheet(tab_name: str):
    ss = get_spreadsheet()
    try:
        ws = ss.worksheet(tab_name)
    except gspread.WorksheetNotFound:
        ws = ss.add_worksheet(title=tab_name, rows=1000, cols=20)
        ws.append_row(HEADERS[tab_name])
    return ws


def read_sheet(tab_name: str) -> list[dict]:
    ws = get_sheet(tab_name)
    records = ws.get_all_records(
        expected_headers=HEADERS[tab_name],
        value_render_option="FORMATTED_VALUE",
    )
    return [{k: str(v).strip() for k, v in record.items()} for record in records]


def append_row(tab_name: str, row: dict):
    ws = get_sheet(tab_name)
    ordered = [row.get(h, "") for h in HEADERS[tab_name]]
    ws.append_row(ordered, value_input_option="USER_ENTERED")


def update_cell_by_id(tab_name: str, id_col: str, id_val: str, update: dict) -> bool:
    ws = get_sheet(tab_name)
    records = ws.get_all_records()
    headers = ws.row_values(1)
    for i, record in enumerate(records):
        if str(record.get(id_col)) == str(id_val):
            row_num = i + 2  # +1 for header, +1 for 1-indexing
            for col_name, value in update.items():
                if col_name in headers:
                    col_num = headers.index(col_name) + 1
                    ws.update_cell(row_num, col_num, value)
            return True
    return False


# ── Organization helpers ─────────────────────────────────────────────────────

def org_code_exists(code: str) -> bool:
    rows = read_sheet("organizations")
    return any(r["org_code"].upper() == code.upper() for r in rows)


def get_org_by_code(code: str) -> dict | None:
    rows = read_sheet("organizations")
    for r in rows:
        if r["org_code"].upper() == code.upper():
            return r
    return None


def get_org_by_id(org_id: str) -> dict | None:
    rows = read_sheet("organizations")
    for r in rows:
        if r["org_id"] == org_id:
            return r
    return None


def create_organization(name: str, admin_email: str, org_code: str) -> str:
    org_id = str(uuid.uuid4())[:8].upper()
    append_row("organizations", {
        "org_id": org_id,
        "name": name,
        "org_code": org_code,
        "admin_email": admin_email,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    return org_id


# ── User helpers ──────────────────────────────────────────────────────────────

def email_exists(email: str) -> bool:
    rows = read_sheet("users")
    return any(r["email"].lower() == email.lower() for r in rows)


def get_user_by_email(email: str) -> dict | None:
    rows = read_sheet("users")
    for r in rows:
        if r["email"].lower() == email.lower():
            return r
    return None


def create_user(org_id: str, email: str, password_hash: str, role: str, name: str) -> str:
    user_id = str(uuid.uuid4())[:8].upper()
    append_row("users", {
        "user_id": user_id,
        "org_id": org_id,
        "email": email,
        "password_hash": password_hash,
        "role": role,
        "name": name,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    return user_id


def get_org_members(org_id: str) -> list[dict]:
    rows = read_sheet("users")
    return [r for r in rows if r["org_id"] == org_id and r["role"] == "member"]


# ── Contribution helpers ─────────────────────────────────────────────────────

def record_contribution(org_id: str, member_id: str, member_name: str, amount: float, recorded_by: str):
    append_row("contributions", {
        "id": str(uuid.uuid4())[:8].upper(),
        "org_id": org_id,
        "member_id": member_id,
        "member_name": member_name,
        "amount": amount,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "recorded_by": recorded_by,
    })


def get_member_contributions(org_id: str, member_id: str) -> list[dict]:
    rows = read_sheet("contributions")
    return [r for r in rows if r["org_id"] == org_id and r["member_id"] == member_id]


def get_org_contributions(org_id: str) -> list[dict]:
    rows = read_sheet("contributions")
    return [r for r in rows if r["org_id"] == org_id]


def get_member_total_savings(org_id: str, member_id: str) -> float:
    rows = get_member_contributions(org_id, member_id)
    return sum(_to_float(r["amount"]) for r in rows)


# ── Loan helpers ──────────────────────────────────────────────────────────────

def request_loan(org_id: str, member_id: str, member_name: str, amount: float, purpose: str):
    append_row("loans", {
        "id": str(uuid.uuid4())[:8].upper(),
        "org_id": org_id,
        "member_id": member_id,
        "member_name": member_name,
        "amount": amount,
        "purpose": purpose,
        "status": "pending",
        "requested_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reviewed_at": "",
        "reviewed_by": "",
    })


def get_org_loans(org_id: str) -> list[dict]:
    rows = read_sheet("loans")
    return [r for r in rows if r["org_id"] == org_id]


def get_member_loans(org_id: str, member_id: str) -> list[dict]:
    rows = read_sheet("loans")
    return [r for r in rows if r["org_id"] == org_id and r["member_id"] == member_id]


def review_loan(loan_id: str, status: str, reviewed_by: str):
    update_cell_by_id("loans", "id", loan_id, {
        "status": status,
        "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "reviewed_by": reviewed_by,
    })


def record_repayment(loan_id: str, org_id: str, member_id: str, amount: float):
    append_row("repayments", {
        "id": str(uuid.uuid4())[:8].upper(),
        "loan_id": loan_id,
        "org_id": org_id,
        "member_id": member_id,
        "amount": amount,
        "date": datetime.now().strftime("%Y-%m-%d"),
    })


def get_loan_repayments(loan_id: str) -> list[dict]:
    rows = read_sheet("repayments")
    return [r for r in rows if r["loan_id"] == loan_id]


def get_loan_balance(loan_id: str, loan_amount) -> float:
    rows = get_loan_repayments(loan_id)
    paid = sum(_to_float(r["amount"]) for r in rows)
    return max(0.0, _to_float(loan_amount) - paid)
