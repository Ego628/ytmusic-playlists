# 🎵 ytmusic-playlists

Analisador e organizador de playlists do **YouTube Music** baseado nas suas músicas curtidas, usando IA para classificação refinada (com pesquisa real em fontes confiáveis, não chutes pelo título).

## O que faz

- Autentica no YouTube Music via browser headers (cookies)
- Busca todas as suas músicas curtidas
- Analisa cada música pesquisando em **Last.fm, Wikipedia e outras fontes**
- Classifica por gênero real (não pelo rótulo "slowed" ou "looped" do título)
- Sugere playlists coerentes baseadas no seu perfil
- Pode **criar as playlists de verdade no YouTube Music** (com confirmação)

## Princípios

1. **Toda ação destrutiva ou de criação pede confirmação** — nunca decide por você
2. **Pesquisa real, não chute** — cada música é investigada em fontes confiáveis
3. **Sugestões, não decisões** — a IA propõe, você aprova

## Estrutura

```
ytmusic-playlists/
├── README.md              ← você está aqui
├── INSTALL.md             ← guia de instalação
├── USER_GUIDE.md          ← guia para humanos (simples)
├── AI_GUIDE.md            ← guia para IAs (como operar)
├── .gitignore             ← nunca subir creds ou dados pessoais
├── scripts/
│   ├── setup_auth.py      ← autenticação
│   ├── suggest_playlists.py ← análise + sugestões
│   └── create_playlists.py  ← cria as playlists no YT Music
└── data/
    ├── browser.json       ← (NÃO versionado) seus headers
    └── analysis.json      ← resultado da análise
```

## Começando

👉 Veja [INSTALL.md](INSTALL.md) para instalar e [USER_GUIDE.md](USER_GUIDE.md) para usar.

## Autor

[Ego628](https://github.com/Ego628)

## Licença

MIT
