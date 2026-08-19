"""
Setup de autenticacao via Browser Headers.

Passos:
1. Abra https://music.youtube.com e faca login
2. F12 -> Network -> filtro "youtubei" -> recarregue (F5)
3. Clique em qualquer requisicao /youtubei/
4. Aba Headers -> Request Headers -> botao direito -> Copy -> Copy as cURL (bash)
5. Rode este script e cole o cURL
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ytmusicapi

HERE = Path(__file__).parent
DATA_DIR = HERE.parent / "data"
AUTH_FILE = DATA_DIR / "browser.json"


def main():
    DATA_DIR.mkdir(exist_ok=True)

    print("=" * 70)
    print("  AUTENTICACAO YOUTUBE MUSIC (Browser Headers)")
    print("=" * 70)
    print()
    print("Passos:")
    print("1. Abra https://music.youtube.com e faca login")
    print("2. F12 -> Network -> filtro 'youtubei' -> recarregue (F5)")
    print("3. Clique em qualquer requisicao /youtubei/")
    print("4. Aba Headers -> Request Headers -> botao direito -> Copy -> Copy as cURL (bash)")
    print()
    print("Cole o cURL copiado abaixo e pressione ENTER DUAS VEZES:")
    print("(Para sair sem colar: Ctrl+C)")
    print()

    headers = sys.stdin.read()
    ytmusicapi.setup(filepath=str(AUTH_FILE), headers_raw=headers)

    print(f"\n[OK] Credenciais salvas em: {AUTH_FILE}")
    print("[OK] Teste rapido...")

    from ytmusicapi import YTMusic
    yt = YTMusic(str(AUTH_FILE))
    liked = yt.get_liked_songs(limit=3)
    n = len(liked.get("tracks", []))
    print(f"[OK] Acesso confirmado (amostra de {n} musicas)")
    print()
    print("Agora voce pode rodar:")
    print("  python scripts/auto_classifier.py --dry-run")


if __name__ == "__main__":
    main()
