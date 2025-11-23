from __future__ import annotations

from datetime import date
from pathlib import Path

import flet as ft

from APP.core.config import get_config
from APP.core.logger import get_logger
from APP.core.security import can_access
from APP.core.utils import format_currency
from APP.models import produtos_models, vendas_models

from .style import CONTROL_STATE, PRIMARY_COLOR, SURFACE, TEXT_MUTED

PRIMARY_BUTTON_STYLE = ft.ButtonStyle(
    bgcolor={CONTROL_STATE.DEFAULT: PRIMARY_COLOR},
    color={CONTROL_STATE.DEFAULT: "white"},
)

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover
    A4 = None
    canvas = None

logger = get_logger()


class RelatoriosView:
    def __init__(self, page: ft.Page):
        hoje = date.today().isoformat()
        self.page = page
        self.inicio = ft.TextField(label="Data inicial (YYYY-MM-DD)", value=hoje)
        self.fim = ft.TextField(label="Data final (YYYY-MM-DD)", value=hoje)
        self.total_text = ft.Text("R$ 0,00", size=26, weight=ft.FontWeight.BOLD)
        self.qtd_text = ft.Text("0", size=22)
        self.descontos_text = ft.Text("R$ 0,00", size=22)
        self.pagamentos_list = ft.Column()
        self.top_produtos_list = ft.Column()
        self.estoque_baixo = ft.Column()
        self.validade_list = ft.Column()
        self.carregar()

    def _range(self):
        inicio_val = (self.inicio.value or "").strip() or date.today().isoformat()
        fim_val = (self.fim.value or "").strip() or inicio_val
        inicio_iso = f"{inicio_val}T00:00:00"
        fim_iso = f"{fim_val}T23:59:59"
        return inicio_iso, fim_iso

    def carregar(self):
        inicio, fim = self._range()
        total = vendas_models.total_vendas_periodo(inicio, fim)
        qtd = vendas_models.quantidade_vendas_periodo(inicio, fim)
        descontos = vendas_models.total_descontos_periodo(inicio, fim)
        pagamentos = vendas_models.pagamentos_por_periodo(inicio, fim)
        top_produtos = vendas_models.produtos_mais_vendidos(inicio, fim, limite=5)
        estoque_baixo = produtos_models.produtos_estoque_baixo()
        validade = produtos_models.produtos_proximos_validade()

        self.total_text.value = format_currency(total)
        self.qtd_text.value = str(qtd)
        self.descontos_text.value = format_currency(descontos)
        self.pagamentos_list.controls = [
            ft.Text(f"{p['forma_pagamento']}: {format_currency(p['total'])}")
            for p in pagamentos
        ] or [ft.Text("Sem dados.", color=TEXT_MUTED)]
        self.top_produtos_list.controls = [
            ft.Text(f"{p['nome']} - {p['quantidade']} un.")
            for p in top_produtos
        ] or [ft.Text("Sem vendas.", color=TEXT_MUTED)]
        self.estoque_baixo.controls = [
            ft.Text(f"{p['nome']} ({p['estoque']} un.)", color="orange")
            for p in estoque_baixo
        ] or [ft.Text("Nenhum produto crítico.", color=TEXT_MUTED)]
        self.validade_list.controls = [
            ft.Text(f"{p['nome']} - {p['data_validade']}", color="orange")
            for p in validade
        ] or [ft.Text("Sem vencimentos próximos.", color=TEXT_MUTED)]
        self.page.update()

    def exportar_pdf(self):
        if not canvas:
            self.page.snack_bar = ft.SnackBar(
                ft.Text("Biblioteca reportlab não instalada."), bgcolor="red"
            )
            self.page.snack_bar.open = True
            self.page.update()
            return
        cfg = get_config()
        destino = Path(cfg.backup_dir) / f"relatorio_{date.today().isoformat()}.pdf"
        inicio, fim = self._range()
        pagamentos = vendas_models.pagamentos_por_periodo(inicio, fim)
        top_produtos = vendas_models.produtos_mais_vendidos(inicio, fim, limite=5)
        c = canvas.Canvas(str(destino), pagesize=A4)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 800, f"Relatório de vendas {inicio} a {fim}")
        c.setFont("Helvetica", 12)
        c.drawString(50, 770, f"Total: {self.total_text.value}")
        c.drawString(50, 750, f"Quantidade de vendas: {self.qtd_text.value}")
        c.drawString(50, 720, "Pagamentos:")
        y = 700
        for pag in pagamentos:
            c.drawString(60, y, f"{pag['forma_pagamento']}: {format_currency(pag['total'])}")
            y -= 18
        y -= 10
        c.drawString(50, y, "Top produtos:")
        y -= 20
        for prod in top_produtos:
            c.drawString(60, y, f"{prod['nome']} - {prod['quantidade']} un.")
            y -= 18
        c.save()
        logger.info("Relatório exportado para %s", destino)
        self.page.snack_bar = ft.SnackBar(
            ft.Text(f"Relatório salvo em {destino}"), bgcolor=PRIMARY_COLOR
        )
        self.page.snack_bar.open = True
        self.page.update()

    def build_view(self) -> ft.View:
        if not can_access("relatorios"):
            return ft.View(
                "/relatorios",
                controls=[ft.Text("Usuário sem permissão para relatórios.", color="red")],
            )
        filtros = ft.ResponsiveRow(
            controls=[
                ft.Container(self.inicio, col={"sm": 12, "md": 4}),
                ft.Container(self.fim, col={"sm": 12, "md": 4}),
                ft.Container(
                    ft.FilledButton(
                        "Atualizar",
                        icon=ft.icons.REFRESH,
                        on_click=lambda e: self.carregar(),
                        style=PRIMARY_BUTTON_STYLE,
                    ),
                    col={"sm": 6, "md": 2},
                ),
                ft.Container(
                    ft.OutlinedButton(
                        "Exportar PDF",
                        icon=ft.icons.PICTURE_AS_PDF,
                        on_click=lambda e: self.exportar_pdf(),
                    ),
                    col={"sm": 6, "md": 2},
                ),
            ],
            spacing=10,
            run_spacing=10,
        )
        cards = ft.ResponsiveRow(
            controls=[
                ft.Container(
                    bgcolor=SURFACE,
                    border_radius=12,
                    padding=16,
                    content=ft.Column(
                        controls=[
                            ft.Text("Total no período"),
                            self.total_text,
                            ft.Text("Quantidade de vendas"),
                            self.qtd_text,
                            ft.Text("Descontos aplicados"),
                            self.descontos_text,
                        ]
                    ),
                    col={"sm": 12, "md": 6, "lg": 4},
                ),
                ft.Container(
                    bgcolor=SURFACE,
                    border_radius=12,
                    padding=16,
                    content=ft.Column(
                        controls=[ft.Text("Pagamentos"), self.pagamentos_list],
                        spacing=8,
                    ),
                    col={"sm": 12, "md": 6, "lg": 4},
                ),
                ft.Container(
                    bgcolor=SURFACE,
                    border_radius=12,
                    padding=16,
                    content=ft.Column(
                        controls=[ft.Text("Produtos mais vendidos"), self.top_produtos_list],
                        spacing=12,
                    ),
                    col={"sm": 12, "md": 6, "lg": 4},
                ),
                ft.Container(
                    bgcolor=SURFACE,
                    border_radius=12,
                    padding=16,
                    content=ft.Column(
                        controls=[
                            ft.Text("Estoque baixo"),
                            self.estoque_baixo,
                            ft.Divider(),
                            ft.Text("Validades próximas"),
                            self.validade_list,
                        ],
                        spacing=12,
                    ),
                    col={"sm": 12, "md": 6, "lg": 4},
                ),
            ],
            spacing=12,
            run_spacing=12,
        )
        return ft.View(
            "/relatorios",
            controls=[
                ft.Column(
                    controls=[
                        ft.Text("Relatórios e Indicadores", size=24, weight=ft.FontWeight.BOLD),
                        filtros,
                        cards,
                    ],
                    spacing=16,
                )
            ],
            scroll=ft.ScrollMode.AUTO,
        )


def build_relatorios_view(page: ft.Page):
    controller = RelatoriosView(page)
    return controller.build_view()


__all__ = ["build_relatorios_view"]
