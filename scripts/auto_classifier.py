"""
Auto-classifier: organiza automaticamente musicas curtidas do YouTube Music
em playlists existentes (ou cria novas baseadas em clusters de genero).

Comando:
  python scripts/auto_classifier.py                 # aplica mudancas
  python scripts/auto_classifier.py --dry-run       # so mostra o que faria
  python scripts/auto_classifier.py --limit 50      # processa N musicas

Gera relatorio em: data/reports/YYYY-MM-DD_HHMM.md (+ .json)
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ytmusicapi import YTMusic
from lib import actions_log, genre_cache, genre_classifier

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
DATA_DIR = HERE.parent / "data"
REPORTS_DIR = DATA_DIR / "reports"
AUTH_FILE = DATA_DIR / "browser.json"


AXIS_LABELS = {
    "bass_underground": "Bass & Underground",
    "classic_timeless": "Clássicos & Atemporais",
    "chicano_soul": "Chicano Soul / Lowrider Oldies",
    "electronic_dance": "Eletrônica",
    "pop_mainstream": "Pop",
    "hip_hop": "Hip-Hop / Rap",
    "rock_metal": "Rock / Metal",
    "uncategorized": "Não Classificadas",
}


def _load_yt() -> YTMusic:
    if not AUTH_FILE.exists():
        print(f"[ERRO] {AUTH_FILE} nao encontrado. Rode: python scripts/setup_auth.py")
        sys.exit(1)
    return YTMusic(str(AUTH_FILE))


def _get_existing_playlists(yt: YTMusic) -> dict[str, dict]:
    pls = {}
    for p in yt.get_library_playlists(limit=100):
        pls[p["playlistId"]] = {"id": p["playlistId"], "title": p.get("title", "")}
    return pls


def _playlist_items_ids(yt: YTMusic, playlist_id: str) -> set[str]:
    out = set()
    try:
        pl = yt.get_playlist(playlist_id, limit=None)
        for t in pl.get("tracks", []):
            vid = t.get("videoId")
            if vid:
                out.add(vid)
    except Exception:
        pass
    return out


def _map_playlist_to_axis(title: str) -> str | None:
    tl = title.lower()
    for axis, keywords in [
        ("bass_underground", ["bass", "phonk", "underground", "weird"]),
        ("classic_timeless", ["clássico", "classico", "atemporal", "eterno", "classic"]),
        ("chicano_soul", ["lowrider", "chicano", "soul night"]),
        ("electronic_dance", ["edm", "house", "eletron", "electronic"]),
        ("pop_mainstream", ["pop ", "pop\"", "k-pop"]),
        ("hip_hop", ["hip-hop", "hip hop", "rap "]),
        ("rock_metal", ["rock", "metal", "punk"]),
    ]:
        for kw in keywords:
            if kw in tl:
                return axis
    return None


def _pick_target_playlist(
    axis: str,
    existing: dict[str, dict],
    axis_playlists: dict[str, str],
) -> tuple[str, bool]:
    if axis in axis_playlists:
        return (axis_playlists[axis], False)
    label = AXIS_LABELS.get(axis, axis.replace("_", " ").title())
    return (label, True)


def run(dry_run: bool, limit: int):
    started = time.time()
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print(f"  AUTO-CLASSIFIER  |  run_id: {run_id}  |  dry_run: {dry_run}")
    print("=" * 70)

    yt = _load_yt()
    print("[1/5] Buscando playlists existentes...")
    existing = _get_existing_playlists(yt)
    print(f"      {len(existing)} playlists")

    axis_playlists: dict[str, str] = {}
    for pid, p in existing.items():
        axis = _map_playlist_to_axis(p["title"])
        if axis and axis not in axis_playlists:
            axis_playlists[axis] = pid

    print("      Mapeamentos detectados:")
    for a, pid in axis_playlists.items():
        print(f"        {a:25s} -> {existing[pid]['title']}")

    print("[2/5] Buscando musicas curtidas...")
    liked_resp = yt.get_liked_songs(limit=limit or 1000)
    liked = liked_resp.get("tracks", [])
    if limit:
        liked = liked[:limit]
    print(f"      {len(liked)} musicas")

    print("[3/5] Classificando generos (cache + Last.fm)...")
    classified = []
    for i, t in enumerate(liked, 1):
        artist = (t.get("artists") or [{}])[0].get("name", "?")
        title = t.get("title", "?")
        cls = genre_classifier.classify_track(artist, title)
        classified.append({"track": t, "cls": cls})
        if i % 10 == 0:
            print(f"      {i}/{len(liked)} ...")
            time.sleep(0.3)
        else:
            time.sleep(0.15)

    print("[4/5] Agrupando por eixo...")
    by_axis: dict[str, list[dict]] = {}
    for item in classified:
        axis = item["cls"]["axis"]
        by_axis.setdefault(axis, []).append(item)

    for axis, items in sorted(by_axis.items()):
        print(f"      {axis:25s} {len(items):>4d} musicas")

    print("[5/5] Organizando nas playlists...")
    actions_log.start_run(run_id, f"auto_classifier dry_run={dry_run} limit={limit}")

    created_playlists: dict[str, str] = {}
    actions_count = 0
    summary = {"added": 0, "created": 0, "skipped_in_playlist": 0, "errors": 0, "by_axis": {}}

    for axis, items in by_axis.items():
        target_label, need_create = _pick_target_playlist(axis, existing, axis_playlists)
        target_id = None

        if need_create:
            if axis in created_playlists:
                target_id = created_playlists[axis]
            elif not dry_run:
                desc = f"Playlist criada automaticamente para musicas do eixo: {axis}"
                new_id = yt.create_playlist(target_label, desc)
                created_playlists[axis] = new_id
                actions_log.log_action(run_id, "create_playlist",
                    {"playlist_id": new_id, "playlist_name": target_label, "axis": axis})
                summary["created"] += 1
                target_id = new_id
                print(f"      [CRIADA] {target_label} ({new_id})")
            else:
                target_id = f"DRY-{axis}"
                print(f"      [DRY] criaria playlist: {target_label}")
        else:
            target_id = target_label

        items_in_target = set() if dry_run else _playlist_items_ids(yt, target_id) if not need_create else set()

        for item in items:
            vid = item["track"].get("videoId")
            if not vid:
                continue
            if vid in items_in_target:
                summary["skipped_in_playlist"] += 1
                continue
            if dry_run:
                summary["added"] += 1
                continue
            try:
                yt.add_playlist_items(target_id, [vid])
                actions_log.log_action(run_id, "add_to_playlist",
                    {"playlist_id": target_id, "playlist_name": target_label,
                     "video_id": vid, "title": item["track"].get("title"),
                     "artist": (item["track"].get("artists") or [{}])[0].get("name"),
                     "axis": axis})
                summary["added"] += 1
                actions_count += 1
            except Exception as e:
                summary["errors"] += 1
                print(f"      [ERRO] {item['track'].get('title')}: {e}")

        summary["by_axis"][axis] = len(items)

    duration = time.time() - started
    summary["duration_s"] = round(duration, 1)
    actions_log.finish_run(run_id, "ok" if not dry_run else "dry_run", summary)

    print()
    print("=" * 70)
    print("  RESULTADO")
    print("=" * 70)
    print(f"  Playlists criadas:      {summary['created']}")
    print(f"  Musicas adicionadas:    {summary['added']}")
    print(f"  Ja estavam na playlist: {summary['skipped_in_playlist']}")
    print(f"  Erros:                  {summary['errors']}")
    print(f"  Duracao:                {summary['duration_s']}s")
    print(f"  Cache stats:            {genre_cache.stats()}")
    print()
    print(f"Para desfazer:  python scripts/rollback.py {run_id}")
    print(f"Relatorios:     {REPORTS_DIR}/{run_id}.md | .json")

    _save_reports(run_id, run_id, classified, summary, by_axis, axis_playlists,
                   dry_run, created_playlists)


def _save_reports(run_id, ts, classified, summary, by_axis, axis_playlists,
                  dry_run, created_playlists):
    ts_dt = datetime.now()
    md_path = REPORTS_DIR / f"{run_id}.md"
    json_path = REPORTS_DIR / f"{run_id}.json"

    lines = [
        f"# Auto-Classifier Report — {ts_dt:%Y-%m-%d %H:%M:%S}",
        "",
        f"**Run ID:** `{run_id}`  ",
        f"**Modo:** {'DRY-RUN (nada foi alterado)' if dry_run else 'APLICADO'}  ",
        f"**Duração:** {summary['duration_s']}s  ",
        f"**Cache stats:** {genre_cache.stats()}",
        "",
        "## Resumo",
        "",
        f"- Playlists criadas: **{summary['created']}**",
        f"- Músicas adicionadas: **{summary['added']}**",
        f"- Já estavam na playlist: **{summary['skipped_in_playlist']}**",
        f"- Erros: **{summary['errors']}**",
        "",
        "## Distribuição por eixo",
        "",
        "| Eixo | Músicas |",
        "|---|---:|",
    ]
    for axis, items in sorted(by_axis.items()):
        lines.append(f"| {axis} | {len(items)} |")

    lines += [
        "",
        "## Mapeamento playlists existentes",
        "",
        "| Eixo | Playlist |",
        "|---|---|",
    ]
    for axis, pid in axis_playlists.items():
        lines.append(f"| {axis} | {pid} |")

    lines += ["", "## Detalhe por música", ""]
    for axis, items in sorted(by_axis.items()):
        lines.append(f"### {axis}")
        lines.append("")
        for item in items:
            c = item["cls"]
            t = item["track"]
            artist = (t.get("artists") or [{}])[0].get("name", "?")
            title = t.get("title", "?")
            tags = ", ".join(c.get("tags", [])[:8]) or "(sem tags)"
            lines.append(
                f"- **{artist} — {title}**  \n"
                f"  gêneros: `{c.get('genres')}` | confiança: `{c.get('confidence'):.2f}` | "
                f"fonte: `{c.get('source')}` | tags: {tags}"
            )
        lines.append("")

    if summary["errors"]:
        lines += ["", "## Erros", "", "Verifique as músicas com erro no log."]

    md_path.write_text("\n".join(lines), encoding="utf-8")

    json_data = {
        "run_id": run_id,
        "timestamp": ts_dt.isoformat(),
        "dry_run": dry_run,
        "summary": summary,
        "by_axis": {a: len(v) for a, v in by_axis.items()},
        "axis_playlists": axis_playlists,
        "created_playlists": created_playlists,
        "classified": [
            {
                "videoId": item["track"].get("videoId"),
                "artist": (item["track"].get("artists") or [{}])[0].get("name"),
                "title": item["track"].get("title"),
                "axis": item["cls"]["axis"],
                "genres": item["cls"]["genres"],
                "tags": item["cls"]["tags"][:10],
                "confidence": item["cls"]["confidence"],
                "source": item["cls"]["source"],
                "listeners": item["cls"].get("listeners", 0),
            }
            for item in classified
        ],
    }
    json_path.write_text(json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  Relatorio MD:   {md_path}")
    print(f"  Relatorio JSON: {json_path}")


def main():
    parser = argparse.ArgumentParser(description="Auto-classifier de musicas curtidas")
    parser.add_argument("--dry-run", action="store_true", help="so mostra o que faria")
    parser.add_argument("--limit", type=int, default=0, help="limite de musicas (0 = todas)")
    args = parser.parse_args()
    run(dry_run=args.dry_run, limit=args.limit)


if __name__ == "__main__":
    main()
