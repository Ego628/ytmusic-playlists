# 🤖 AI Guide — Como operar neste projeto

Este documento define como uma IA deve se comportar ao trabalhar neste projeto com o usuário. **Leia antes de executar qualquer ação.**

---

## 🎯 Princípios Fundamentais

### 1. SUGESTÃO, NUNCA DECISÃO
Toda ação que altere a conta do usuário (criar/renomear/apagar playlists, adicionar/remover músicas) **deve ser proposta antes e executada só após confirmação explícita**.

```python
# ❌ ERRADO
yt.create_playlist("Rock", "Minhas favoritas")

# ✅ CERTO
print("Vou criar a playlist 'Rock' com 12 músicas. Confirma? [s/n]")
if user_confirms():
    yt.create_playlist("Rock", "Minhas favoritas")
```

### 2. PESQUISA REAL, NÃO CHUTE
Nunca classifique uma música só pelo título (ex: "DEATHMETAL" do Panchiko **não é metal**, é dream pop). Sempre:
- Pesquise em Last.fm, Wikipedia, Rate Your Music
- Verifique contexto do artista (cena musical, outros trabalhos)
- Se o título tiver "slowed/looped/reverb", olhe o **gênero original**, não o efeito

### 3. ADAPTABILIDADE AOS EIXOS DO USUÁRIO
Os eixos musicais **não são fixos**. Se o usuário disser:
- "junta o eixo X com o Y" → junta
- "separa o subgrupo Z" → separa
- "muda o critério para ..." → muda

O histórico atual de preferência do usuário:
- **Bass & Underground** agrupa: phonk, hardstyle, jumpstyle, horrorcore, witch house, weirdcore, dreamcore, trap, drill (tudo com bass forte)
- **Clássicos & Atemporais** separados (jazz, dream pop, new wave, art pop experimental)
- **Cenas regionais** separadas quando bem definidas (ex: Chicano Soul / Lowrider Oldies)

---

## 🔐 Segurança

- **NUNCA** exponha o conteúdo de `data/browser.json` (contém cookies de sessão)
- **NUNCA** comite `browser.json` ou `analysis.json` (estão no .gitignore)
- **NUNCA** imprima cookies/tokens completos em logs ou respostas
- Ao pesquisar uma música, use **título + artista**, não headers do usuário

---

## 📋 Fluxo de Trabalho

### Análise (read-only)
1. Carregar `data/browser.json`
2. Buscar curtidas com `yt.get_liked_songs(limit=500)`
3. Para cada música, pesquisar em fontes confiáveis (Last.fm, Wikipedia)
4. Classificar por eixos baseados nas preferências do usuário
5. Mostrar sugestões e salvar em `data/analysis.json`

### Criação de playlist (requer confirmação)
1. Ler `data/analysis.json`
2. **Para cada playlist sugerida:**
   - Mostrar nome + quantidade + lista de músicas
   - Perguntar: criar? [s/n/editar]
   - Se sim: criar com `yt.create_playlist(name, description)`
   - Adicionar músicas com `yt.add_playlist_items(playlist_id, video_ids)`
3. Mostrar resumo final do que foi criado

### Refinamento
Se o usuário pedir ajustes:
- Re-analisar só o subconjunto afetado
- Não sobrescrever o que já estava bom
- Confirmar antes de aplicar

---

## 🛠️ APIs ytmusicapi relevantes

```python
from ytmusicapi import YTMusic
yt = YTMusic("data/browser.json")

# Leitura
yt.get_liked_songs(limit=500)
yt.get_library_playlists(limit=25)
yt.get_playlist(playlist_id)
yt.search(query, filter="songs")

# Escrita (SEMPRE com confirmação!)
yt.create_playlist(title, description)
yt.add_playlist_items(playlistId, videoIds)
yt.remove_playlist_items(playlistId, videos)
yt.delete_playlist(playlistId)
```

---

## 📊 Formato do analysis.json

```json
{
  "analyzed_at": "2026-08-17T...",
  "total_liked": 22,
  "axes": {
    "classic_timeless": { "description": "...", "tracks": [...] },
    "chicano_soul":     { "description": "...", "tracks": [...] },
    "bass_underground": { "description": "...", "tracks": [...] }
  },
  "suggested_playlists": [
    { "name": "...", "axis": "...", "tracks": [...] }
  ]
}
```

---

## ⚠️ Armadilhas Comuns

| Título enganosos | Gênero real |
|---|---|
| Panchiko - DEATHMETAL | Dream Pop / Shoegaze |
| KERTZAGEM (slowed+) | Hardstyle |
| bunny suit (slowed+bass) | Horrorcore (sematary, Haunted Mound) |
| Major Tom (hardstyle) | Hardstyle edit de synth-pop |
| Midnight, the Stars and You | Jazz 1934 (Ray Noble) |

**Nunca** classifique baseado em:
- Tags "slowed", "looped", "reverb", "best part", "super slowed"
- Caracteres glitch no título (rukiwaa usa ឱロリ— etc)
- Nomes de arquivo estilo phonk (mmm00nm0thz, febuary)

---

## 🎨 Personalidade

- Seja direto e eficiente
- Use português brasileiro
- Explique pesquisas quando forem surpreendentes ("apesar do título 'deathmetal', Panchiko é dream pop")
- Se errar, assuma e pesquise de novo — não insista no erro
- Peça feedback no final: "quer ajustar alguma classificação?"

---

## 🚨 Em caso de dúvida

Antes de executar, **pergunte**. É sempre melhor confirmar do que desfazer.
