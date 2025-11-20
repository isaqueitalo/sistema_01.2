from __future__ import annotations

from datetime import date, datetime

import flet as ft

from APP.core.security import can_access
from APP.core.utils import format_currency
from APP.models import vendas_models

from .style import SURFACE


def build_pedidos_view(page: ft.Page) -> ft.View:
    if not can_access("relatorios"):
        return ft.View(
            "/pedidos",
            controls=[ft.Text("Usuário sem permissão para visualizar pedidos.", color="red")],
        )

    data_field = ft.TextField(
        label="Data",
        value=date.today().isoformat(),
        read_only=True,
        expand=True,
    )
    cards_column = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True, spacing=12)

    def carregar(_=None):
        selecionada = data_field.value or date.today().isoformat()
        inicio = f"{selecionada}T00:00:00"
        fim = f"{selecionada}T23:59:59"
        vendas = vendas_models.vendas_por_periodo(inicio, fim)
        cards = []
        for venda in vendas:
            itens = vendas_models.itens_da_venda(venda["id"])
            itens_texto = "\n".join(
                [
                    f"- {item['nome']} x{item['quantidade']} = {format_currency(item['total_item'])}"
                    for item in itens
                ]
            )
            hora = venda["criado_em"] or "-"
            try:
                hora = datetime.fromisoformat(hora).strftime("%d/%m %H:%M")
            except Exception:
                pass
            desconto_valor = float(venda["desconto_percentual"] or 0)
            cards.append(
                ft.Container(
                    bgcolor=SURFACE,
                    border_radius=12,
                    padding=12,
                    content=ft.Column(
                        controls=[
                            ft.Text(f"Pedido {venda['codigo']} • {hora}", weight=ft.FontWeight.BOLD),
                            ft.Text(f"Cliente: {venda['cliente'] or 'Consumidor Final'}"),
                            ft.Text(f"Vendedor: {venda['vendedor'] or '-'}"),
                            ft.Text(f"Total bruto: {format_currency(venda['total_bruto'])}"),
                            ft.Text(f"Desconto: {format_currency(desconto_valor)}"),
                            ft.Text(f"Total líquido: {format_currency(venda['total_liquido'])}"),
                            ft.Text(itens_texto or "Sem itens."),
                        ],
                        spacing=4,
                    ),
                )
            )
        cards_column.controls = cards or [ft.Text("Nenhuma venda nesse dia.", color="white70")]
        page.update()

    carregar()

    def ao_escolher_data(e: ft.ControlEvent):
        valor = e.control.value
        if valor:
            data_field.value = valor
        carregar()

    date_picker = ft.DatePicker(on_change=ao_escolher_data)
    page.overlay.append(date_picker)

    def abrir_calendario(_):
        date_picker.pick_date()

    filtros = ft.Row(
        controls=[
            data_field,
            ft.IconButton(ft.icons.CALENDAR_MONTH, on_click=abrir_calendario),
            ft.ElevatedButton("Atualizar", on_click=carregar),
        ],
        spacing=10,
    )

    return ft.View(
        "/pedidos",
        controls=[
            ft.Column(
                controls=[
                    ft.Text("Pedidos do Dia", size=26, weight=ft.FontWeight.BOLD),
                    filtros,
                    cards_column,
                ],
                spacing=16,
            )
        ],
        scroll=ft.ScrollMode.AUTO,
    )


__all__ = ["build_pedidos_view"]
