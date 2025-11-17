from __future__ import annotations

from typing import Optional

import flet as ft

from APP.core.logger import get_logger
from APP.core.session import session
from APP.core.security import can_access
from APP.models import produtos_models

from .style import PRIMARY_COLOR, SURFACE, WARNING_COLOR

PRIMARY_BUTTON_STYLE = ft.ButtonStyle(
    bgcolor={ft.MaterialState.DEFAULT: PRIMARY_COLOR},
    color={ft.MaterialState.DEFAULT: "white"},
)

logger = get_logger()


class ProdutosView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.somente_consulta = session.has_role("vendedor") and not session.has_role(
            "gerente", "admin"
        )
        self.produto_id: Optional[int] = None
        self.busca_field = ft.TextField(
            label="Buscar por nome ou código",
            prefix_icon=ft.icons.SEARCH,
            on_change=lambda _: self.carregar_produtos(),
        )
        self.nome = ft.TextField(label="Nome do produto", expand=2)
        self.preco = ft.TextField(label="Preço de venda", keyboard_type=ft.KeyboardType.NUMBER)
        self.estoque = ft.TextField(label="Estoque atual", keyboard_type=ft.KeyboardType.NUMBER)
        self.estoque_minimo = ft.TextField(
            label="Estoque mínimo", keyboard_type=ft.KeyboardType.NUMBER
        )
        self.codigo = ft.TextField(label="Código de barras")
        self.categoria = ft.Dropdown(
            label="Categoria",
            options=[
                ft.dropdown.Option(op)
                for op in [
                    "Medicamento",
                    "Higiene",
                    "Cosmético",
                    "Bebida",
                    "Padaria",
                    "Limpeza",
                    "Outros",
                ]
            ],
        )
        self.validade = ft.TextField(label="Data de validade (YYYY-MM-DD)")
        self.lote = ft.TextField(label="Lote")
        self.tabela = ft.DataTable(
            bgcolor=SURFACE,
            column_spacing=12,
            columns=[
                ft.DataColumn(ft.Text("Nome")),
                ft.DataColumn(ft.Text("Estoque")),
                ft.DataColumn(ft.Text("Preço")),
                ft.DataColumn(ft.Text("Categoria")),
                ft.DataColumn(ft.Text("Validade")),
                ft.DataColumn(ft.Text("Ações")),
            ],
            rows=[],
        )
        self.carregar_produtos()

    def _alerta(self, mensagem: str, cor: str = PRIMARY_COLOR):
        self.page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor=cor)
        self.page.snack_bar.open = True
        self.page.update()

    def limpar_formulario(self):
        self.produto_id = None
        for campo in [
            self.nome,
            self.preco,
            self.estoque,
            self.estoque_minimo,
            self.codigo,
            self.validade,
            self.lote,
        ]:
            campo.value = ""
        self.categoria.value = None
        self.page.update()

    def carregar_produtos(self):
        produtos = produtos_models.listar_produtos(self.busca_field.value or None)
        linhas = []
        for item in produtos:
            estoque_baixo = item["estoque"] < item["estoque_minimo"]
            if self.somente_consulta:
                acoes = ft.DataCell(ft.Text("-"))
            else:
                acoes = ft.DataCell(
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                ft.icons.EDIT,
                                icon_color=PRIMARY_COLOR,
                                on_click=lambda e, data=item: self.selecionar_produto(
                                    data
                                ),
                            ),
                            ft.IconButton(
                                ft.icons.DELETE,
                                icon_color=WARNING_COLOR,
                                on_click=lambda e, pid=item["id"]: self.excluir_produto(pid),
                            ),
                        ]
                    )
                )
            linhas.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item["nome"])),
                        ft.DataCell(
                            ft.Text(
                                f"{item['estoque']}",
                                color=WARNING_COLOR if estoque_baixo else "white",
                            )
                        ),
                        ft.DataCell(ft.Text(f"R$ {item['preco_venda']:.2f}")),
                        ft.DataCell(ft.Text(item["categoria"] or "-")),
                        ft.DataCell(ft.Text(item["data_validade"] or "-")),
                        acoes,
                    ]
                )
            )
        self.tabela.rows = linhas
        self.page.update()

    def selecionar_produto(self, produto):
        self.produto_id = produto["id"]
        self.nome.value = produto["nome"]
        self.preco.value = str(produto["preco_venda"])
        self.estoque.value = str(produto["estoque"])
        self.estoque_minimo.value = str(produto["estoque_minimo"])
        self.codigo.value = produto["codigo_barras"] or ""
        self.categoria.value = produto["categoria"]
        self.validade.value = produto["data_validade"] or ""
        self.lote.value = produto["lote"] or ""
        self.page.update()

    def salvar_produto(self):
        try:
            preco = float(self.preco.value or "0")
            estoque = float(self.estoque.value or "0")
            estoque_minimo = float(self.estoque_minimo.value or "0")
        except ValueError:
            self._alerta("Valores numéricos inválidos.", WARNING_COLOR)
            return
        dados = dict(
            nome=self.nome.value,
            preco_venda=preco,
            estoque=estoque,
            estoque_minimo=estoque_minimo,
            codigo_barras=self.codigo.value or None,
            categoria=self.categoria.value or None,
            data_validade=self.validade.value or None,
            lote=self.lote.value or None,
        )
        if not dados["nome"]:
            self._alerta("Informe o nome do produto.", WARNING_COLOR)
            return
        if self.produto_id:
            produtos_models.atualizar_produto(self.produto_id, **dados)
            self._alerta("Produto atualizado!")
        else:
            produtos_models.criar_produto(**dados)
            self._alerta("Produto criado!")
        self.limpar_formulario()
        self.carregar_produtos()

    def excluir_produto(self, produto_id: int):
        produtos_models.excluir_produto(produto_id)
        self._alerta("Produto removido.")
        self.carregar_produtos()

    def build_view(self) -> ft.View:
        if not can_access("produtos"):
            return ft.View(
                "/produtos",
                controls=[ft.Text("Sem permissão para produtos.", color="red")],
            )
        if self.somente_consulta:
            formulario = ft.Container(
                bgcolor=SURFACE,
                border_radius=12,
                padding=16,
                content=ft.Text("Modo consulta: vendedores não podem alterar produtos."),
            )
        else:
            formulario = ft.Container(
                bgcolor=SURFACE,
                border_radius=12,
                padding=16,
                content=ft.Column(
                    controls=[
                        ft.Text("Cadastro / Edição", weight=ft.FontWeight.BOLD),
                        ft.ResponsiveRow(
                            controls=[
                                ft.Container(self.nome, col={"sm": 12, "md": 6}),
                                ft.Container(self.preco, col={"sm": 6, "md": 3}),
                                ft.Container(self.estoque, col={"sm": 6, "md": 3}),
                                ft.Container(self.estoque_minimo, col={"sm": 6, "md": 3}),
                                ft.Container(self.codigo, col={"sm": 6, "md": 3}),
                                ft.Container(self.categoria, col={"sm": 6, "md": 3}),
                                ft.Container(self.validade, col={"sm": 6, "md": 3}),
                                ft.Container(self.lote, col={"sm": 6, "md": 3}),
                            ],
                            spacing=10,
                        ),
                        ft.Row(
                            controls=[
                                ft.FilledButton(
                                    "Salvar",
                                    icon=ft.icons.SAVE,
                                    on_click=lambda e: self.salvar_produto(),
                                    style=PRIMARY_BUTTON_STYLE,
                                ),
                                ft.TextButton(
                                    "Limpar", on_click=lambda e: self.limpar_formulario()
                                ),
                            ]
                        ),
                    ],
                    spacing=12,
                ),
            )

        listagem = ft.Container(
            bgcolor=SURFACE,
            border_radius=12,
            padding=16,
            content=ft.Column(
                controls=[
                    ft.Text("Produtos cadastrados", weight=ft.FontWeight.BOLD),
                    self.busca_field,
                    self.tabela,
                ],
                spacing=12,
            ),
        )
        return ft.View(
            "/produtos",
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Gestão de Produtos", size=24, weight=ft.FontWeight.BOLD),
                        formulario,
                        listagem,
                    ],
                    spacing=16,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
        )


def build_produtos_view(page: ft.Page):
    controller = ProdutosView(page)
    return controller.build_view()


__all__ = ["build_produtos_view"]
