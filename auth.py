"""
Módulo de Autenticação e Sessão para o Sistema de Empréstimo de Ferramentas.
Gerencia hash seguro de senhas, validação de credenciais e persistência de sessão
no arquivo 'login.json'.
"""

import os
import json
import hashlib
import hmac
from datetime import datetime
from typing import Optional, Dict, Any

import database

DEFAULT_LOGIN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login.json")


def hash_password(password: str) -> str:
    """Gera um hash seguro da senha usando PBKDF2-HMAC-SHA256 com salt aleatório."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${key.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    try:
        salt_hex, key_hex = hashed.split("$")
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(key, new_key)
    except Exception:
        return False


def get_saved_session(
    login_path: str = DEFAULT_LOGIN_PATH,
    db_path: str = database.DEFAULT_DB_PATH
) -> Optional[Dict[str, Any]]:
    """
    Verifica a existência e integridade do arquivo login.json.
    Se a sessão for válida e o usuário existir no banco, retorna o dicionário do usuário.
    Caso contrário, limpa a sessão corrompida/antiga e retorna None.
    """
    if not os.path.exists(login_path):
        return None

    try:
        with open(login_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        user_id = data.get("user_id")
        username = data.get("username")

        if not user_id or not username:
            clear_session(login_path)
            return None

        # Valida se o usuário ainda existe no banco de dados SQLite
        user = database.get_user_by_id(user_id, db_path=db_path)
        if user and user["username"].lower() == username.lower():
            return {
                "id": user["id"],
                "username": user["username"],
                "created_at": user["created_at"],
                "logged_in_at": data.get("logged_in_at")
            }
        else:
            # Usuário não existe mais no banco
            clear_session(login_path)
            return None

    except (json.JSONDecodeError, OSError, Exception):
        # Arquivo corrompido ou erro de leitura: remove para evitar falhas
        clear_session(login_path)
        return None


def save_session(user: Dict[str, Any], login_path: str = DEFAULT_LOGIN_PATH) -> bool:
    """Salva os dados do usuário autenticado no arquivo login.json."""
    try:
        data = {
            "user_id": user["id"],
            "username": user["username"],
            "logged_in_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(login_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except OSError:
        return False


def clear_session(login_path: str = DEFAULT_LOGIN_PATH) -> bool:
    """Remove o arquivo login.json ao realizar logout ou quando a sessão é invalidada."""
    try:
        if os.path.exists(login_path):
            os.remove(login_path)
        return True
    except OSError:
        return False


def authenticate(
    username: str,
    password: str,
    login_path: str = DEFAULT_LOGIN_PATH,
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Autentica um usuário existente.
    Retorna o dicionário do usuário autenticado ou levanta ValueError com a mensagem de erro.
    """
    username = username.strip()
    if not username or not password:
        raise ValueError("Preencha o nome de usuário e a senha.")

    user = database.get_user_by_username(username, db_path=db_path)
    if not user:
        raise ValueError("Usuário não encontrado.")

    if not verify_password(password, user["password_hash"]):
        raise ValueError("Senha incorreta.")

    user_data = {
        "id": user["id"],
        "username": user["username"],
        "created_at": user["created_at"]
    }
    save_session(user_data, login_path=login_path)
    return user_data


def register(
    username: str,
    password: str,
    confirm_password: str,
    login_path: str = DEFAULT_LOGIN_PATH,
    db_path: str = database.DEFAULT_DB_PATH
) -> Dict[str, Any]:
    """
    Cadastra uma nova conta de usuário.
    Realiza validações e, em caso de sucesso, salva a sessão e retorna o usuário.
    """
    username = username.strip()
    if not username:
        raise ValueError("O nome de usuário não pode estar em branco.")

    if len(username) < 3:
        raise ValueError("O nome de usuário deve ter pelo menos 3 caracteres.")

    if not username.replace("_", "").replace("-", "").isalnum():
        raise ValueError("O nome de usuário deve conter apenas letras, números, '-' ou '_'.")

    if not password:
        raise ValueError("A senha não pode estar em branco.")

    if len(password) < 4:
        raise ValueError("A senha deve ter pelo menos 4 caracteres.")

    if password != confirm_password:
        raise ValueError("As senhas não coincidem.")

    existing = database.get_user_by_username(username, db_path=db_path)
    if existing:
        raise ValueError(f"O nome de usuário '{username}' já está em uso.")

    pwd_hash = hash_password(password)
    user_id = database.create_user(username, pwd_hash, db_path=db_path)

    user_data = {
        "id": user_id,
        "username": username,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_session(user_data, login_path=login_path)
    return user_data
