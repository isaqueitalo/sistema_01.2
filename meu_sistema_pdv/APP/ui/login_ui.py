from __future__ import annotations

import flet as ft

from APP.core.logger import get_logger
from APP.core.session import session
from APP.models import usuarios_models

from .style import BACKGROUND, CONTROL_STATE, PRIMARY_COLOR, SURFACE

logger = get_logger()


def build_login_view(page: ft.Page, on_success) -> ft.View:
    username = ft.TextField(
        label="Usuário",
        autofocus=True,
        color="white",
        border_radius=12,
    )
    password = ft.TextField(
        label="Senha",
        password=True,
        can_reveal_password=True,
        color="white",
        border_radius=12,
        on_submit=lambda _: autenticar(None),
    )
    feedback = ft.Text("", color="red")

    def autenticar(evt):
        usuario = usuarios_models.autenticar(username.value.strip(), password.value)
        if usuario:
            session.login(usuario)
            feedback.value = ""
            page.snack_bar = ft.SnackBar(ft.Text("Login realizado!"), bgcolor=PRIMARY_COLOR)
            page.snack_bar.open = True
            page.update()
            logger.info("Login bem-sucedido para %s", usuario["username"])
            on_success()
        else:
            feedback.value = "Usuário ou senha inválidos."
            password.value = ""
            page.update()

    entrar_btn = ft.ElevatedButton(
        text="Entrar",
        icon=ft.icons.LOGIN,
        on_click=autenticar,
        style=ft.ButtonStyle(
            bgcolor={CONTROL_STATE.DEFAULT: PRIMARY_COLOR},
            color={CONTROL_STATE.DEFAULT: "white"},
            shape={CONTROL_STATE.DEFAULT: ft.RoundedRectangleBorder(radius=12)},
        ),
    )

    card = ft.Container(
        width=420,
        padding=30,
        bgcolor=SURFACE,
        border_radius=16,
        content=ft.Column(
            controls=[
                ft.Text("Meu Sistema PDV", size=26, weight=ft.FontWeight.BOLD),
                ft.Text("Acesse com suas credenciais", color="gray"),
                username,
                password,
                entrar_btn,
                feedback,
            ],
            spacing=16,
            tight=True,
        ),
    )

    return ft.View(
        "/",
        bgcolor=BACKGROUND,
        controls=[
            ft.Row(
                controls=[card],
                alignment=ft.MainAxisAlignment.CENTER,
            )
        ],
        vertical_alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )


__all__ = ["build_login_view"]
