import reflex as rx

from ..state.auth import AuthState
from ..components.navbar import navbar
from .. import styles


def _field(label: str, **input_props) -> rx.Component:
    return rx.vstack(
        rx.text(label, size="2", weight="medium", color="var(--gray-11)"),
        rx.input(width="100%", **input_props),
        spacing="1",
        width="100%",
    )


def login_tab() -> rx.Component:
    return rx.vstack(
        rx.heading("Welcome back", size="4"),
        rx.text("Log in to your cooperative account.", color="var(--gray-10)", size="2"),
        _field(
            "Email",
            placeholder="you@example.com",
            value=AuthState.login_email,
            on_change=AuthState.set_login_email,
        ),
        _field(
            "Password",
            placeholder="••••••••",
            type="password",
            value=AuthState.login_password,
            on_change=AuthState.set_login_password,
        ),
        rx.cond(
            AuthState.login_error != "",
            rx.callout(AuthState.login_error, icon="triangle_alert", color_scheme="red", size="1", width="100%"),
        ),
        rx.button("Login", on_click=AuthState.do_login, width="100%", size="3", color_scheme="green"),
        spacing="4",
        width="100%",
        padding_top="1em",
    )


def register_org_tab() -> rx.Component:
    return rx.vstack(
        rx.heading("Register your cooperative", size="4"),
        rx.text("Create an admin account and get an organization code to share with members.", color="var(--gray-10)", size="2"),
        _field(
            "Cooperative Name",
            placeholder="e.g. Ilorin Teachers Cooperative",
            value=AuthState.reg_org_name,
            on_change=AuthState.set_reg_org_name,
        ),
        _field(
            "Your Full Name",
            placeholder="e.g. Abdul Anafi",
            value=AuthState.reg_admin_name,
            on_change=AuthState.set_reg_admin_name,
        ),
        _field(
            "Admin Email",
            placeholder="you@example.com",
            value=AuthState.reg_org_email,
            on_change=AuthState.set_reg_org_email,
        ),
        _field(
            "Password",
            type="password",
            value=AuthState.reg_org_password,
            on_change=AuthState.set_reg_org_password,
        ),
        _field(
            "Confirm Password",
            type="password",
            value=AuthState.reg_org_confirm,
            on_change=AuthState.set_reg_org_confirm,
        ),
        rx.cond(
            AuthState.reg_org_error != "",
            rx.callout(AuthState.reg_org_error, icon="triangle_alert", color_scheme="red", size="1", width="100%"),
        ),
        rx.cond(
            AuthState.reg_org_success_code != "",
            rx.callout(
                rx.vstack(
                    rx.text("Cooperative registered successfully!", weight="bold"),
                    rx.text(f"Your Organization Code: {AuthState.reg_org_success_code}"),
                    rx.text("Share this with your members so they can join.", size="2"),
                    spacing="1",
                ),
                icon="party_popper",
                color_scheme="green",
                size="1",
                width="100%",
            ),
        ),
        rx.button("Register Cooperative", on_click=AuthState.register_org, width="100%", size="3", color_scheme="green"),
        spacing="4",
        width="100%",
        padding_top="1em",
    )


def register_member_tab() -> rx.Component:
    return rx.vstack(
        rx.heading("Join your cooperative", size="4"),
        rx.text("Ask your cooperative admin for the organization code.", color="var(--gray-10)", size="2"),
        _field(
            "Organization Code",
            placeholder="e.g. ILORI1234",
            value=AuthState.reg_member_org_code,
            on_change=AuthState.set_reg_member_org_code,
        ),
        _field(
            "Full Name",
            value=AuthState.reg_member_name,
            on_change=AuthState.set_reg_member_name,
        ),
        _field(
            "Email",
            placeholder="you@example.com",
            value=AuthState.reg_member_email,
            on_change=AuthState.set_reg_member_email,
        ),
        _field(
            "Password",
            type="password",
            value=AuthState.reg_member_password,
            on_change=AuthState.set_reg_member_password,
        ),
        _field(
            "Confirm Password",
            type="password",
            value=AuthState.reg_member_confirm,
            on_change=AuthState.set_reg_member_confirm,
        ),
        rx.cond(
            AuthState.reg_member_error != "",
            rx.callout(AuthState.reg_member_error, icon="triangle_alert", color_scheme="red", size="1", width="100%"),
        ),
        rx.cond(
            AuthState.reg_member_success != "",
            rx.callout(AuthState.reg_member_success, icon="party_popper", color_scheme="green", size="1", width="100%"),
        ),
        rx.button("Join Cooperative", on_click=AuthState.register_member, width="100%", size="3", color_scheme="green"),
        spacing="4",
        width="100%",
        padding_top="1em",
    )


def landing() -> rx.Component:
    return rx.box(
        navbar(),
        rx.center(
            rx.vstack(
                rx.vstack(
                    rx.heading("🏛️ Kopt-OS", size="8"),
                    rx.text(
                        "The digital operating system for cooperative societies",
                        size="4",
                        color="var(--gray-10)",
                    ),
                    rx.text(
                        "Manage members, savings, loans, and financial records — all in one place.",
                        size="2",
                        color="var(--gray-9)",
                    ),
                    spacing="2",
                    align="center",
                    padding_bottom="1.5em",
                ),
                rx.box(
                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("Login", value="login"),
                            rx.tabs.trigger("Register Cooperative", value="register_org"),
                            rx.tabs.trigger("Join as Member", value="register_member"),
                        ),
                        rx.tabs.content(login_tab(), value="login"),
                        rx.tabs.content(register_org_tab(), value="register_org"),
                        rx.tabs.content(register_member_tab(), value="register_member"),
                        default_value="login",
                        width="100%",
                    ),
                    **styles.CARD_STYLE,
                    max_width="480px",
                ),
                spacing="4",
                align="center",
                padding="3em 1.5em",
                max_width="520px",
                width="100%",
            ),
            width="100%",
        ),
        **styles.PAGE_STYLE,
    )
