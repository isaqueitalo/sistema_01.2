from __future__ import annotations

import flet as ft

from APP.core.security import can_access
from APP.core.session import session
from APP.core.utils import format_currency, hoje_intervalo, mes_atual_intervalo
from APP.models import produtos_models, vendas_models

from .style import (
    PRIMARY_COLOR,
    SECONDARY_COLOR,
    SUCCESS_COLOR,
    SURFACE,
    WARNING_COLOR,
    build_card,
)


def _coletar_resumos():
    dia_inicio, dia_fim = hoje_intervalo()
    mes_inicio, mes_fim = mes_atual_intervalo()
    total_dia = vendas_models.total_vendas_periodo(dia_inicio, dia_fim)
    total_mes = vendas_models.total_vendas_periodo(mes_inicio, mes_fim)
    qtd_baixo = len(produtos_models.produtos_estoque_baixo())
    qtd_validade = len(produtos_models.produtos_proximos_validade())
    mais_vendido = vendas_models.produtos_mais_vendidos(dia_inicio, dia_fim, limite=1)
    top = mais_vendido[0]["nome"] if mais_vendido else "Sem vendas hoje"
    return total_dia, total_mes, qtd_baixo, qtd_validade, top


def build_dashboard_view(page: ft.Page, on_navigate, on_logout) -> ft.View:
    total_dia, total_mes, qtd_baixo, qtd_validade, top = _coletar_resumos()

    cards = [
        build_card("Vendas do dia", format_currency(total_dia), ft.icons.CALENDAR_TODAY),
        build_card(
            "Vendas do mês",
            format_currency(total_mes),
            ft.icons.CALENDAR_MONTH,
            SECONDARY_COLOR,
        ),
        build_card(
            "Estoque baixo",
            str(qtd_baixo),
            ft.icons.WARNING_AMBER,
            WARNING_COLOR,
        ),
        build_card(
            "Validades próximas",
            str(qtd_validade),
            ft.icons.EVENT_AVAILABLE,
            SUCCESS_COLOR,
        ),
    ]

    nav_itens = [
        ("Tela de Vendas", ft.icons.POINT_OF_SALE, "/pdv", "pdv"),
        ("Produtos", ft.icons.INVENTORY_2_ROUNDED, "/produtos", "produtos"),
        ("Usuários", ft.icons.PEOPLE, "/usuarios", "usuarios"),
        ("Relatórios", ft.icons.INSERT_CHART, "/relatorios", "relatorios"),
        ("Pedidos do dia", ft.icons.RECEIPT_LONG, "/pedidos", "relatorios"),
        ("Controle de Caixa", ft.icons.ATTACH_MONEY, "/caixa", "caixa"),
        ("Logs do sistema", ft.icons.LIST_ALT, "/logs", "logs"),
        ("Configurações", ft.icons.SETTINGS, "/config", "config"),
    ]

    botoes = []
    for titulo, icon, rota, secao in nav_itens:
        if not can_access(secao):
            continue
        botoes.append(
            ft.Container(
                bgcolor=SURFACE,
                border_radius=12,
                padding=14,
                on_click=lambda e, r=rota: on_navigate(r),
                content=ft.Column(
                    controls=[
                        ft.Icon(icon, color=PRIMARY_COLOR, size=28),
                        ft.Text(titulo, weight=ft.FontWeight.BOLD),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                ),
            )
        )

    if botoes:
        navegacao = ft.GridView(
            expand=1,
            runs_count=3,
            max_extent=260,
            child_aspect_ratio=1.6,
            spacing=12,
            run_spacing=12,
            controls=botoes,
        )
    else:
        navegacao = ft.Text(
            "Nenhum módulo disponível para seu perfil.", color="white70"
        )

    conteudo = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Text(
                        f"Bem-vindo, {session.user.nome}",
                        size=26,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.TextButton(
                        "Sair",
                        icon=ft.icons.LOGOUT,
                        on_click=lambda e: on_logout(),
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            ft.Text("Acessos rápidos", size=22, weight=ft.FontWeight.BOLD),
            navegacao,
            ft.Divider(),
            ft.Text("Resumo rápido", weight=ft.FontWeight.BOLD),
            ft.Row(cards, wrap=True, spacing=12, run_spacing=12),
            ft.Divider(),
            ft.Text(f"Produto destaque hoje: {top}", color="white"),
        ],
        spacing=20,
    )

    return ft.View(
        "/dashboard",
        controls=[ft.Container(conteudo, expand=True, padding=0)],
        vertical_alignment=ft.MainAxisAlignment.START,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        scroll=ft.ScrollMode.AUTO,
    )


__all__ = ["build_dashboard_view"]
