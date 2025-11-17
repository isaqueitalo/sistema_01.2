from __future__ import annotations

from pathlib import Path

import flet as ft

from APP.core.config import get_config
from APP.core.security import can_access

from .style import SURFACE


def ler_logs(linhas: int = 100) -> str:
    caminho = Path(get_config().log_path)
    if not caminho.exists():
        return "Nenhum log registrado ainda."
    with caminho.open("r", encoding="utf-8") as arquivo:
        conteudo = arquivo.readlines()[-linhas:]
    return "".join(conteudo)


def build_logs_view(page: ft.Page) -> ft.View:
    if not can_access("logs"):
        return ft.View("/logs", controls=[ft.Text("Apenas administradores.", color="red")])
    texto = ft.Text(ler_logs(), selectable=True, size=12)

    def atualizar(_):
        texto.value = ler_logs()
        page.update()

    return ft.View(
        "/logs",
        controls=[
            ft.Column(
                controls=[
                    ft.Text("Logs do sistema", size=24, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        bgcolor=SURFACE,
                        border_radius=12,
                        padding=16,
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Text("Últimos registros"),
                                        ft.IconButton(
                                            ft.icons.REFRESH,
                                            tooltip="Atualizar",
                                            on_click=atualizar,
                                        ),
                                    ],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                ),
                                ft.Container(
                                    content=texto,
                                    height=400,
                                    border_radius=12,
                                    bgcolor="#00000033",
                                    padding=10,
                                ),
                            ],
                            spacing=10,
                        ),
                    ),
                ],
                spacing=14,
            )
        ],
    )


__all__ = ["build_logs_view"]
