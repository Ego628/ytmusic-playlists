# 🔧 Instalação

## Pré-requisitos

- **Windows 10/11** (PowerShell 5.1+)
- **Python 3.10+** ([download](https://python.org))
- **Conta Google** com acesso ao YouTube Music
- **Chrome/Edge** para copiar headers

## Passo 1 — Clonar o repositório

```powershell
cd C:\Users\Pj\Documents
git clone https://github.com/Ego628/ytmusic-playlists.git
cd ytmusic-playlists
```

## Passo 2 — Instalar dependências

```powershell
pip install ytmusicapi
```

> 💡 Opcional: crie um venv antes (`python -m venv .venv` e `.venv\Scripts\Activate.ps1`)

## Passo 3 — Autenticar no YouTube Music

Esse é o único passo "manual". Você vai copiar os headers de uma requisição do YouTube Music.

### 3.1 Abra o YouTube Music logado

1. Abra `https://music.youtube.com` no Chrome
2. Faça login se ainda não estiver

### 3.2 Copie os headers

1. Pressione **F12** (DevTools)
2. Aba **Network** → filtro: `youtubei`
3. Recarregue a página (F5)
4. Clique em qualquer requisição que começar com `/youtubei/`
5. Na aba **Headers**, role até **Request Headers**
6. Botão direito → **Copy** → **Copy as cURL (bash)**

### 3.3 Rode o setup

```powershell
python scripts/setup_auth.py
```

Cole o cURL copiado e pressione **Enter duas vezes**.

O arquivo `data/browser.json` será criado. Ele **nunca** é enviado ao GitHub (está no `.gitignore`).

## Passo 4 — Testar

```powershell
python scripts/suggest_playlists.py
```

Deve aparecer suas músicas curtidas e sugestões de playlists.

## Pronto!

Veja [USER_GUIDE.md](USER_GUIDE.md) para começar a usar.

---

### ⚠️ Problemas comuns

**"You are not logged in"** → seus headers expiraram. Repita o Passo 3.

**"UnicodeEncodeError"** → já foi corrigido nos scripts (usamos `sys.stdout.reconfigure(encoding='utf-8')`).

**"oauth_credentials not provided"** → use o formato de browser auth (cookies), não OAuth. O `setup_auth.py` já faz isso certo.
