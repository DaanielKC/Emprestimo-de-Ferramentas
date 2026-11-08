# 🛠️ Sistema de Empréstimo de Ferramentas (TUI)

Um sistema completo de terminal (TUI - Terminal User Interface) para empréstimo e compartilhamento comunitário de ferramentas, construído com **Python 3.10+**, **Textual** e **SQLite**. O código foi criado com o Google Antigravity, utilizando o modelo Gemini 3.8 Flash.

---

## 🚀 Como Executar

### 1. Pré-requisitos
Certifique-se de que possui o Python 3.10 ou superior instalado e a biblioteca `textual`:

```bash
pip install textual
```

### 2. Executando a Aplicação
Navegue até a pasta do projeto e inicie o sistema:

```bash
cd "caminho-da-pasta"
python app.py
```

---

## 👥 Contas de Demonstração Pré-cadastradas

O sistema inicializa automaticamente o banco de dados `ferramentas.db` com dados de demonstração (semente/seed) para teste imediato:

| Usuário | Senha | Ferramentas Cadastradas |
|---|---|---|
| `carlos` | `carlos123` | Furadeira Bosch 550W, Jogo de Chaves Combinadas |
| `maria` | `maria123` | Serra Tico-Tico Makita, Escada Articulada 4.7m |

> **Nota:** Você também pode criar novas contas a qualquer momento na opção **Fazer Login / Cadastrar**.

---

## 📁 Estrutura de Arquivos

```
sistema_ferramentas/
├── app.py              # Ponto de entrada da aplicação Textual e ciclo de vida
├── screens.py          # Telas, modais e formulários reativos do Textual
├── database.py         # Módulo SQLite, schemas, seeding e operações CRUD
├── auth.py             # Módulo de autenticação segura (PBKDF2) e sessão (login.json)
├── styles.tcss         # Folha de estilos (TCSS) com tema escuro e moderno
├── login.json          # Arquivo de persistência de sessão (gerado após login)
├── ferramentas.db      # Banco de dados local SQLite (gerado automaticamente)
├── test_system.py      # Suíte de testes automatizados de ponta a ponta
└── README.md           # Documentação completa do sistema
```

---

## 🧭 Fluxo e Funcionalidades

### 1. Inicialização e Persistência de Sessão (`login.json`)
- Ao iniciar, o app verifica a existência e integridade do arquivo `login.json`.
- Se houver uma sessão válida e o usuário existir no banco SQLite, o aplicativo restaura o login automaticamente.
- Se o arquivo não existir ou for inválido, o app inicia no **Modo Visitante**.
- Ao fazer **Logout manual**, o arquivo `login.json` é removido e o sistema retorna ao modo visitante.
- Caso o usuário feche o aplicativo ou terminal enquanto conectado, a sessão permanece salva para a próxima execução.

### 2. Modo Visitante (Não Autenticado)
- **Listar Ferramentas:** Permite navegar por todas as ferramentas cadastradas no banco de dados e filtrar em tempo real por nome/descrição.
  - Selecione qualquer ferramenta para inspecionar os detalhes no painel inferior.
  - Ao tentar a ação **"Pegar Emprestado"**, o sistema detecta que o usuário não está conectado e abre uma janela modal solicitando autenticação, com atalho direto para a tela de Login/Cadastro.
- **Fazer Login / Cadastrar:** Tela com abas para entrar com usuário e senha ou registrar uma nova conta.

### 3. Modo Usuário Logado
Assim que autenticado, o Menu Principal se expande com as opções completas:
1. **Listar Ferramentas:** Além de visualizar os detalhes, clicar em **"Pegar Emprestado"** exibe a janela com o **telefone de contato direto** do proprietário para negociação (ligação ou WhatsApp).
2. **Cadastrar Ferramenta:** Formulário para disponibilizar um novo equipamento, informando nome, descrição/acessórios e telefone para contato.
3. **Minhas Ferramentas Cadastradas:** Painel dedicado para gerenciar as ferramentas do próprio usuário:
   - **Editar:** Atualiza nome, descrição, telefone ou status.
   - **Alternar Status:** Alterna rapidamente entre *Disponível* e *Emprestado*.
   - **Excluir:** Remove a ferramenta do banco de dados com modal de confirmação.
4. **Painel de Perfil:** Exibe as credenciais do usuário e estatísticas em tempo real (total de ferramentas, disponíveis e emprestadas).
5. **Sair da Conta (Logout):** Confirma e remove a sessão salva, retornando ao modo visitante.

---

## ⌨️ Atalhos de Teclado (Keybindings)

| Tecla | Ação |
|---|---|
| `Tab` / `Shift+Tab` | Navegar entre botões e campos de formulário |
| `Enter` | Acionar botão ou selecionar linha da tabela |
| `Escape` | Voltar à tela anterior |
| `l` | Abrir catálogo de ferramentas (a partir do menu) |
| `b` | Solicitar empréstimo da ferramenta selecionada |
| `r` | Recarregar / limpar filtro de busca |
| `e` | Editar ferramenta selecionada (em Minhas Ferramentas) |
| `t` | Alternar status Disponível/Emprestado |
| `d` | Excluir ferramenta selecionada |
| `q` | Sair da aplicação |

---

## 🧪 Execução dos Testes Automatizados

Para rodar os testes de integração do banco de dados, autenticação, persistência e TUI Textual:

```bash
python test_system.py
```
