import reflex as rx

config = rx.Config(
    app_name="kopt_os",
    plugins=[
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(appearance="light", accent_color="green", radius="large"),
        ),
    ],
)
