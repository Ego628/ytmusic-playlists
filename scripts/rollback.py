"""
Rollback: desfaz acoes registradas no actions_log.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ytmusicapi import YTMusic
from lib import actions_log

HERE = Path(__file__).parent
DATA_DIR = HERE.parent / "data"
AUTH_FILE = DATA_DIR / "browser.json"


def _undo_action(yt: YTMusic, action: dict) -> bool:
    kind = action["kind"]
    p = action["payload"]
    try:
        if kind == "add_to_playlist":
            yt.remove_playlist_items(p["playlist_id"], [p["video_id"]])
            return True
        if kind == "create_playlist":
            yt.delete_playlist(p["playlist_id"])
            return True
        if kind == "remove_from_playlist":
            yt.add_playlist_items(p["playlist_id"], [p["video_id"]])
            return True
        return False
    except Exception as e:
        print(f"  [ERRO] falha ao desfazer {kind}: {e}")
        return False


def rollback(run_id: str, *, dry_run: bool = False) -> dict:
    run = actions_log.get_run(run_id)
    if not run:
        print(f"[ERRO] run_id '{run_id}' nao encontrado.")
        return {"ok": False}

    actions = actions_log.get_actions(run_id, only_active=True)
    print(f"Run: {run_id}")
    print(f"  Comando: {run['command']}")
    print(f"  Status:  {run['status']}")
    print(f"  Acoes a desfazer: {len(actions)}")

    if dry_run:
        for a in actions:
            print(f"  [DRY] {a['kind']}: {a['payload']}")
        return {"ok": True, "undone": 0, "dry": True}

    yt = YTMusic(str(AUTH_FILE))
    undone = 0
    for a in actions:
        ok = _undo_action(yt, a)
        if ok:
            actions_log.mark_rolled_back(a["id"])
            undone += 1
            print(f"  [OK] desfeito: {a['kind']} {a['payload'].get('playlist_name', '')}")

    actions_log.mark_run_status(run_id, "rolled_back")
    return {"ok": True, "undone": undone, "total": len(actions)}


def main():
    parser = argparse.ArgumentParser(description="Rollback de acoes do auto_classifier")
    parser.add_argument("run_id", nargs="?", help="ID do run (deixe vazio para listar)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.run_id:
        runs = actions_log.list_runs(10)
        print("Ultimas execucoes:")
        for r in runs:
            print(f"  {r['run_id']:25s} {r['command']:20s} {r['status']:12s}")
        return

    rollback(args.run_id, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
