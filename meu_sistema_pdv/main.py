from __future__ import annotations

import flet as ft

from APP.core.config import get_config
from APP.core.database import initialize_database
from APP.core.logger import get_logger
from APP.core.session import session
from APP.ui import (
    build_caixa_view,
    build_config_view,
    build_dashboard_view,
    build_login_view,
    build_pedidos_view,
    build_pdv_view,
    build_produtos_view,
    build_relatorios_view,
    build_usuarios_view,
    build_logs_view,
)
from APP.ui.style import apply_theme


def main(page: ft.Page):
    cfg = get_config()
    apply_theme(page)
    initialize_database()
    logger = get_logger()
    logger.info("Aplicação iniciada.")
    page.title = cfg.app_name
    page.window.width = 1200
    page.window.height = 780
    page.window.maximizable = True

    def navegar(route: str):
        if not session.is_authenticated() and route != "/":
            page.go("/")
            return
        page.go(route)

    def fazer_logout():
        session.logout()
        page.go("/")

    def route_change(e: ft.RouteChangeEvent):
        page.views.clear()
        page.on_keyboard_event = None
        if page.route == "/":
            page.views.append(
                build_login_view(
                    page,
                    on_success=lambda: page.go("/dashboard"),
                )
            )
        elif not session.is_authenticated():
            page.go("/")
            return
        elif page.route == "/dashboard":
            page.views.append(
                build_dashboard_view(
                    page,
                    on_navigate=navegar,
                    on_logout=fazer_logout,
                )
            )
        elif page.route == "/pdv":
            page.views.append(build_pdv_view(page, on_back=navegar))
        elif page.route == "/produtos":
            page.views.append(build_produtos_view(page))
        elif page.route == "/usuarios":
            page.views.append(build_usuarios_view(page))
        elif page.route == "/relatorios":
            page.views.append(build_relatorios_view(page))
        elif page.route == "/caixa":
            page.views.append(build_caixa_view(page))
        elif page.route == "/logs":
            page.views.append(build_logs_view(page))
        elif page.route == "/config":
            page.views.append(build_config_view(page))
        elif page.route == "/pedidos":
            page.views.append(build_pedidos_view(page))
        else:
            page.views.append(
                ft.View(
                    page.route,
                    controls=[ft.Text("Página não encontrada.", color="red")],
                )
            )
        page.update()

    def view_pop(e: ft.ViewPopEvent):
        page.views.pop()
        if page.views:
            page.go(page.views[-1].route)

    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go(page.route if session.is_authenticated() else "/")


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
