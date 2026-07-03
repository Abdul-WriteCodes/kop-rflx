"""Session/auth state. Ported from the original auth.py.

In Streamlit, "session state" is a global dict Streamlit manages for you.
In Reflex, each browser tab gets its own instance of rx.State automatically,
so we don't need to reinvent session handling — plain instance attributes
on AuthState *are* the per-user session.
"""

import hashlib
import secrets
import string

import reflex as rx

from .. import sheets


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed


def generate_org_code(name: str) -> str:
    prefix = "".join(c for c in name.upper() if c.isalpha())[:4]
    suffix = "".join(secrets.choice(string.digits) for _ in range(4))
    return f"{prefix}{suffix}"


class AuthState(rx.State):
    """Base auth/session state. AdminState and MemberState inherit from this
    so every page has access to the logged-in user without re-fetching it."""

    logged_in: bool = False
    user: dict[str, str] = {}

    # login form
    login_email: str = ""
    login_password: str = ""
    login_error: str = ""

    # register-organization form
    reg_org_name: str = ""
    reg_admin_name: str = ""
    reg_org_email: str = ""
    reg_org_password: str = ""
    reg_org_confirm: str = ""
    reg_org_error: str = ""
    reg_org_success_code: str = ""

    # register-member form
    reg_member_org_code: str = ""
    reg_member_name: str = ""
    reg_member_email: str = ""
    reg_member_password: str = ""
    reg_member_confirm: str = ""
    reg_member_error: str = ""
    reg_member_success: str = ""

    @rx.var
    def role(self) -> str:
        return self.user.get("role", "").strip().lower()

    @rx.var
    def user_name(self) -> str:
        return self.user.get("name", "User")

    # ── Field setters (Reflex doesn't auto-generate these) ─────────────────

    @rx.event
    def set_login_email(self, value: str):
        self.login_email = value

    @rx.event
    def set_login_password(self, value: str):
        self.login_password = value

    @rx.event
    def set_reg_org_name(self, value: str):
        self.reg_org_name = value

    @rx.event
    def set_reg_admin_name(self, value: str):
        self.reg_admin_name = value

    @rx.event
    def set_reg_org_email(self, value: str):
        self.reg_org_email = value

    @rx.event
    def set_reg_org_password(self, value: str):
        self.reg_org_password = value

    @rx.event
    def set_reg_org_confirm(self, value: str):
        self.reg_org_confirm = value

    @rx.event
    def set_reg_member_org_code(self, value: str):
        self.reg_member_org_code = value

    @rx.event
    def set_reg_member_name(self, value: str):
        self.reg_member_name = value

    @rx.event
    def set_reg_member_email(self, value: str):
        self.reg_member_email = value

    @rx.event
    def set_reg_member_password(self, value: str):
        self.reg_member_password = value

    @rx.event
    def set_reg_member_confirm(self, value: str):
        self.reg_member_confirm = value

    # ── Actions ──────────────────────────────────────────────────────────


    @rx.event
    def do_login(self):
        self.login_error = ""
        if not self.login_email or not self.login_password:
            self.login_error = "Please fill in all fields."
            return

        user = sheets.get_user_by_email(self.login_email.strip())
        if not user or not verify_password(self.login_password, user["password_hash"]):
            self.login_error = "Invalid email or password."
            return

        self.user = {k: str(v).strip() for k, v in user.items()}
        self.logged_in = True
        self.login_password = ""

        role = self.user.get("role", "").strip().lower()
        if role == "admin":
            return rx.redirect("/admin")
        if role == "member":
            return rx.redirect("/member")
        self.login_error = (
            f"Could not determine your role (got '{role}'). "
            "Check the 'role' column in the users sheet."
        )
        self.logged_in = False

    @rx.event
    def logout(self):
        self.logged_in = False
        self.user = {}
        return rx.redirect("/")

    @rx.event
    def register_org(self):
        self.reg_org_error = ""
        self.reg_org_success_code = ""

        if not all([self.reg_org_name, self.reg_admin_name, self.reg_org_email,
                    self.reg_org_password, self.reg_org_confirm]):
            self.reg_org_error = "Please fill in all fields."
            return
        if self.reg_org_password != self.reg_org_confirm:
            self.reg_org_error = "Passwords do not match."
            return
        if len(self.reg_org_password) < 6:
            self.reg_org_error = "Password must be at least 6 characters."
            return
        if sheets.email_exists(self.reg_org_email.strip()):
            self.reg_org_error = "An account with this email already exists."
            return

        org_code = generate_org_code(self.reg_org_name)
        while sheets.org_code_exists(org_code):
            org_code = generate_org_code(self.reg_org_name)

        org_id = sheets.create_organization(self.reg_org_name.strip(), self.reg_org_email.strip(), org_code)
        sheets.create_user(
            org_id, self.reg_org_email.strip(), hash_password(self.reg_org_password),
            "admin", self.reg_admin_name.strip(),
        )

        self.reg_org_success_code = org_code
        self.reg_org_name = ""
        self.reg_admin_name = ""
        self.reg_org_email = ""
        self.reg_org_password = ""
        self.reg_org_confirm = ""

    @rx.event
    def register_member(self):
        self.reg_member_error = ""
        self.reg_member_success = ""

        if not all([self.reg_member_org_code, self.reg_member_name, self.reg_member_email,
                    self.reg_member_password, self.reg_member_confirm]):
            self.reg_member_error = "Please fill in all fields."
            return
        if self.reg_member_password != self.reg_member_confirm:
            self.reg_member_error = "Passwords do not match."
            return
        if len(self.reg_member_password) < 6:
            self.reg_member_error = "Password must be at least 6 characters."
            return

        org = sheets.get_org_by_code(self.reg_member_org_code.strip())
        if not org:
            self.reg_member_error = "Organization code not found. Ask your cooperative admin for the correct code."
            return
        if sheets.email_exists(self.reg_member_email.strip()):
            self.reg_member_error = "An account with this email already exists."
            return

        sheets.create_user(
            org["org_id"], self.reg_member_email.strip(), hash_password(self.reg_member_password),
            "member", self.reg_member_name.strip(),
        )

        self.reg_member_success = f"You've joined {org['name']} successfully! You can now log in."
        self.reg_member_org_code = ""
        self.reg_member_name = ""
        self.reg_member_email = ""
        self.reg_member_password = ""
        self.reg_member_confirm = ""

    # ── Route guards, used as on_load handlers on protected pages ──────────

    def require_admin(self):
        if not self.logged_in:
            return rx.redirect("/")
        if self.role != "admin":
            return rx.redirect("/")

    def require_member(self):
        if not self.logged_in:
            return rx.redirect("/")
        if self.role != "member":
            return rx.redirect("/")
