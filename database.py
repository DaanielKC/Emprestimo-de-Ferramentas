"""
Módulo de Banco de Dados SQLite para o Sistema de Empréstimo de Ferramentas.
Gerencia conexões, criação automática de tabelas, inserção de dados iniciais (seed)
e operações CRUD para usuários e ferramentas.
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ferramentas.db")


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Cria e retorna uma conexão com o banco de dados SQLite com suporte a Foreign Keys."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH, seed: bool = True) -> None:
    """
    Inicializa o banco de dados criando as tabelas necessárias caso não existam.
    Se o banco for novo ou estiver vazio, insere dados iniciais de demonstração.
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # Tabela de Usuários
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
        """)

        # Tabela de Ferramentas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                contact_phone TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Disponível',
                created_at TEXT NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        conn.commit()

        # Opcional: Inserir dados de exemplo se a tabela de ferramentas estiver vazia
        if seed:
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                _seed_initial_data(cursor, conn)


def _seed_initial_data(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    """Cria usuários e ferramentas de exemplo para teste imediato."""
    # Importação local para evitar dependência circular
    from auth import hash_password
    
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Criar usuário demo 1: 'carlos' (senha: 'carlos123')
    pwd_carlos = hash_password("carlos123")
    cursor.execute(
        "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
        ("carlos", pwd_carlos, agora)
    )
    carlos_id = cursor.lastrowid

    # Criar usuário demo 2: 'maria' (senha: 'maria123')
    pwd_maria = hash_password("maria123")
    cursor.execute(
        "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
        ("maria", pwd_maria, agora)
    )
    maria_id = cursor.lastrowid

    # Ferramentas de exemplo
    ferramentas_exemplo = [
        (
            carlos_id,
            "Furadeira de Impacto Bosch GSB 550W",
            "Acompanha jogo de brocas para concreto, madeira e metal. Voltagem 110V.",
            "(11) 98765-4321",
            "Disponível",
            agora
        ),
        (
            carlos_id,
            "Jogo de Chaves Combinadas (6mm a 22mm)",
            "Jogo completo de chaves de boca e estria em aço cromo vanádio com estojo.",
            "(11) 98765-4321",
            "Disponível",
            agora
        ),
        (
            maria_id,
            "Serra Tico-Tico Makita 450W",
            "Ideal para cortes retos e curvos em madeira e plástico. Com lâmina reserva.",
            "(11) 99123-8899",
            "Disponível",
            agora
        ),
        (
            maria_id,
            "Escada Articulada de Alumínio 4x3 (4.7m)",
            "Escada multifunção com travas de segurança reforçadas. Suporta até 150kg.",
            "(11) 99123-8899",
            "Emprestado",
            agora
        ),
    ]

    cursor.executemany("""
        INSERT INTO tools (owner_id, name, description, contact_phone, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, ferramentas_exemplo)
    conn.commit()


# ==========================================
# Funções de Usuário
# ==========================================

def get_user_by_username(username: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Busca usuário pelo nome de usuário (case-insensitive)."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? COLLATE NOCASE", (username.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Busca usuário pelo ID."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_user(username: str, password_hash: str, db_path: str = DEFAULT_DB_PATH) -> int:
    """Cadastra um novo usuário e retorna seu ID."""
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
            (username.strip(), password_hash, agora)
        )
        conn.commit()
        return cursor.lastrowid


# ==========================================
# Funções de Ferramentas
# ==========================================

def get_all_tools(search_term: Optional[str] = None, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retorna todas as ferramentas com o nome do dono, permitindo filtro de busca."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        query = """
            SELECT t.id, t.owner_id, t.name, t.description, t.contact_phone, t.status, t.created_at,
                   u.username AS owner_name
            FROM tools t
            INNER JOIN users u ON t.owner_id = u.id
        """
        params = []
        if search_term:
            query += " WHERE t.name LIKE ? OR t.description LIKE ?"
            term = f"%{search_term.strip()}%"
            params.extend([term, term])
            
        query += " ORDER BY t.id DESC"
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_tools_by_owner(owner_id: int, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retorna todas as ferramentas pertencentes a um determinado usuário."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.owner_id, t.name, t.description, t.contact_phone, t.status, t.created_at,
                   u.username AS owner_name
            FROM tools t
            INNER JOIN users u ON t.owner_id = u.id
            WHERE t.owner_id = ?
            ORDER BY t.id DESC
        """, (owner_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_tool_by_id(tool_id: int, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Busca uma ferramenta pelo seu ID juntamente com o nome do dono."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.owner_id, t.name, t.description, t.contact_phone, t.status, t.created_at,
                   u.username AS owner_name
            FROM tools t
            INNER JOIN users u ON t.owner_id = u.id
            WHERE t.id = ?
        """, (tool_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_tool(owner_id: int, name: str, description: str, contact_phone: str, db_path: str = DEFAULT_DB_PATH) -> int:
    """Cadastra uma nova ferramenta no banco de dados."""
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tools (owner_id, name, description, contact_phone, status, created_at)
            VALUES (?, ?, ?, ?, 'Disponível', ?)
        """, (owner_id, name.strip(), description.strip(), contact_phone.strip(), agora))
        conn.commit()
        return cursor.lastrowid


def update_tool(tool_id: int, owner_id: int, name: str, description: str, contact_phone: str, status: str, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Atualiza as informações de uma ferramenta (somente se pertencer ao owner_id)."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tools
            SET name = ?, description = ?, contact_phone = ?, status = ?
            WHERE id = ? AND owner_id = ?
        """, (name.strip(), description.strip(), contact_phone.strip(), status.strip(), tool_id, owner_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_tool(tool_id: int, owner_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Exclui uma ferramenta do banco de dados (somente se pertencer ao owner_id)."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tools WHERE id = ? AND owner_id = ?", (tool_id, owner_id))
        conn.commit()
        return cursor.rowcount > 0


def get_user_stats(user_id: int, db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Retorna estatísticas do usuário (total de ferramentas, disponíveis e emprestadas)."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tools WHERE owner_id = ?", (user_id,))
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tools WHERE owner_id = ? AND status = 'Disponível'", (user_id,))
        disponiveis = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM tools WHERE owner_id = ? AND status = 'Emprestado'", (user_id,))
        emprestadas = cursor.fetchone()[0]

        return {
            "total_ferramentas": total,
            "disponiveis": disponiveis,
            "emprestadas": emprestadas
        }
