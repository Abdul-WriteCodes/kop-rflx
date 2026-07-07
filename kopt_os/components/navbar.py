import reflex as rx

from ..state.auth import AuthState
from .. import styles


def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.icon("landmark", size=22, color=styles.ACCENT),
                rx.heading("Kopt-OS", size="5"),
                spacing="2",
                align="center",
            ),
            rx.spacer(),
            rx.cond(
                AuthState.logged_in,
                rx.hstack(
                    rx.vstack(
                        rx.text(AuthState.user_name, weight="bold", size="2"),
                        rx.badge(AuthState.role, variant="soft", color_scheme="green"),
                        spacing="0",
                        align="end",
                    ),
                    rx.button(
                        rx.icon("log-out", size=16),
                        "Logout",
                        on_click=AuthState.logout,
                        variant="soft",
                        color_scheme="red",
                        size="2",
                    ),
                    spacing="4",
                    align="center",
                ),
                rx.text(""),
            ),
            width="100%",
            align="center",
            padding="1em 2em",
        ),
        border_bottom=f"1px solid {styles.BORDER}",
        width="100%",
        position="sticky",
        top="0",
        background=styles.BG,
        z_index="10",
    )
