from __future__ import annotations

import flet as ft

from APP.core import backup
from APP.core.config import get_config
from APP.core.database import execute
from APP.core.security import can_access

from .style import PRIMARY_COLOR, SURFACE

PRIMARY_BUTTON_STYLE = ft.ButtonStyle(
    bgcolor={ft.MaterialState.DEFAULT: PRIMARY_COLOR},
    color={ft.MaterialState.DEFAULT: "white"},
)


def _obter_config_loja():
    row = execute("SELECT * FROM configuracoes_loja WHERE id = 1", fetchone=True)
    return row


def _salvar_config(dados):
    execute(
        """
        UPDATE configuracoes_loja
        SET nome = ?, cnpj = ?, endereco = ?, telefone = ?, logo = ?
        WHERE id = 1
        """,
        (
            dados["nome"],
            dados["cnpj"],
            dados["endereco"],
            dados["telefone"],
            dados["logo"],
        ),
        commit=True,
    )


def build_config_view(page: ft.Page) -> ft.View:
    if not can_access("config"):
        return ft.View("/config", controls=[ft.Text("Acesso restrito.", color="red")])
    dados = _obter_config_loja()
    nome = ft.TextField(label="Nome da loja", value=dados["nome"])
    cnpj = ft.TextField(label="CNPJ", value=dados["cnpj"])
    endereco = ft.TextField(label="Endereço", value=dados["endereco"])
    telefone = ft.TextField(label="Telefone / WhatsApp", value=dados["telefone"])
    logo = ft.TextField(label="Logo (caminho ou URL)", value=dados["logo"])

    def salvar(_):
        _salvar_config(
            {
                "nome": nome.value,
                "cnpj": cnpj.value,
                "endereco": endereco.value,
                "telefone": telefone.value,
                "logo": logo.value,
            }
        )
        page.snack_bar = ft.SnackBar(ft.Text("Configurações salvas!"), bgcolor=PRIMARY_COLOR)
        page.snack_bar.open = True
        page.update()

    def backup_agora(_):
        destino = backup.criar_backup_manual()
        page.snack_bar = ft.SnackBar(
            ft.Text(f"Backup criado em {destino.name}"), bgcolor=PRIMARY_COLOR
        )
        page.snack_bar.open = True
        page.update()

    cfg = get_config()
    info = ft.Text(
        f"Banco de dados: {cfg.database_path}\nLog: {cfg.log_path}",
        color="white70",
    )

    return ft.View(
        "/config",
        controls=[
            ft.Column(
                controls=[
                    ft.Text("Configurações da Loja", size=24, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        bgcolor=SURFACE,
                        border_radius=12,
                        padding=16,
                        content=ft.Column(
                            controls=[nome, cnpj, endereco, telefone, logo],
                            spacing=10,
                        ),
                    ),
                    ft.Row(
                        controls=[
                            ft.FilledButton(
                                "Salvar",
                                icon=ft.icons.SAVE,
                                on_click=salvar,
                                style=PRIMARY_BUTTON_STYLE,
                            ),
                            ft.OutlinedButton(
                                "Criar backup agora",
                                icon=ft.icons.CLOUD_UPLOAD,
                                on_click=backup_agora,
                            ),
                        ]
                    ),
                    ft.Container(
                        bgcolor=SURFACE,
                        border_radius=12,
                        padding=16,
                        content=ft.Column(
                            controls=[ft.Text("Informações do sistema"), info],
                            spacing=8,
                        ),
                    ),
                ],
                spacing=16,
            )
        ],
    )


__all__ = ["build_config_view"]
