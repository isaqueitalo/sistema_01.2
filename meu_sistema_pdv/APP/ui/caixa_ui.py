from __future__ import annotations

from datetime import date

import flet as ft

from APP.core.security import can_access
from APP.core.session import session
from APP.core.utils import format_currency
from APP.models import caixa_models

from .style import PRIMARY_COLOR, SURFACE, WARNING_COLOR

PRIMARY_BUTTON_STYLE = ft.ButtonStyle(
    bgcolor={ft.MaterialState.DEFAULT: PRIMARY_COLOR},
    color={ft.MaterialState.DEFAULT: "white"},
)


class CaixaView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.valor_abertura = ft.TextField(
            label="Valor de abertura", keyboard_type=ft.KeyboardType.NUMBER
        )
        self.valor_fechamento = ft.TextField(
            label="Valor contado no fechamento", keyboard_type=ft.KeyboardType.NUMBER
        )
        self.rel_inicio = ft.TextField(label="Período inicial", value=date.today().isoformat())
        self.rel_fim = ft.TextField(label="Período final", value=date.today().isoformat())
        self.relatorio_list = ft.Column()
        self.formas_totais = ft.Column()
        self.atualizar_estado()

    def _toast(self, mensagem: str, cor: str = PRIMARY_COLOR):
        self.page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor=cor)
        self.page.snack_bar.open = True
        self.page.update()

    def atualizar_estado(self):
        self.caixa_atual = caixa_models.caixa_aberto(session.user.id)
        if self.caixa_atual:
            totais = caixa_models.total_por_forma(self.caixa_atual["id"])
            self.formas_totais.controls = [
                ft.Text(f"{t['forma_pagamento']}: {format_currency(t['total'])}")
                for t in totais
            ] or [ft.Text("Sem movimentos ainda.")]
        else:
            self.formas_totais.controls = [ft.Text("Nenhum caixa aberto.")]
        self.page.update()

    def abrir_caixa(self):
        if self.caixa_atual:
            self._toast("Já existe um caixa aberto.", WARNING_COLOR)
            return
        try:
            valor = float(self.valor_abertura.value or "0")
        except ValueError:
            valor = 0
        caixa_models.abrir_caixa(session.user.id, valor)
        self._toast("Caixa aberto!")
        self.atualizar_estado()

    def fechar_caixa(self):
        if not self.caixa_atual:
            self._toast("Não há caixa aberto.", WARNING_COLOR)
            return
        try:
            valor = float(self.valor_fechamento.value or "0")
        except ValueError:
            valor = 0
        caixa_models.fechar_caixa(self.caixa_atual["id"], valor)
        self._toast("Caixa fechado.")
        self.atualizar_estado()

    def carregar_relatorio(self):
        rel = caixa_models.relatorio_caixas(self.rel_inicio.value, self.rel_fim.value)
        self.relatorio_list.controls = [
            ft.Text(
                f"{item['codigo']} - Operador {item['operador']} - Status: {item['status']} - "
                f"Abertura: {item['aberto_em']}"
            )
            for item in rel
        ] or [ft.Text("Sem dados.")]
        self.page.update()

    def build_view(self) -> ft.View:
        if not can_access("caixa"):
            return ft.View("/caixa", controls=[ft.Text("Sem permissão.", color="red")])
        painel_atual = ft.Container(
            bgcolor=SURFACE,
            border_radius=12,
            padding=16,
            content=ft.Column(
                controls=[
                    ft.Text("Situação do caixa", weight=ft.FontWeight.BOLD),
                    ft.Text(
                        "Caixa aberto"
                        if self.caixa_atual
                        else "Nenhum caixa aberto",
                        color="white70",
                    ),
                    ft.Row(
                        controls=[
                            self.valor_abertura,
                            ft.FilledButton(
                                "Abrir caixa",
                                icon=ft.icons.LOCK_OPEN,
                                on_click=lambda e: self.abrir_caixa(),
                                style=PRIMARY_BUTTON_STYLE,
                            ),
                        ]
                    ),
                    ft.Row(
                        controls=[
                            self.valor_fechamento,
                            ft.FilledButton(
                                "Fechar caixa",
                                icon=ft.icons.LOCK,
                                on_click=lambda e: self.fechar_caixa(),
                                style=PRIMARY_BUTTON_STYLE,
                            ),
                        ]
                    ),
                    ft.Text("Totais por forma de pagamento"),
                    self.formas_totais,
                ],
                spacing=12,
            ),
        )
        relatorio = ft.Container(
            bgcolor=SURFACE,
            border_radius=12,
            padding=16,
            content=ft.Column(
                controls=[
                    ft.Text("Relatório de caixas"),
                    ft.Row(
                        controls=[
                            self.rel_inicio,
                            self.rel_fim,
                            ft.FilledButton(
                                "Consultar",
                                icon=ft.icons.SEARCH,
                                on_click=lambda e: self.carregar_relatorio(),
                                style=PRIMARY_BUTTON_STYLE,
                            ),
                        ],
                        spacing=12,
                    ),
                    self.relatorio_list,
                ],
                spacing=12,
            ),
        )
        return ft.View(
            "/caixa",
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Controle de Caixa", size=24, weight=ft.FontWeight.BOLD),
                        painel_atual,
                        relatorio,
                    ],
                    spacing=16,
                )
            ],
        )


def build_caixa_view(page: ft.Page):
    controller = CaixaView(page)
    return controller.build_view()


__all__ = ["build_caixa_view"]
