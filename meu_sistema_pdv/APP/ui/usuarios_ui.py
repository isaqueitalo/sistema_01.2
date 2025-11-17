from __future__ import annotations

from typing import Optional

import flet as ft

from APP.core.security import can_access
from APP.models import usuarios_models

from .style import PRIMARY_COLOR, SURFACE, WARNING_COLOR

PRIMARY_BUTTON_STYLE = ft.ButtonStyle(
    bgcolor={ft.MaterialState.DEFAULT: PRIMARY_COLOR},
    color={ft.MaterialState.DEFAULT: "white"},
)


class UsuariosView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.usuario_id: Optional[int] = None
        self.nome = ft.TextField(label="Nome completo")
        self.username = ft.TextField(label="Usuário")
        self.senha = ft.TextField(label="Senha", password=True, can_reveal_password=True)
        self.role = ft.Dropdown(
            label="Papel",
            options=[
                ft.dropdown.Option("admin", "Administrador"),
                ft.dropdown.Option("gerente", "Gerente"),
                ft.dropdown.Option("vendedor", "Vendedor"),
            ],
        )
        self.tabela = ft.DataTable(
            bgcolor=SURFACE,
            column_spacing=12,
            columns=[
                ft.DataColumn(ft.Text("Nome")),
                ft.DataColumn(ft.Text("Usuário")),
                ft.DataColumn(ft.Text("Papel")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Ações")),
            ],
            rows=[],
        )
        self.carregar()

    def _toast(self, msg: str, color: str = PRIMARY_COLOR):
        self.page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=color)
        self.page.snack_bar.open = True
        self.page.update()

    def carregar(self):
        usuarios = usuarios_models.listar_usuarios()
        linhas = []
        for user in usuarios:
            linhas.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(user["nome"])),
                        ft.DataCell(ft.Text(user["username"])),
                        ft.DataCell(ft.Text(user["role"])),
                        ft.DataCell(
                            ft.Text("Ativo" if user["ativo"] else "Inativo")
                        ),
                        ft.DataCell(
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        ft.icons.EDIT,
                                        icon_color=PRIMARY_COLOR,
                                        on_click=lambda e, dados=user: self.selecionar(
                                            dados
                                        ),
                                    ),
                                    ft.IconButton(
                                        ft.icons.DELETE,
                                        icon_color=WARNING_COLOR,
                                        on_click=lambda e, uid=user["id"]: self.excluir(
                                            uid
                                        ),
                                    ),
                                ]
                            )
                        ),
                    ]
                )
            )
        self.tabela.rows = linhas
        self.page.update()

    def selecionar(self, dados):
        self.usuario_id = dados["id"]
        self.nome.value = dados["nome"]
        self.username.value = dados["username"]
        self.username.disabled = True
        self.role.value = dados["role"]
        self.senha.value = ""
        self.page.update()

    def limpar(self):
        self.usuario_id = None
        self.nome.value = ""
        self.username.value = ""
        self.username.disabled = False
        self.senha.value = ""
        self.role.value = None
        self.page.update()

    def salvar(self):
        if not all([self.nome.value, self.username.value or self.usuario_id, self.role.value]):
            self._toast("Preencha nome, usuário e papel.", WARNING_COLOR)
            return
        if self.usuario_id:
            usuarios_models.atualizar_usuario(
                self.usuario_id,
                nome=self.nome.value,
                role=self.role.value,
                senha=self.senha.value or None,
            )
            self._toast("Usuário atualizado.")
        else:
            if not self.senha.value:
                self._toast("Informe uma senha.", WARNING_COLOR)
                return
            usuarios_models.criar_usuario(
                nome=self.nome.value,
                username=self.username.value,
                senha=self.senha.value,
                role=self.role.value,
            )
            self._toast("Usuário criado.")
        self.limpar()
        self.carregar()

    def excluir(self, usuario_id: int):
        usuarios_models.excluir_usuario(usuario_id)
        self._toast("Usuário removido.")
        self.carregar()

    def build_view(self) -> ft.View:
        if not can_access("usuarios"):
            return ft.View(
                "/usuarios", controls=[ft.Text("Somente administradores.", color="red")]
            )
        formulario = ft.Container(
            bgcolor=SURFACE,
            border_radius=12,
            padding=16,
            content=ft.Column(
                controls=[
                    ft.Text("Cadastro de usuários", weight=ft.FontWeight.BOLD),
                    self.nome,
                    self.username,
                    self.senha,
                    self.role,
                    ft.Row(
                        controls=[
                            ft.FilledButton(
                                "Salvar",
                                icon=ft.icons.SAVE,
                                on_click=lambda e: self.salvar(),
                                style=PRIMARY_BUTTON_STYLE,
                            ),
                            ft.TextButton("Limpar", on_click=lambda e: self.limpar()),
                        ]
                    ),
                ],
                spacing=12,
            ),
        )
        return ft.View(
            "/usuarios",
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Gerenciamento de Usuários", size=24, weight=ft.FontWeight.BOLD),
                        formulario,
                        ft.Container(
                            bgcolor=SURFACE,
                            border_radius=12,
                            padding=16,
                            content=ft.Column(
                                controls=[ft.Text("Usuários cadastrados"), self.tabela],
                                spacing=12,
                            ),
                        ),
                    ],
                    spacing=16,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
        )


def build_usuarios_view(page: ft.Page):
    controller = UsuariosView(page)
    return controller.build_view()


__all__ = ["build_usuarios_view"]
