from .login_ui import build_login_view
from .dashboard_ui import build_dashboard_view
from .vendas_ui import build_pdv_view
from .produtos_ui import build_produtos_view
from .usuarios_ui import build_usuarios_view
from .relatorios_ui import build_relatorios_view
from .caixa_ui import build_caixa_view
from .logs_viewer import build_logs_view
from .config_ui import build_config_view
from .pedidos_ui import build_pedidos_view

__all__ = [
    "build_login_view",
    "build_dashboard_view",
    "build_pdv_view",
    "build_produtos_view",
    "build_usuarios_view",
    "build_relatorios_view",
    "build_caixa_view",
    "build_logs_view",
    "build_config_view",
    "build_pedidos_view",
]
