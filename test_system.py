"""
Script de testes automatizados de ponta a ponta (E2E) para o Sistema de Empréstimo de Ferramentas.
Valida banco de dados, sessão login.json e ciclo de vida da interface Textual.
"""

import os
import sys
import asyncio

import database
import auth
from app import FerramentasApp
from screens import MainMenuScreen, ToolListScreen, AuthScreen, AddToolScreen, MyToolsScreen, ProfileScreen


async def test_full_system():
    print("\n--- INICIANDO TESTES DO SISTEMA ---")
    
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_db = os.path.join(test_dir, "test_ferramentas.db")
    test_login = os.path.join(test_dir, "test_login.json")

    # Limpar resíduos de testes anteriores
    for p in (test_db, test_login):
        if os.path.exists(p):
            os.remove(p)

    # 1. Testar Inicialização do Banco SQLite
    print("[1] Testando inicialização e seeding do SQLite...")
    database.init_db(test_db, seed=True)
    tools = database.get_all_tools(db_path=test_db)
    assert len(tools) >= 4, f"Esperado ao menos 4 ferramentas de exemplo, obtido {len(tools)}"
    print(f"  -> Sucesso: {len(tools)} ferramentas carregadas no banco inicial.")

    # 2. Testar Autenticação e Registro
    print("[2] Testando cadastro e autenticação de usuários...")
    novo_usuario = auth.register("joaosilva", "senha123", "senha123", login_path=test_login, db_path=test_db)
    assert novo_usuario["username"] == "joaosilva"
    assert os.path.exists(test_login), "Arquivo login.json deveria ter sido criado."
    print("  -> Sucesso: Usuário cadastrado e login.json gerado.")

    # 3. Testar Recuperação de Sessão Persistente
    print("[3] Testando restauração de sessão a partir do login.json...")
    sessao = auth.get_saved_session(login_path=test_login, db_path=test_db)
    assert sessao is not None
    assert sessao["username"] == "joaosilva"
    print(f"  -> Sucesso: Sessão recuperada para o usuário '{sessao['username']}'.")

    # 4. Testar Operações CRUD de Ferramentas
    print("[4] Testando operações de Ferramentas...")
    # Cadastrar ferramenta
    tool_id = database.create_tool(
        owner_id=sessao["id"],
        name="Cortador de Grama Elétrico Tramontina",
        description="Potência de 1300W com coletor de grama.",
        contact_phone="(11) 97777-6666",
        db_path=test_db
    )
    assert tool_id is not None
    print(f"  -> Ferramenta ID #{tool_id} criada.")

    # Listar ferramentas do usuário
    minhas = database.get_tools_by_owner(sessao["id"], db_path=test_db)
    assert len(minhas) == 1
    assert minhas[0]["name"] == "Cortador de Grama Elétrico Tramontina"
    print("  -> Listagem de ferramentas do usuário validada.")

    # Atualizar ferramenta
    database.update_tool(
        tool_id=tool_id,
        owner_id=sessao["id"],
        name="Cortador de Grama Elétrico Tramontina 1300W (Atualizado)",
        description="Potência de 1300W com coletor e lâmina extra.",
        contact_phone="(11) 97777-6666",
        status="Emprestado",
        db_path=test_db
    )
    tool_atualizada = database.get_tool_by_id(tool_id, db_path=test_db)
    assert tool_atualizada["status"] == "Emprestado"
    assert "Atualizado" in tool_atualizada["name"]
    print("  -> Edição e alternância de status validadas.")

    # Estatísticas do perfil
    stats = database.get_user_stats(sessao["id"], db_path=test_db)
    assert stats["total_ferramentas"] == 1
    assert stats["emprestadas"] == 1
    assert stats["disponiveis"] == 0
    print(f"  -> Estatísticas do perfil validadas: {stats}.")

    # Excluir ferramenta
    excluido = database.delete_tool(tool_id, sessao["id"], db_path=test_db)
    assert excluido is True
    assert database.get_tool_by_id(tool_id, db_path=test_db) is None
    print("  -> Exclusão de ferramenta validada.")

    # 5. Testar Limpeza de Sessão (Logout)
    print("[5] Testando logout e exclusão do login.json...")
    auth.clear_session(test_login)
    assert not os.path.exists(test_login), "login.json deveria ter sido removido no logout."
    assert auth.get_saved_session(login_path=test_login, db_path=test_db) is None
    print("  -> Logout verificado com sucesso.")

    # 6. Testar Interface Textual em Modo Headless (run_test)
    print("[6] Testando ciclo de vida da interface Textual...")
    app = FerramentasApp()
    app.db_path = test_db
    app.login_path = test_login

    async with app.run_test() as pilot:
        # App inicializa em modo visitante pois login.json não existe
        assert app.current_user is None
        await pilot.pause()
        print("  -> Textual montado em Modo Visitante com sucesso.")

        # Simula autenticação no app
        app.current_user = {"id": 1, "username": "carlos", "created_at": "2026-11-07"}
        auth.save_session(app.current_user, login_path=test_login)
        main_screen = app.screen
        if isinstance(main_screen, MainMenuScreen):
            main_screen.refresh_menu()
        await pilot.pause()
        print("  -> Menu principal atualizado para Modo Logado com sucesso.")

        # Testar abertura da tela de listagem de ferramentas
        app.push_screen(ToolListScreen())
        await pilot.pause()
        assert isinstance(app.screen, ToolListScreen)
        print("  -> ToolListScreen aberta e renderizada.")

        # Testar voltar ao menu
        app.pop_screen()
        await pilot.pause()
        assert isinstance(app.screen, MainMenuScreen)
        print("  -> Retorno ao MainMenuScreen realizado com sucesso.")

    # Limpeza final dos arquivos de teste
    for p in (test_db, test_login):
        if os.path.exists(p):
            os.remove(p)

    print("\n[OK] TODOS OS TESTES PASSARAM COM SUCESSO!\n")


if __name__ == "__main__":
    asyncio.run(test_full_system())
