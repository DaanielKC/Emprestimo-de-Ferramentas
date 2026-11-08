"""
Telas e Componentes de Interface Textual (TUI) para o Sistema de Empréstimo de Ferramentas.
Implementa o fluxo de navegação, modais, formulários e listagens reativas.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from textual.app import ComposeResult
from textual.screen import Screen, ModalScreen
from textual.widgets import (
    Header,
    Footer,
    Button,
    Input,
    Label,
    Static,
    DataTable,
    TabbedContent,
    TabPane,
    Select,
)
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.binding import Binding

import database
import auth


# ==============================================================================
# MODAIS GENÉRICOS E DE DETALHES
# ==============================================================================

class ConfirmModal(ModalScreen[bool]):
    """Modal de confirmação genérica (ex: exclusão, logout)."""

    def __init__(self, title: str, message: str, confirm_label: str = "Confirmar", cancel_label: str = "Voltar / Cancelar"):
        super().__init__()
        self.modal_title = title
        self.message = message
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label(self.modal_title, classes="modal-title")
            yield Static(self.message, classes="modal-body")
            with Horizontal(classes="modal-buttons"):
                yield Button(self.cancel_label, variant="default", id="btn-cancel")
                yield Button(self.confirm_label, variant="error", id="btn-confirm")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-confirm":
            self.dismiss(True)
        else:
            self.dismiss(False)


class RequireLoginModal(ModalScreen[bool]):
    """Modal exibido quando um visitante tenta pegar uma ferramenta emprestada."""

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label("🔒 Autenticação Necessária", classes="modal-title")
            yield Static(
                "Para solicitar o empréstimo de uma ferramenta e visualizar o "
                "telefone de contato do proprietário, você precisa estar conectado à sua conta.\n\n"
                "Deseja fazer login ou criar um novo cadastro agora?",
                classes="modal-body"
            )
            with Horizontal(classes="modal-buttons"):
                yield Button("🔙 Voltar", variant="default", id="btn-back")
                yield Button("🔑 Fazer Login / Cadastrar", variant="success", id="btn-go-auth")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-go-auth":
            self.dismiss(True)
        else:
            self.dismiss(False)


class BorrowModal(ModalScreen[None]):
    """
    Modal de exibição do contato do proprietário para negociação de empréstimo.
    Exibido para usuários autenticados ao solicitar o empréstimo.
    """

    def __init__(self, tool: Dict[str, Any]):
        super().__init__()
        self.tool = tool

    def compose(self) -> ComposeResult:
        status_color = "green" if self.tool.get("status") == "Disponível" else "yellow"
        with Vertical(classes="modal-dialog"):
            yield Label("🤝 Negociar Empréstimo", classes="modal-title")
            yield Static(
                f"[bold cyan]{self.tool.get('name')}[/]\n"
                f"Proprietário: [bold]{self.tool.get('owner_name')}[/]\n"
                f"Status Atual: [{status_color} bold]{self.tool.get('status')}[/]\n\n"
                f"[italic]{self.tool.get('description')}[/]\n",
                classes="modal-body"
            )
            with Vertical(classes="modal-phone-box"):
                yield Label("📞 CONTATO DIRETO DO PROPRIETÁRIO:")
                yield Label(f"[bold]{self.tool.get('contact_phone')}[/]")
                yield Static(
                    "[dim]Ligue ou envie mensagem via WhatsApp para combinar o local e a devolução.[/]"
                )
            with Horizontal(classes="modal-buttons"):
                yield Button("Fechar / Voltar", variant="primary", id="btn-close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)


# ==============================================================================
# TELA DE AUTENTICAÇÃO (LOGIN / CADASTRO)
# ==============================================================================

class AuthScreen(Screen):
    """Tela com abas para realizar Login ou Cadastrar uma nova conta."""

    BINDINGS = [
        Binding("escape", "go_back", "Voltar"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="screen-container"):
            with Vertical(classes="form-container"):
                yield Label("🔐 Autenticação de Usuário", classes="screen-header-title")
                yield Label("Acesse sua conta existente ou cadastre-se gratuitamente:", classes="screen-header-desc")

                with TabbedContent():
                    with TabPane("🔑 Fazer Login", id="tab-login"):
                        yield Label("Nome de Usuário:", classes="form-label")
                        yield Input(placeholder="Digite seu usuário...", id="login-username", classes="form-input")

                        yield Label("Senha:", classes="form-label")
                        yield Input(placeholder="Digite sua senha...", password=True, id="login-password", classes="form-input")

                        with Horizontal(classes="form-buttons"):
                            yield Button("🔙 Voltar", variant="default", id="btn-login-back")
                            yield Button("Entrar", variant="success", id="btn-login-submit")

                    with TabPane("📝 Criar Nova Conta", id="tab-register"):
                        yield Label("Escolha um Nome de Usuário:", classes="form-label")
                        yield Input(placeholder="Ex: joaosilva", id="reg-username", classes="form-input")

                        yield Label("Escolha uma Senha (mín. 4 caracteres):", classes="form-label")
                        yield Input(placeholder="Digite a senha...", password=True, id="reg-password", classes="form-input")

                        yield Label("Confirme a Senha:", classes="form-label")
                        yield Input(placeholder="Repita a senha...", password=True, id="reg-confirm", classes="form-input")

                        with Horizontal(classes="form-buttons"):
                            yield Button("🔙 Voltar", variant="default", id="btn-reg-back")
                            yield Button("Criar Conta e Entrar", variant="primary", id="btn-reg-submit")

        yield Footer()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id in ("btn-login-back", "btn-reg-back"):
            self.action_go_back()
            return

        if button_id == "btn-login-submit":
            username = self.query_one("#login-username", Input).value
            password = self.query_one("#login-password", Input).value
            try:
                user = auth.authenticate(
                    username=username,
                    password=password,
                    login_path=self.app.login_path,
                    db_path=self.app.db_path
                )
                self.app.current_user = user
                self.app.notify(
                    f"Bem-vindo(a) de volta, {user['username']}!",
                    title="Login realizado com sucesso",
                    severity="information"
                )
                self.app.pop_screen()
            except ValueError as e:
                self.app.notify(str(e), title="Falha no Login", severity="error")

        elif button_id == "btn-reg-submit":
            username = self.query_one("#reg-username", Input).value
            password = self.query_one("#reg-password", Input).value
            confirm = self.query_one("#reg-confirm", Input).value
            try:
                user = auth.register(
                    username=username,
                    password=password,
                    confirm_password=confirm,
                    login_path=self.app.login_path,
                    db_path=self.app.db_path
                )
                self.app.current_user = user
                self.app.notify(
                    f"Conta criada com sucesso! Conectado como {user['username']}.",
                    title="Cadastro concluído",
                    severity="information"
                )
                self.app.pop_screen()
            except ValueError as e:
                self.app.notify(str(e), title="Falha no Cadastro", severity="error")


# ==============================================================================
# TELA DE LISTAGEM GERAL DE FERRAMENTAS
# ==============================================================================

class ToolListScreen(Screen):
    """Tela do catálogo completo de ferramentas, acessível a visitantes e logados."""

    BINDINGS = [
        Binding("escape", "go_back", "Voltar"),
        Binding("b", "borrow_selected", "Pegar Emprestado"),
        Binding("r", "refresh_list", "Recarregar"),
    ]

    selected_tool: reactive[Optional[Dict[str, Any]]] = reactive(None)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="screen-container"):
            yield Label("📋 Catálogo de Ferramentas Disponíveis", classes="screen-header-title")
            yield Label(
                "Selecione uma ferramenta da lista para ver os detalhes completos ou pegar emprestado:",
                classes="screen-header-desc"
            )

            with Horizontal(id="search-bar-container"):
                yield Input(placeholder="🔍 Pesquisar por nome ou descrição da ferramenta...", id="input-search")
                yield Button("Recarregar", variant="default", id="btn-refresh")

            yield DataTable(id="tools-table", cursor_type="row")

            with Vertical(id="details-panel"):
                yield Label("Detalhes da Ferramenta Selecionada:", classes="details-title")
                yield Static("Nenhuma ferramenta selecionada.", id="static-tool-details")

            with Horizontal(classes="action-bar"):
                yield Button("🔙 Voltar ao Menu", variant="default", id="btn-back")
                yield Button("🤝 Pegar Emprestado", variant="success", id="btn-borrow")

        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#tools-table", DataTable)
        table.add_columns("ID", "Nome da Ferramenta", "Status", "Proprietário", "Telefone", "Cadastrado em")
        self.load_tools()

    def load_tools(self, search_term: Optional[str] = None) -> None:
        table = self.query_one("#tools-table", DataTable)
        table.clear()
        tools = database.get_all_tools(search_term=search_term, db_path=self.app.db_path)

        for t in tools:
            status_text = f"[green]{t['status']}[/]" if t["status"] == "Disponível" else f"[yellow]{t['status']}[/]"
            phone_display = t["contact_phone"] if self.app.current_user else "[dim]🔒 Fazer Login[/]"
            table.add_row(
                str(t["id"]),
                t["name"],
                status_text,
                t["owner_name"],
                phone_display,
                t["created_at"],
                key=str(t["id"])
            )

        if tools:
            self.selected_tool = tools[0]
            self.update_details_panel(tools[0])
        else:
            self.selected_tool = None
            self.query_one("#static-tool-details", Static).update("[yellow]Nenhuma ferramenta encontrada.[/]")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "input-search":
            self.load_tools(search_term=event.value)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key and event.row_key.value:
            tool_id = int(event.row_key.value)
            tool = database.get_tool_by_id(tool_id, db_path=self.app.db_path)
            if tool:
                self.selected_tool = tool
                self.update_details_panel(tool)

    def update_details_panel(self, tool: Dict[str, Any]) -> None:
        status_color = "green" if tool["status"] == "Disponível" else "yellow"
        phone_info = (
            f"[bold green]{tool['contact_phone']}[/]"
            if self.app.current_user
            else "[italic yellow]Oculto para visitantes. Faça login para visualizar o telefone![/]"
        )

        details_text = (
            f"[bold cyan]{tool['name']}[/]  |  Status: [{status_color} bold]{tool['status']}[/]  |  "
            f"Proprietário: [bold]{tool['owner_name']}[/]\n"
            f"[bold]Contato:[/] {phone_info}\n"
            f"[bold]Descrição:[/] {tool['description']}\n"
            f"[dim]Cadastrado em: {tool['created_at']}[/]"
        )
        self.query_one("#static-tool-details", Static).update(details_text)

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_refresh_list(self) -> None:
        search_val = self.query_one("#input-search", Input).value
        self.load_tools(search_term=search_val)
        self.app.notify("Lista de ferramentas atualizada.", title="Atualizado")

    def action_borrow_selected(self) -> None:
        if not self.selected_tool:
            self.app.notify("Selecione uma ferramenta da lista primeiro.", severity="warning")
            return

        # Regra de negócio: Se não estiver logado, redireciona para Login/Cadastro
        if not self.app.current_user:
            def on_login_modal_result(wants_login: bool) -> None:
                if wants_login:
                    self.app.push_screen(AuthScreen(), callback=self.on_auth_completed)

            self.app.push_screen(RequireLoginModal(), callback=on_login_modal_result)
        else:
            # Usuário logado: exibe telefone de contato para negociação
            self.app.push_screen(BorrowModal(self.selected_tool))

    def on_auth_completed(self, *args) -> None:
        """Chamado após fechar a tela de autenticação para recarregar com novo status de login."""
        self.load_tools()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.action_go_back()
        elif event.button.id == "btn-refresh":
            self.action_refresh_list()
        elif event.button.id == "btn-borrow":
            self.action_borrow_selected()


# ==============================================================================
# TELA DE CADASTRO DE NOVA FERRAMENTA
# ==============================================================================

class AddToolScreen(Screen):
    """Formulário para cadastrar uma nova ferramenta (usuários logados)."""

    BINDINGS = [
        Binding("escape", "go_back", "Voltar"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="screen-container"):
            with Vertical(classes="form-container"):
                yield Label("➕ Cadastrar Nova Ferramenta", classes="screen-header-title")
                yield Label("Disponibilize suas ferramentas para outros usuários pegarem emprestado:", classes="screen-header-desc")

                yield Label("Nome da Ferramenta / Modelo:", classes="form-label")
                yield Input(placeholder="Ex: Furadeira de Impacto Bosch 650W", id="input-tool-name", classes="form-input")

                yield Label("Descrição e Acessórios Inclusos:", classes="form-label")
                yield Input(placeholder="Ex: Acompanha maleta, jogo de 5 brocas. Voltagem 110V.", id="input-tool-desc", classes="form-input")

                yield Label("Telefone de Contato (WhatsApp / Ligação):", classes="form-label")
                yield Input(placeholder="Ex: (11) 98765-4321", id="input-tool-phone", classes="form-input")

                with Horizontal(classes="form-buttons"):
                    yield Button("🔙 Voltar / Cancelar", variant="default", id="btn-cancel")
                    yield Button("💾 Cadastrar Ferramenta", variant="success", id="btn-save")

        yield Footer()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.action_go_back()
            return

        if event.button.id == "btn-save":
            name = self.query_one("#input-tool-name", Input).value.strip()
            desc = self.query_one("#input-tool-desc", Input).value.strip()
            phone = self.query_one("#input-tool-phone", Input).value.strip()

            if not name:
                self.app.notify("Por favor, preencha o nome da ferramenta.", severity="error")
                return
            if not desc:
                self.app.notify("Por favor, adicione uma breve descrição da ferramenta.", severity="error")
                return
            if not phone:
                self.app.notify("Por favor, informe um telefone de contato para empréstimos.", severity="error")
                return

            try:
                database.create_tool(
                    owner_id=self.app.current_user["id"],
                    name=name,
                    description=desc,
                    contact_phone=phone,
                    db_path=self.app.db_path
                )
                self.app.notify(f"Ferramenta '{name}' cadastrada com sucesso!", title="Sucesso", severity="information")
                self.app.pop_screen()
            except Exception as e:
                self.app.notify(f"Erro ao salvar ferramenta: {str(e)}", severity="error")


# ==============================================================================
# MODAL DE EDIÇÃO DE FERRAMENTA
# ==============================================================================

class EditToolModal(ModalScreen[bool]):
    """Modal de formulário para editar uma ferramenta existente."""

    def __init__(self, tool: Dict[str, Any]):
        super().__init__()
        self.tool = tool

    def compose(self) -> ComposeResult:
        with Vertical(classes="modal-dialog"):
            yield Label(f"✏️ Editar: {self.tool['name']}", classes="modal-title")

            yield Label("Nome:", classes="form-label")
            yield Input(value=self.tool["name"], id="edit-name", classes="form-input")

            yield Label("Descrição:", classes="form-label")
            yield Input(value=self.tool["description"], id="edit-desc", classes="form-input")

            yield Label("Telefone de Contato:", classes="form-label")
            yield Input(value=self.tool["contact_phone"], id="edit-phone", classes="form-input")

            yield Label("Status de Disponibilidade:", classes="form-label")
            status_options = [("Disponível", "Disponível"), ("Emprestado", "Emprestado")]
            yield Select(status_options, value=self.tool["status"], id="edit-status")

            with Horizontal(classes="modal-buttons"):
                yield Button("🔙 Cancelar", variant="default", id="btn-cancel")
                yield Button("💾 Salvar Alterações", variant="success", id="btn-save")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-cancel":
            self.dismiss(False)
            return

        if event.button.id == "btn-save":
            name = self.query_one("#edit-name", Input).value.strip()
            desc = self.query_one("#edit-desc", Input).value.strip()
            phone = self.query_one("#edit-phone", Input).value.strip()
            status = self.query_one("#edit-status", Select).value

            if not name or not desc or not phone:
                self.app.notify("Todos os campos devem ser preenchidos.", severity="error")
                return

            database.update_tool(
                tool_id=self.tool["id"],
                owner_id=self.app.current_user["id"],
                name=name,
                description=desc,
                contact_phone=phone,
                status=str(status),
                db_path=self.app.db_path
            )
            self.dismiss(True)


# ==============================================================================
# TELA DE FERRAMENTAS DO USUÁRIO ("MINHAS FERRAMENTAS")
# ==============================================================================

class MyToolsScreen(Screen):
    """Painel de gerenciamento das ferramentas cadastradas pelo usuário autenticado."""

    BINDINGS = [
        Binding("escape", "go_back", "Voltar"),
        Binding("e", "edit_selected", "Editar"),
        Binding("t", "toggle_status_selected", "Alternar Status"),
        Binding("d", "delete_selected", "Excluir"),
    ]

    selected_tool: reactive[Optional[Dict[str, Any]]] = reactive(None)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(classes="screen-container"):
            yield Label("🧰 Minhas Ferramentas Cadastradas", classes="screen-header-title")
            yield Label(
                "Gerencie suas ferramentas cadastradas, altere disponibilidade ou edite as informações:",
                classes="screen-header-desc"
            )

            yield DataTable(id="my-tools-table", cursor_type="row")

            with Vertical(id="details-panel"):
                yield Label("Ferramenta Selecionada:", classes="details-title")
                yield Static("Nenhuma ferramenta selecionada.", id="static-my-details")

            with Horizontal(classes="action-bar"):
                yield Button("🔙 Voltar ao Menu", variant="default", id="btn-back")
                yield Button("➕ Nova Ferramenta", variant="default", id="btn-new")
                yield Button("🔄 Alternar Status", variant="warning", id="btn-toggle")
                yield Button("✏️ Editar", variant="primary", id="btn-edit")
                yield Button("🗑️ Excluir", variant="error", id="btn-delete")

        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#my-tools-table", DataTable)
        table.add_columns("ID", "Nome da Ferramenta", "Status", "Telefone", "Cadastrado em")
        self.load_my_tools()

    def load_my_tools(self) -> None:
        table = self.query_one("#my-tools-table", DataTable)
        table.clear()
        tools = database.get_tools_by_owner(self.app.current_user["id"], db_path=self.app.db_path)

        for t in tools:
            status_text = f"[green]{t['status']}[/]" if t["status"] == "Disponível" else f"[yellow]{t['status']}[/]"
            table.add_row(
                str(t["id"]),
                t["name"],
                status_text,
                t["contact_phone"],
                t["created_at"],
                key=str(t["id"])
            )

        if tools:
            self.selected_tool = tools[0]
            self.update_details_panel(tools[0])
        else:
            self.selected_tool = None
            self.query_one("#static-my-details", Static).update(
                "[yellow]Você ainda não cadastrou nenhuma ferramenta. Clique em 'Nova Ferramenta' para começar![/]"
            )

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.row_key and event.row_key.value:
            tool_id = int(event.row_key.value)
            tool = database.get_tool_by_id(tool_id, db_path=self.app.db_path)
            if tool:
                self.selected_tool = tool
                self.update_details_panel(tool)

    def update_details_panel(self, tool: Dict[str, Any]) -> None:
        status_color = "green" if tool["status"] == "Disponível" else "yellow"
        details_text = (
            f"[bold cyan]{tool['name']}[/]  |  Status: [{status_color} bold]{tool['status']}[/]\n"
            f"[bold]Telefone para Contato:[/] {tool['contact_phone']}\n"
            f"[bold]Descrição:[/] {tool['description']}\n"
            f"[dim]Cadastrado em: {tool['created_at']}[/]"
        )
        self.query_one("#static-my-details", Static).update(details_text)

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_edit_selected(self) -> None:
        if not self.selected_tool:
            self.app.notify("Selecione uma ferramenta para editar.", severity="warning")
            return

        def on_edit_result(edited: bool) -> None:
            if edited:
                self.app.notify("Ferramenta atualizada com sucesso!", severity="information")
                self.load_my_tools()

        self.app.push_screen(EditToolModal(self.selected_tool), callback=on_edit_result)

    def action_toggle_status_selected(self) -> None:
        if not self.selected_tool:
            self.app.notify("Selecione uma ferramenta para alternar o status.", severity="warning")
            return

        new_status = "Emprestado" if self.selected_tool["status"] == "Disponível" else "Disponível"
        database.update_tool(
            tool_id=self.selected_tool["id"],
            owner_id=self.app.current_user["id"],
            name=self.selected_tool["name"],
            description=self.selected_tool["description"],
            contact_phone=self.selected_tool["contact_phone"],
            status=new_status,
            db_path=self.app.db_path
        )
        self.app.notify(f"Status alterado para: {new_status}", severity="information")
        self.load_my_tools()

    def action_delete_selected(self) -> None:
        if not self.selected_tool:
            self.app.notify("Selecione uma ferramenta para excluir.", severity="warning")
            return

        tool_id = self.selected_tool["id"]
        tool_name = self.selected_tool["name"]

        def on_confirm_delete(confirmed: bool) -> None:
            if confirmed:
                database.delete_tool(tool_id, self.app.current_user["id"], db_path=self.app.db_path)
                self.app.notify(f"Ferramenta '{tool_name}' excluída com sucesso.", severity="information")
                self.load_my_tools()

        self.app.push_screen(
            ConfirmModal(
                title="🗑️ Confirmar Exclusão",
                message=f"Deseja realmente excluir permanentemente a ferramenta:\n[bold cyan]'{tool_name}'[/]?",
                confirm_label="Excluir Definitivamente",
                cancel_label="Voltar / Cancelar"
            ),
            callback=on_confirm_delete
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.action_go_back()
        elif event.button.id == "btn-new":
            self.app.push_screen(AddToolScreen(), callback=lambda _: self.load_my_tools())
        elif event.button.id == "btn-edit":
            self.action_edit_selected()
        elif event.button.id == "btn-toggle":
            self.action_toggle_status_selected()
        elif event.button.id == "btn-delete":
            self.action_delete_selected()


# ==============================================================================
# TELA DE PERFIL DO USUÁRIO
# ==============================================================================

class ProfileScreen(Screen):
    """Exibe dados cadastrais e estatísticas do usuário autenticado."""

    BINDINGS = [
        Binding("escape", "go_back", "Voltar"),
    ]

    def compose(self) -> ComposeResult:
        user = self.app.current_user or {}
        stats = database.get_user_stats(user.get("id", 0), db_path=self.app.db_path)

        yield Header(show_clock=True)
        with Vertical(classes="screen-container"):
            with Vertical(id="profile-card"):
                yield Label("👤 Painel de Perfil do Usuário", classes="screen-header-title")
                yield Static(
                    f"Nome de Usuário: [bold cyan]{user.get('username')}[/]\n"
                    f"Identificador (ID): [bold]#{user.get('id')}[/]\n"
                    f"Membro desde: [bold]{user.get('created_at')}[/]\n",
                    classes="modal-body"
                )

                yield Label("📊 Resumo das Ferramentas:", classes="details-title")
                with Horizontal(classes="stats-grid"):
                    with Vertical(classes="stat-box"):
                        yield Label(str(stats["total_ferramentas"]), classes="stat-number")
                        yield Label("Cadastradas", classes="stat-label")
                    with Vertical(classes="stat-box"):
                        yield Label(f"[green]{stats['disponiveis']}[/]", classes="stat-number")
                        yield Label("Disponíveis", classes="stat-label")
                    with Vertical(classes="stat-box"):
                        yield Label(f"[yellow]{stats['emprestadas']}[/]", classes="stat-number")
                        yield Label("Emprestadas", classes="stat-label")

                with Horizontal(classes="form-buttons"):
                    yield Button("🚪 Sair da Conta (Logout)", variant="error", id="btn-profile-logout")
                    yield Button("🔙 Voltar ao Menu", variant="default", id="btn-profile-back")

        yield Footer()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-profile-back":
            self.action_go_back()
        elif event.button.id == "btn-profile-logout":
            def on_confirm_logout(confirmed: bool) -> None:
                if confirmed:
                    auth.clear_session(self.app.login_path)
                    self.app.current_user = None
                    self.app.notify("Sessão finalizada com sucesso.", title="Logout")
                    self.app.pop_screen()

            self.app.push_screen(
                ConfirmModal(
                    title="🚪 Confirmar Logout",
                    message="Deseja realmente sair da sua conta e retornar ao modo visitante?",
                    confirm_label="Sim, Sair",
                    cancel_label="Voltar"
                ),
                callback=on_confirm_logout
            )


# ==============================================================================
# MENU PRINCIPAL (VISITANTE E USUÁRIO LOGADO)
# ==============================================================================

class MainMenuScreen(Screen):
    """
    Tela principal com menu dinâmico:
    - Modo Visitante: Listar ferramentas, Login/Cadastro, Sair.
    - Modo Logado: Listar ferramentas, Cadastrar ferramenta, Minhas ferramentas, Perfil, Logout, Sair.
    """

    BINDINGS = [
        Binding("l", "open_tool_list", "Listar Ferramentas"),
        Binding("q", "quit_app", "Sair"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="main-menu-container"):
            yield Label("🛠️ SISTEMA DE EMPRÉSTIMO DE FERRAMENTAS", id="main-title")
            yield Label("Compartilhamento comunitário de ferramentas e equipamentos", id="main-subtitle")

            yield Static(id="session-status-card")

            with Vertical(id="visitor-buttons"):
                yield Button("📋 1. Listar Ferramentas", variant="primary", classes="menu-btn", id="btn-list-tools")
                yield Button("🔑 2. Fazer Login / Cadastrar", variant="success", classes="menu-btn", id="btn-auth")
                yield Button("❌ 0. Sair do Aplicativo", variant="error", classes="menu-btn", id="btn-quit")

            with Vertical(id="logged-in-buttons"):
                yield Button("📋 1. Listar Todas as Ferramentas", variant="primary", classes="menu-btn", id="btn-list-tools-auth")
                yield Button("➕ 2. Cadastrar Nova Ferramenta", variant="success", classes="menu-btn", id="btn-add-tool")
                yield Button("🧰 3. Minhas Ferramentas Cadastradas", variant="default", classes="menu-btn", id="btn-my-tools")
                yield Button("👤 4. Painel de Perfil & Estatísticas", variant="default", classes="menu-btn", id="btn-profile")
                yield Button("🚪 5. Sair da Conta (Logout)", variant="warning", classes="menu-btn", id="btn-logout")
                yield Button("❌ 0. Sair do Aplicativo", variant="error", classes="menu-btn", id="btn-quit-auth")

        yield Footer()

    def on_mount(self) -> None:
        self.refresh_menu()

    def on_screen_resume(self) -> None:
        """Chamado quando outra tela é fechada e voltamos ao Menu Principal."""
        self.refresh_menu()

    def refresh_menu(self) -> None:
        """Atualiza a caixa de status e os botões de acordo com o estado atual de login."""
        user = self.app.current_user
        try:
            status_widget = self.query_one("#session-status-card", Static)
            visitor_box = self.query_one("#visitor-buttons", Vertical)
            logged_in_box = self.query_one("#logged-in-buttons", Vertical)
        except Exception:
            return

        if user:
            status_text = (
                f"[bold green]🟢 CONECTADO:[/] [bold cyan]{user['username']}[/] (ID #{user['id']})\n"
                f"[dim]Sessão ativa salva em login.json[/]"
            )
            status_widget.update(status_text)
            visitor_box.display = False
            logged_in_box.display = True
        else:
            status_text = (
                "[bold yellow]⚪ MODO VISITANTE (Não autenticado)[/]\n"
                "[dim]Você pode visualizar o catálogo. Para emprestar ou cadastrar ferramentas, faça login.[/]"
            )
            status_widget.update(status_text)
            visitor_box.display = True
            logged_in_box.display = False

    def action_open_tool_list(self) -> None:
        self.app.push_screen(ToolListScreen())

    def action_quit_app(self) -> None:
        self.app.exit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id

        if btn_id in ("btn-list-tools", "btn-list-tools-auth"):
            self.action_open_tool_list()
        elif btn_id == "btn-auth":
            self.app.push_screen(AuthScreen(), callback=lambda _: self.refresh_menu())
        elif btn_id == "btn-add-tool":
            self.app.push_screen(AddToolScreen())
        elif btn_id == "btn-my-tools":
            self.app.push_screen(MyToolsScreen())
        elif btn_id == "btn-profile":
            self.app.push_screen(ProfileScreen(), callback=lambda _: self.refresh_menu())
        elif btn_id == "btn-logout":
            def on_confirm_logout(confirmed: bool) -> None:
                if confirmed:
                    auth.clear_session(self.app.login_path)
                    self.app.current_user = None
                    self.app.notify("Sessão encerrada com sucesso.", title="Logout", severity="information")
                    self.refresh_menu()

            self.app.push_screen(
                ConfirmModal(
                    title="🚪 Confirmar Logout",
                    message="Deseja realmente sair da sua conta e retornar ao modo visitante?",
                    confirm_label="Sim, Desconectar",
                    cancel_label="Voltar"
                ),
                callback=on_confirm_logout
            )
        elif btn_id in ("btn-quit", "btn-quit-auth"):
            self.action_quit_app()
