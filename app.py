"""
Sistema Completo de Empréstimo de Ferramentas - Terminal User Interface (TUI)
Desenvolvido com Python, Textual e SQLite.

Ponto de entrada principal da aplicação.
"""

import os
import sys

from textual.app import App
from textual.reactive import reactive
from typing import Optional, Dict, Any

import database
import auth
from screens import MainMenuScreen


class FerramentasApp(App):
    """Aplicação Principal Textual para Empréstimo de Ferramentas."""

    CSS_PATH = "styles.tcss"
    TITLE = "🛠️ FerramentaLivre - Sistema de Empréstimo de Ferramentas"
    SUB_TITLE = "Interface TUI em Terminal"

    # Estado reativo do usuário autenticado no sistema (None = Visitante)
    current_user: reactive[Optional[Dict[str, Any]]] = reactive(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Caminhos dos arquivos de persistência locais
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(base_dir, "ferramentas.db")
        self.login_path = os.path.join(base_dir, "login.json")

    def on_mount(self) -> None:
        """Inicializa banco de dados, recupera sessão se houver e exibe o menu inicial."""
        # 1. Garante que as tabelas SQLite existam
        try:
            database.init_db(self.db_path, seed=True)
        except Exception as e:
            self.notify(f"Erro ao inicializar o banco de dados: {str(e)}", severity="error", timeout=6)

        # 2. Verifica existência e integridade do arquivo login.json
        saved_user = auth.get_saved_session(login_path=self.login_path, db_path=self.db_path)
        if saved_user:
            self.current_user = saved_user
            self.notify(
                f"Sessão restaurada! Olá, {saved_user['username']}.",
                title="Sessão Ativa",
                severity="information",
                timeout=4
            )
        else:
            self.current_user = None

        # 3. Abre a tela inicial com o Menu Principal
        self.push_screen(MainMenuScreen())


if __name__ == "__main__":
    app = FerramentasApp()
    app.run()
