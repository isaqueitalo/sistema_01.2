from __future__ import annotations

import flet as ft

# Compatibilidade entre versões do Flet
if hasattr(ft, "ControlState"):
    CONTROL_STATE = ft.ControlState
elif hasattr(ft, "MaterialState"):
    CONTROL_STATE = ft.MaterialState
else:
    # Fallback mínimo para versões legadas, garantindo que os mapeamentos de estilo
    # continuem funcionando mesmo sem enum de estado exposto pelo Flet.
    class _ControlStateFallback:
        DEFAULT = "default"

    CONTROL_STATE = _ControlStateFallback

PRIMARY_COLOR = "#0EA5E9"
SECONDARY_COLOR = "#6366F1"
SUCCESS_COLOR = "#22C55E"
WARNING_COLOR = "#F59E0B"
ERROR_COLOR = "#EF4444"
BACKGROUND = "#0F172A"
SURFACE = "#1E293B"
TEXT_MUTED = "#94A3B8"


def apply_theme(page: ft.Page) -> None:
    page.theme_mode = ft.ThemeMode.DARK
    page.title = "Meu Sistema PDV"
    page.padding = 20
    page.bgcolor = BACKGROUND
    page.update()


def build_card(title: str, value: str, icon: str, color: str = PRIMARY_COLOR) -> ft.Container:
    return ft.Container(
        bgcolor=SURFACE,
        border_radius=12,
        padding=16,
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(icon, color=color, size=32),
                        ft.Text(title, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Text(value, size=28, weight=ft.FontWeight.BOLD, color="white"),
            ],
            spacing=10,
        ),
    )


def action_button(label: str, icon: str, on_click) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        text=label,
        icon=icon,
        style=ft.ButtonStyle(
            bgcolor={CONTROL_STATE.DEFAULT: PRIMARY_COLOR},
            color={CONTROL_STATE.DEFAULT: "white"},
            shape={CONTROL_STATE.DEFAULT: ft.RoundedRectangleBorder(radius=12)},
        ),
        on_click=on_click,
    )


__all__ = [
    "apply_theme",
    "build_card",
    "action_button",
    "PRIMARY_COLOR",
    "SECONDARY_COLOR",
    "SUCCESS_COLOR",
    "WARNING_COLOR",
    "ERROR_COLOR",
    "SURFACE",
    "TEXT_MUTED",
    "CONTROL_STATE",
]
