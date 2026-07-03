import reflex as rx

from .pages.landing import landing
from .pages.admin import admin_dashboard
from .pages.member import member_dashboard
from .state.admin import AdminState
from .state.member import MemberState

app = rx.App()

app.add_page(landing, route="/", title="Kopt-OS")
app.add_page(admin_dashboard, route="/admin", title="Kopt-OS · Admin", on_load=AdminState.load_dashboard)
app.add_page(member_dashboard, route="/member", title="Kopt-OS · Member", on_load=MemberState.load_dashboard)
