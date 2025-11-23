from __future__ import annotations

from datetime import datetime
from typing import List, Optional

import flet as ft

from APP.core.logger import get_logger
from APP.core.security import can_access
from APP.core.session import session
from APP.core.utils import format_currency
from APP.models import (
    caixa_models,
    clientes_models,
    produtos_models,
    vendas_models,
)

from .style import (
    CONTROL_STATE,
    PRIMARY_COLOR,
    SECONDARY_COLOR,
    SURFACE,
    SUCCESS_COLOR,
    WARNING_COLOR,
)

PRIMARY_BUTTON_STYLE = ft.ButtonStyle(
    bgcolor={CONTROL_STATE.DEFAULT: PRIMARY_COLOR},
    color={CONTROL_STATE.DEFAULT: "white"},
)
SECONDARY_BUTTON_STYLE = ft.ButtonStyle(
    bgcolor={CONTROL_STATE.DEFAULT: SECONDARY_COLOR},
    color={CONTROL_STATE.DEFAULT: "white"},
)

logger = get_logger()


class PDVController:
    def __init__(self, page: ft.Page, on_back) -> None:
        self.page = page
        self.on_back = on_back
        self.carrinho: List[dict] = []
        self.ultima_venda: Optional[dict] = None
        self.busca_field = ft.TextField(
            label="Código de barras ou nome",
            autofocus=True,
            border_radius=12,
            on_submit=lambda _: self._confirmar_entrada(),
            on_change=lambda e: self.atualizar_sugestoes(),
        )
        self.sugestoes_lista = ft.Column(spacing=0)
        self.sugestoes_container = ft.Container(
            content=self.sugestoes_lista,
            bgcolor=SURFACE,
            border_radius=8,
            visible=False,
            padding=0,
        )
        self.sugestoes_dados: List[dict] = []
        self.sugestoes_index: int = -1
        self._ultimo_texto_busca: str = ""
        self.carrinho_list = ft.ListView(
            spacing=4,
            padding=0,
            expand=True,
            auto_scroll=False,
        )
        self.quantidade_field = ft.TextField(
            label="Qtd",
            width=120,
            value="1",
            on_submit=lambda _: self.adicionar_item(),
        )
        self.desconto_field = ft.TextField(
            label="Desconto (R$)",
            width=150,
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=lambda _: self.atualizar_resumo(),
        )
        self.saida_valor_field = ft.TextField(
            label="Valor pago do caixa",
            width=180,
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="R$ ",
        )
        self.saida_descricao_field = ft.TextField(
            label="Descrição da saída",
            multiline=True,
            min_lines=2,
            max_lines=3,
        )
        self.perda_valor_field = ft.TextField(
            label="Valor da perda",
            width=180,
            value="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            prefix_text="R$ ",
        )
        self.perda_descricao_field = ft.TextField(
            label="Explique a perda (extravio, dano, doação, etc.)",
            multiline=True,
            min_lines=2,
            max_lines=3,
        )
        self.pagamento_dropdown = ft.Dropdown(
            label="Forma de pagamento (F9)",
            value="Dinheiro",
            options=[ft.dropdown.Option(p) for p in vendas_models.FORMAS_PAGAMENTO],
            border_radius=12,
        )
        self.cliente_dropdown = ft.Dropdown(
            label="Cliente (F7)",
            border_radius=12,
        )
        self._carregar_clientes()

        self.tabela = ft.DataTable(
            bgcolor=SURFACE,
            border_radius=12,
            column_spacing=12,
            columns=[
                ft.DataColumn(ft.Text("Produto")),
                ft.DataColumn(ft.Text("Qtd")),
                ft.DataColumn(ft.Text("Preço")),
                ft.DataColumn(ft.Text("Total")),
                ft.DataColumn(ft.Text("Ações")),
            ],
            rows=[],
        )
        self.subtotal_text = ft.Text("R$ 0,00", size=20, weight=ft.FontWeight.BOLD)
        self.desconto_text = ft.Text("R$ 0,00", color=WARNING_COLOR)
        self.total_text = ft.Text("R$ 0,00", size=24, weight=ft.FontWeight.BOLD)
        self.ultima_text = ft.Text("Nenhuma venda ainda.", color="white70")
        self.atualizar_lista_carrinho()

    def _carregar_clientes(self):
        clientes = clientes_models.listar_clientes()
        self.cliente_dropdown.options = [
            ft.dropdown.Option(str(c["id"]), c["nome"]) for c in clientes
        ]
        consumidor = next((c for c in clientes if c["nome"] == "Consumidor Final"), None)
        if consumidor:
            self.cliente_dropdown.value = str(consumidor["id"])

    def _mostrar_alerta(self, mensagem: str, color: str = WARNING_COLOR):
        self.page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor=color)
        self.page.snack_bar.open = True
        self.page.update()

    def _produto_por_busca(self, texto: str):
        texto = texto.strip()
        if not texto:
            return None
        produto = produtos_models.buscar_por_codigo(texto)
        if produto:
            return produto
        return produtos_models.buscar_por_nome(texto)

    def atualizar_sugestoes(self):
        texto = (self.busca_field.value or "").strip()
        if texto == self._ultimo_texto_busca:
            return
        self._ultimo_texto_busca = texto
        if len(texto) < 2:
            self.ocultar_sugestoes()
            return
        resultados = produtos_models.buscar_sugestoes(texto, limite=6)
        if not resultados:
            self.ocultar_sugestoes()
            return

        self.sugestoes_dados = resultados
        self.sugestoes_index = 0
        self._renderizar_sugestoes()
        self.sugestoes_container.visible = True
        self.page.update()

    def selecionar_sugestao(self, produto):
        self.busca_field.value = produto["codigo_barras"] or produto["nome"]
        self.ocultar_sugestoes()

    def ocultar_sugestoes(self):
        self.sugestoes_dados = []
        self.sugestoes_index = -1
        self._ultimo_texto_busca = ""
        if self.sugestoes_container.visible:
            self.sugestoes_container.visible = False
            self.page.update()

    def _renderizar_sugestoes(self):
        controles = []
        for idx, produto in enumerate(self.sugestoes_dados):
            selecionado = idx == self.sugestoes_index
            controles.append(
                ft.Container(
                    bgcolor="#1f2937" if selecionado else None,
                    border_radius=6,
                    padding=8,
                    on_click=lambda e, p=produto: self.selecionar_sugestao(p),
                    content=ft.Column(
                        controls=[
                            ft.Text(produto["nome"], weight=ft.FontWeight.BOLD),
                            ft.Text(
                                f"Cód: {produto['codigo_barras'] or '-'} • {format_currency(produto['preco_venda'])}",
                                size=12,
                                color="white70",
                            ),
                        ],
                        spacing=2,
                    ),
                )
            )
        self.sugestoes_lista.controls = controles

    def mover_sugestao(self, delta: int):
        if not self.sugestoes_dados:
            return
        self.sugestoes_index = (self.sugestoes_index + delta) % len(self.sugestoes_dados)
        self._renderizar_sugestoes()
        self.page.update()

    def aplicar_sugestao_atual(self):
        if not self.sugestoes_dados or self.sugestoes_index < 0:
            return
        self.selecionar_sugestao(self.sugestoes_dados[self.sugestoes_index])

    def _atalho_busca(self, e: ft.KeyboardEvent):
        """Permite navegar nas sugestões e confirmar pelo teclado.

        Esta função fica isolada para evitar problemas de indentação e
        padronizar o tratamento das teclas, já que o Flet envia os nomes
        das teclas com ou sem espaços dependendo do sistema operacional.
        """

        key = (e.key or "").replace(" ", "").upper()
        if key in ("ARROWDOWN", "DOWN"):
            self.mover_sugestao(1)
        elif key in ("ARROWUP", "UP"):
            self.mover_sugestao(-1)
        elif key in ("ENTER", "NUMPADENTER"):
            self._confirmar_entrada()
        elif key in ("ESCAPE", "ESC"):
            self.ocultar_sugestoes()

    def atualizar_lista_carrinho(self):
        if not self.carrinho:
            self.carrinho_list.controls = [
                ft.Text("Nenhum produto no carrinho.", color="white70")
            ]
        else:
            itens = []
            for item in self.carrinho:
                itens.append(
                    ft.ListTile(
                        title=ft.Text(item["nome"]),
                        subtitle=ft.Text(
                            f"Qtd: {item['quantidade']:.2f} x {format_currency(item['preco_unitario'])}"
                        ),
                        trailing=ft.Text(
                            format_currency(item["quantidade"] * item["preco_unitario"])
                        ),
                        dense=True,
                    )
                )
            self.carrinho_list.controls = itens

    def adicionar_item(self):
        produto = self._produto_por_busca(self.busca_field.value or "")
        if not produto:
            self._mostrar_alerta("Produto não encontrado.", color=WARNING_COLOR)
            return
        try:
            quantidade = float(self.quantidade_field.value or "1")
        except ValueError:
            quantidade = 1
        existente = next(
            (item for item in self.carrinho if item["produto_id"] == produto["id"]),
            None,
        )
        if existente:
            existente["quantidade"] += quantidade
        else:
            self.carrinho.append(
                {
                    "produto_id": produto["id"],
                    "nome": produto["nome"],
                    "preco_unitario": produto["preco_venda"],
                    "quantidade": quantidade,
                }
            )
        self.busca_field.value = ""
        self.quantidade_field.value = "1"
        self.ocultar_sugestoes()
        self.atualizar_tabela()
        self.atualizar_resumo()

    def atualizar_tabela(self):
        linhas = []
        for idx, item in enumerate(self.carrinho):
            linhas.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(item["nome"])),
                        ft.DataCell(
                            ft.Row(
                                controls=[
                                    ft.IconButton(
                                        ft.icons.REMOVE,
                                        on_click=lambda e, i=idx: self.ajustar_quantidade(
                                            i, -1
                                        ),
                                        icon_size=18,
                                    ),
                                    ft.Text(f"{item['quantidade']:.2f}"),
                                    ft.IconButton(
                                        ft.icons.ADD,
                                        on_click=lambda e, i=idx: self.ajustar_quantidade(
                                            i, 1
                                        ),
                                        icon_size=18,
                                    ),
                                ]
                            )
                        ),
                        ft.DataCell(ft.Text(format_currency(item["preco_unitario"]))),
                        ft.DataCell(
                            ft.Text(
                                format_currency(
                                    item["quantidade"] * item["preco_unitario"]
                                )
                            )
                        ),
                        ft.DataCell(
                            ft.IconButton(
                                ft.icons.DELETE_FOREVER,
                                on_click=lambda e, i=idx: self.remover_item(i),
                                icon_color=WARNING_COLOR,
                            )
                        ),
                    ]
                )
            )
        self.tabela.rows = linhas
        self.atualizar_lista_carrinho()
        self.page.update()

    def ajustar_quantidade(self, index: int, delta: float):
        if index >= len(self.carrinho):
            return
        self.carrinho[index]["quantidade"] = max(
            0.01, self.carrinho[index]["quantidade"] + delta
        )
        self.atualizar_tabela()
        self.atualizar_resumo()

    def remover_item(self, index: int):
        if index < len(self.carrinho):
            self.carrinho.pop(index)
            self.atualizar_tabela()
            self.atualizar_resumo()

    def atualizar_resumo(self):
        subtotal = sum(item["quantidade"] * item["preco_unitario"] for item in self.carrinho)
        try:
            desconto_valor = float((self.desconto_field.value or "0").replace(",", "."))
        except ValueError:
            desconto_valor = 0
        desconto_valor = max(0, min(desconto_valor, subtotal))
        total = subtotal - desconto_valor
        self.subtotal_text.value = format_currency(subtotal)
        self.desconto_text.value = format_currency(desconto_valor)
        self.total_text.value = format_currency(max(total, 0))
        self.page.update()

    def alterar_preco_ultimo(self):
        if not self.carrinho:
            return
        ultimo = self.carrinho[-1]
        dialog = ft.AlertDialog(modal=True)

        novo_preco = ft.TextField(
            label="Novo preço",
            value=str(ultimo["preco_unitario"]),
            autofocus=True,
        )

        def salvar(_):
            try:
                ultimo["preco_unitario"] = float(novo_preco.value)
            except ValueError:
                pass
            dialog.open = False
            self.page.update()
            self.atualizar_tabela()
            self.atualizar_resumo()

        def fechar(e=None):
            dialog.open = False
            self.page.update()

        dialog.title = ft.Text(f"Ajustar preço de {ultimo['nome']}")
        dialog.content = novo_preco
        dialog.actions = [
            ft.TextButton("Cancelar", on_click=fechar),
            ft.FilledButton("Salvar", on_click=salvar, style=PRIMARY_BUTTON_STYLE),
        ]

        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def finalizar_venda(self):
        if not self.carrinho:
            self._mostrar_alerta("Carrinho vazio.", color=WARNING_COLOR)
            return

        cliente_id = (
            int(self.cliente_dropdown.value) if self.cliente_dropdown.value else None
        )
        try:
            desconto_valor = float((self.desconto_field.value or "0").replace(",", "."))
        except ValueError:
            desconto_valor = 0
        subtotal = sum(item["quantidade"] * item["preco_unitario"] for item in self.carrinho)
        desconto_valor = max(0, min(desconto_valor, subtotal))
        pagamentos = [
            {
                "forma": self.pagamento_dropdown.value or "Dinheiro",
                "valor": subtotal - desconto_valor,
            }
        ]

        resultado = vendas_models.registrar_venda(
            self.carrinho,
            usuario_id=session.user.id,
            cliente_id=cliente_id,
            desconto_valor=desconto_valor,
            pagamentos=pagamentos,
            forma_principal=self.pagamento_dropdown.value,
        )
        caixa = caixa_models.caixa_aberto(session.user.id)
        if caixa:
            caixa_models.registrar_movimento(
                caixa["id"],
                tipo="venda",
                valor=resultado["total"],
                forma_pagamento=pagamentos[0]["forma"],
                venda_id=resultado["id"],
                descricao=f"Venda {resultado['codigo']}",
            )
        self.ultima_venda = resultado
        self.carrinho = []
        self.atualizar_tabela()
        self.atualizar_resumo()
        self.atualizar_ultima_venda_texto()
        self.ocultar_sugestoes()
        self._mostrar_alerta("Venda registrada com sucesso!", color=SUCCESS_COLOR)

    def atualizar_ultima_venda_texto(self):
        if not self.ultima_venda:
            self.ultima_text.value = "Nenhuma venda ainda."
        else:
            timestamp = self.ultima_venda.get("criado_em")
            hora = ""
            if timestamp:
                try:
                    hora = datetime.fromisoformat(timestamp).strftime("%d/%m %H:%M")
                except ValueError:
                    hora = timestamp
            itens_detalhe = "\n".join(
                [
                    f"- {item['nome']} x{item['quantidade']} = {format_currency(item['quantidade'] * item['preco_unitario'])}"
                    for item in self.ultima_venda["itens"]
                ]
            )
            self.ultima_text.value = (
                f"Venda {self.ultima_venda['codigo']}\n"
                f"Total: {format_currency(self.ultima_venda['total'])}\n"
                f"Hora: {hora}\nItens:\n{itens_detalhe}"
            )
        self.page.update()

    def limpar_carrinho(self):
        self.carrinho = []
        self.atualizar_tabela()
        self.atualizar_resumo()

    def registrar_pagamento_caixa(self, _=None):
        caixa = caixa_models.caixa_aberto(session.user.id)
        if not caixa:
            self._mostrar_alerta(
                "Nenhum caixa aberto para registrar a saída.", color=WARNING_COLOR
            )
            return

        try:
            valor = float((self.saida_valor_field.value or "0").replace(",", "."))
        except ValueError:
            valor = 0

        descricao = (self.saida_descricao_field.value or "").strip()

        if valor <= 0:
            self._mostrar_alerta(
                "Informe um valor maior que zero para registrar o pagamento.",
                color=WARNING_COLOR,
            )
            return
        if not descricao:
            self._mostrar_alerta(
                "Descreva o motivo da saída do caixa.", color=WARNING_COLOR
            )
            return

        caixa_models.registrar_movimento(
            caixa["id"],
            tipo="saida_caixa",
            valor=-abs(valor),
            forma_pagamento="Dinheiro",
            descricao=descricao,
        )
        self.saida_valor_field.value = "0"
        self.saida_descricao_field.value = ""
        self.page.update()
        self._mostrar_alerta(
            "Pagamento em dinheiro do caixa registrado.", color=SUCCESS_COLOR
        )

    def registrar_perda(self, _=None):
        caixa = caixa_models.caixa_aberto(session.user.id)
        if not caixa:
            self._mostrar_alerta(
                "Nenhum caixa aberto para registrar perdas.", color=WARNING_COLOR
            )
            return

        try:
            valor = float((self.perda_valor_field.value or "0").replace(",", "."))
        except ValueError:
            valor = 0

        descricao = (self.perda_descricao_field.value or "").strip()

        if valor <= 0:
            self._mostrar_alerta(
                "Informe um valor maior que zero para registrar a perda.",
                color=WARNING_COLOR,
            )
            return
        if not descricao:
            self._mostrar_alerta(
                "Explique o motivo da perda (extravio, dano, doação...).",
                color=WARNING_COLOR,
            )
            return

        caixa_models.registrar_movimento(
            caixa["id"],
            tipo="perda",
            valor=-abs(valor),
            forma_pagamento="Dinheiro",
            descricao=descricao,
        )
        self.perda_valor_field.value = "0"
        self.perda_descricao_field.value = ""
        self.page.update()
        self._mostrar_alerta("Perda registrada no caixa.", color=SUCCESS_COLOR)

    def atalhos(self, e: ft.KeyboardEvent):
        key = (e.key or "").replace(" ", "").upper()
        if key == "F2":
            self.busca_field.focus()
        elif key == "F3":
            self.adicionar_item()
        elif key == "F4":
            self.quantidade_field.focus()
        elif key == "F5":
            self.alterar_preco_ultimo()
        elif key == "F6":
            self.remover_item(len(self.carrinho) - 1)
        elif key == "F7":
            self.cliente_dropdown.focus()
        elif key == "F8":
            self.finalizar_venda()
        elif key == "F9":
            self.pagamento_dropdown.focus()
        elif key == "F10":
            self.desconto_field.focus()
        elif key == "F11":
            self.on_back("/dashboard")
        elif key in ("ARROWDOWN", "DOWN"):
            self.mover_sugestao(1)
        elif key in ("ARROWUP", "UP"):
            self.mover_sugestao(-1)
        elif key in ("ENTER", "NUMPADENTER"):
            self._confirmar_entrada()

    def build_view(self) -> ft.View:
        cabecalho = ft.Row(
            controls=[
                ft.Text("PDV / Caixa", size=26, weight=ft.FontWeight.BOLD),
                ft.FilledButton(
                    "Voltar (F11)",
                    icon=ft.icons.ARROW_BACK,
                    on_click=lambda e: self.on_back("/dashboard"),
                    style=PRIMARY_BUTTON_STYLE,
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        captura = ft.Container(
            bgcolor=SURFACE,
            border_radius=12,
            padding=12,
            content=ft.Column(
                controls=[
                    ft.Text("Captura rápida (F2-F6)", color="white70"),
                    ft.Row(
                        controls=[
                            self.busca_field,
                            self.quantidade_field,
                            ft.FilledButton(
                                "Adicionar (F3)",
                                icon=ft.icons.ADD_SHOPPING_CART,
                                on_click=lambda e: self.adicionar_item(),
                                style=PRIMARY_BUTTON_STYLE,
                            ),
                        ],
                        spacing=8,
                    ),
                    self.sugestoes_container,
                ],
                spacing=6,
            ),
        )

        pagamentos = ft.Container(
            bgcolor=SURFACE,
            border_radius=12,
            padding=12,
            content=ft.Column(
                controls=[
                    ft.Text("Cliente e pagamento", color="white70"),
                    ft.Column(
                        controls=[
                            self.cliente_dropdown,
                            self.pagamento_dropdown,
                            self.desconto_field,
                        ],
                        spacing=8,
                    ),
                    ft.Row(
                        controls=[
                            ft.FilledButton(
                                "Finalizar venda (F8)",
                                icon=ft.icons.CHECK_CIRCLE,
                                on_click=lambda e: self.finalizar_venda(),
                                style=SECONDARY_BUTTON_STYLE,
                            ),
                            ft.TextButton(
                                "Limpar carrinho",
                                on_click=lambda e: self.limpar_carrinho(),
                            ),
                        ],
                        spacing=8,
                    ),
                ],
                spacing=10,
            ),
        )

        pagamentos_caixa = ft.Container(
            bgcolor=SURFACE,
            border_radius=12,
            padding=12,
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Pagamentos com dinheiro do caixa",
                        color="white70",
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "Registre saídas pagas diretamente do caixa com uma breve descrição.",
                        color="white60",
                        size=12,
                    ),
                    ft.Row(
                        controls=[
                            self.saida_valor_field,
                            ft.FilledButton(
                                "Registrar saída",
                                icon=ft.icons.SAVINGS,
                                style=PRIMARY_BUTTON_STYLE,
                                on_click=self.registrar_pagamento_caixa,
                            ),
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.saida_descricao_field,
                ],
                spacing=8,
            ),
        )

        perdas_caixa = ft.Container(
            bgcolor=SURFACE,
            border_radius=12,
            padding=12,
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Perdas", color="white70", weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        "Registre produtos extraviados, danificados ou doados para que entrem no relatório.",
                        color="white60",
                        size=12,
                    ),
                    ft.Row(
                        controls=[
                            self.perda_valor_field,
                            ft.FilledButton(
                                "Registrar perda",
                                icon=ft.icons.REMOVE_SHOPPING_CART,
                                style=PRIMARY_BUTTON_STYLE,
                                on_click=self.registrar_perda,
                            ),
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    self.perda_descricao_field,
                ],
                spacing=8,
            ),
        )

        resumo = ft.Container(
            bgcolor=SURFACE,
            border_radius=12,
            padding=12,
            content=ft.Column(
                controls=[
                    ft.Text("Resumo", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row(
                        controls=[ft.Text("Subtotal", color="white54"), self.subtotal_text],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Row(
                        controls=[ft.Text("Desconto", color="white54"), self.desconto_text],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Divider(),
                    ft.Row(
                        controls=[
                            ft.Text("TOTAL", size=22, weight=ft.FontWeight.BOLD),
                            self.total_text,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                spacing=6,
            ),
        )

        ultima = ft.Container(
            bgcolor=SURFACE,
            border_radius=12,
            padding=12,
            content=ft.Column(
                controls=[ft.Text("Última venda", weight=ft.FontWeight.BOLD), self.ultima_text],
                spacing=6,
            ),
        )

        tabela_container = ft.Container(
            bgcolor=SURFACE,
            border_radius=12,
            padding=10,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[ft.Text("Itens da venda", weight=ft.FontWeight.BOLD)],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Container(
                        height=360,
                        content=ft.Column(
                            controls=[self.tabela],
                            scroll=ft.ScrollMode.AUTO,
                            expand=True,
                        ),
                    ),
                ],
                spacing=6,
                expand=True,
            ),
        )

        layout = ft.ResponsiveRow(
            controls=[
                ft.Container(
                    ft.Column([captura, tabela_container], spacing=12),
                    col={"xs": 12, "lg": 8},
                ),
                ft.Container(
                    ft.Column(
                        [pagamentos, resumo, ultima, pagamentos_caixa, perdas_caixa],
                        spacing=12,
                    ),
                    col={"xs": 12, "lg": 4},
                ),
            ],
            spacing=12,
            run_spacing=12,
        )

        self.page.on_keyboard_event = self.atalhos
        return ft.View(
            "/pdv",
            controls=[ft.Container(ft.Column([cabecalho, layout], spacing=14), expand=True)],
            scroll=ft.ScrollMode.AUTO,
        )

    def _confirmar_entrada(self):
        if self.sugestoes_dados:
            self.aplicar_sugestao_atual()
        else:
            self.adicionar_item()


def build_pdv_view(page: ft.Page, on_back):
    if not can_access("pdv"):
        return ft.View(
            "/pdv",
            controls=[ft.Text("Você não tem permissão para o PDV.", color="red")],
        )
    controller = PDVController(page, on_back)
    return controller.build_view()


__all__ = ["build_pdv_view"]
