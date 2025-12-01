import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJECT_DIR = os.path.join(ROOT_DIR, "meu_sistema_pdv")
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from APP.ui.vendas_ui import PDVController


class DummyEvent:
    def __init__(self, key: str | None):
        self.key = key


class PDVAtalhoBuscaTests(unittest.TestCase):
    def _build_controller(self):
        ctrl = object.__new__(PDVController)
        ctrl.mover_sugestao = MagicMock()
        ctrl._confirmar_entrada = MagicMock()
        ctrl.ocultar_sugestoes = MagicMock()
        return ctrl

    def test_on_change_skip_when_text_unchanged(self):
        ctrl = self._build_controller()
        ctrl.sugestoes_container = SimpleNamespace(visible=False)
        ctrl.page = MagicMock()
        ctrl.busca_field = SimpleNamespace(value="cafe")
        ctrl._ultimo_texto_busca = "cafe"

        with patch("APP.ui.vendas_ui.produtos_models.buscar_sugestoes") as buscar:
            ctrl.atualizar_sugestoes()

        buscar.assert_not_called()

    def test_arrow_down_moves_to_next_suggestion(self):
        ctrl = self._build_controller()

        ctrl._atalho_busca(DummyEvent("Arrow Down"))

        ctrl.mover_sugestao.assert_called_once_with(1)
        ctrl._confirmar_entrada.assert_not_called()
        ctrl.ocultar_sugestoes.assert_not_called()

    def test_arrow_up_moves_to_previous_suggestion(self):
        ctrl = self._build_controller()

        ctrl._atalho_busca(DummyEvent("Arrow Up"))

        ctrl.mover_sugestao.assert_called_once_with(-1)
        ctrl._confirmar_entrada.assert_not_called()
        ctrl.ocultar_sugestoes.assert_not_called()

    def test_enter_confirms_current_suggestion(self):
        ctrl = self._build_controller()

        ctrl._atalho_busca(DummyEvent("Enter"))

        ctrl._confirmar_entrada.assert_called_once_with()
        ctrl.mover_sugestao.assert_not_called()
        ctrl.ocultar_sugestoes.assert_not_called()

    def test_escape_hides_suggestions(self):
        ctrl = self._build_controller()

        ctrl._atalho_busca(DummyEvent("Esc"))

        ctrl.ocultar_sugestoes.assert_called_once_with()
        ctrl.mover_sugestao.assert_not_called()
        ctrl._confirmar_entrada.assert_not_called()

    def test_unhandled_key_does_nothing(self):
        ctrl = self._build_controller()

        ctrl._atalho_busca(DummyEvent("Space"))

        ctrl.mover_sugestao.assert_not_called()
        ctrl._confirmar_entrada.assert_not_called()
        ctrl.ocultar_sugestoes.assert_not_called()


class PDVSugestaoSelecionadaTests(unittest.TestCase):
    def test_selecionar_sugestao_adiciona_item(self):
        ctrl = object.__new__(PDVController)
        ctrl.busca_field = SimpleNamespace(value="")
        ctrl.ocultar_sugestoes = MagicMock()
        ctrl.adicionar_item = MagicMock()

        produto = {"codigo_barras": "123", "nome": "Café"}

        ctrl.selecionar_sugestao(produto)

        self.assertEqual(ctrl.busca_field.value, "123")
        ctrl.ocultar_sugestoes.assert_called_once_with()
        ctrl.adicionar_item.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
