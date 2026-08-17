"""
Autenticacao no YouTube Music via Browser Headers (cookies).

Passos:
1. Abra https://music.youtube.com e faca login
2. F12 -> Network -> filtro "youtubei" -> recarregue (F5)
3. Clique em qualquer requisicao /youtubei/
4. Aba Headers -> Request Headers -> botao direito -> Copy -> Copy as cURL (bash)
5. Rode este script e cole o cURL
"""
import sys
from pathlib import Path
import ytmusicapi

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent.parent
DATA_DIR = HERE / "data"
AUTH_FILE = DATA_DIR / "browser.json"


def main():
    DATA_DIR.mkdir(exist_ok=True)

    print("=" * 70)
    print("  AUTENTICACAO YOUTUBE MUSIC (Browser Headers)")
    print("=" * 70)
    print()
    print("Cole o cURL copiado do DevTools e pressione ENTER DUAS VEZES.")
    print("(Para sair sem colar: Ctrl+C)")
    print()

    ytmusicapi.setup(filepath=str(AUTH_FILE), headers_raw=sys.stdin)

    # Teste rapido
    from ytmusicapi import YTMusic
    yt = YTMusic(str(AUTH_FILE))
    liked = yt.get_liked_songs(limit=3)
    n = len(liked.get("tracks", []))
    print(f"\n[OK] Credenciais salvas em: {AUTH_FILE}")
    print(f"[OK] Teste: acesso confirmado (amostra de {n} musicas)")
    print("[OK] Agora voce pode rodar: python scripts/suggest_playlists.py")


if __name__ == "__main__":
    main()
