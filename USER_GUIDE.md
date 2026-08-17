# 👤 Guia do Usuário

Bem-vindo! Este guia é pra você (humano) usar o projeto sem dor de cabeça.

---

## 🚀 Uso rápido (3 comandos)

```powershell
# 1. Analisar suas curtidas e ver sugestões
python scripts/suggest_playlists.py

# 2. Criar as playlists sugeridas no seu YouTube Music
python scripts/create_playlists.py

# 3. Se os headers expiraram, re-autenticar
python scripts/setup_auth.py
```

---

## 📊 O que cada script faz

### `suggest_playlists.py` — Analisa e sugere

- Busca suas músicas curtidas do YouTube Music
- Pesquisa cada música em fontes confiáveis (Last.fm, Wikipedia)
- Classifica pelo gênero **real** (não pelo rótulo do título)
- Mostra sugestões de playlists no terminal
- Salva o resultado em `data/analysis.json`

**Não modifica nada na sua conta.** Só analisa.

### `create_playlists.py` — Cria as playlists

- Lê o `analysis.json`
- **Mostra cada playlist que vai criar e pede confirmação**
- Você pode:
  - Aceitar todas
  - Aceitar só algumas
  - Pular completamente
- Cria só o que você aprovar

### `setup_auth.py` — Autenticação

- Só precisa rodar uma vez (ou quando expirar)
- Guia você a copiar os headers do navegador
- Salva em `data/browser.json` (nunca sobe pro GitHub)

---

## 🎯 Como as sugestões funcionam

A IA agrupa suas curtidas em eixos musicais coerentes. Os eixos **não são fixos** — se você pedir pra juntar ou separar, ela adapta.

Exemplo de eixos detectados:

| Eixo | Descrição | Exemplos |
|---|---|---|
| 🕰️ Clássicos & Atemporais | Jazz, dream pop, new wave, art pop | Midnight (1934), Panchiko, Pretenders, Dean Blunt |
| 🚗 Chicano Soul | Soul mexicano-americano, oldies | Joey Quinones, Thee Sinseers, The Informers |
| 🔊 Bass & Underground | Phonk, hardstyle, jumpstyle, witch house, weirdcore | HUSSVRX, sematary, ZXVABEAT, rukiwaa |

**Regra do jogo:**
- Hardstyle, phonk, jumpstyle, horrorcore, weirdcore → tudo junto em "Bass & Underground" (baixo forte = mesma vibe)
- Clássicos e atemporais → grupo próprio
- Cenas regionais específicas (Chicano Soul) → grupo próprio

---

## ⚠️ Regra de ouro

**A IA nunca cria, apaga ou modifica playlists sem sua confirmação explícita.**

Se ela sugerir algo, você pode:
- ✅ "Sim, cria"
- ❌ "Não, pula"
- 🔧 "Muda assim: ..."

Qualquer comando que altere sua conta passa por você antes.

---

## 🆘 Troubleshooting

### "Headers expiraram"
Rode `python scripts/setup_auth.py` de novo.

### "Música não foi classificada direito"
A IA vai pesquisar de novo. Você pode dizer: "essa música é X gênero, corrige".

### "Não quero essas sugestões"
Diga: "refaz com esses critérios: ...". Ela adapta os eixos.

---

## 📁 Seus dados

| Arquivo | O que é | Sobe pro GitHub? |
|---|---|---|
| `data/browser.json` | Seus cookies | ❌ NÃO |
| `data/analysis.json` | Resultado da análise | ❌ NÃO |
| `scripts/*.py` | Código | ✅ SIM |
| `*.md` | Documentação | ✅ SIM |

Seu token, cookies e dados pessoais **nunca** saem da sua máquina.
