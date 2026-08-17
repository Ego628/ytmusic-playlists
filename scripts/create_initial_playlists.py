"""
Cria as 3 playlists no YouTube Music conforme pedido explicito do usuario.
"""
import sys
from pathlib import Path
from ytmusicapi import YTMusic

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent.parent
AUTH_FILE = HERE / "data" / "browser.json"

PLAYLISTS = [
    {
        "name": "Clássicos & Atemporais",
        "description": "Jazz 30s, dream pop Y2K, new wave 80s, art pop — atemporais que dialogam entre épocas",
        "ids": [
            "1RJJHh-lZDE",  # Midnight, the Stars and You
            "zZLGokmJiLk",  # Dean Blunt - Galice
            "sPqTf6wRphE",  # Panchiko - DEATHMETAL
            "oIPFr7sOauw",  # Pretenders - Don't Tell A Lie
        ],
    },
    {
        "name": "Lowrider Nights",
        "description": "Chicano Soul / Lowrider Oldies — soul puro pra ouvir dirigindo devagar",
        "ids": [
            "x41DpERUw2E",  # Joey Quinones & Thee Sinseers
            "kertTmcZ-no",  # The Informers
            "j-77i1Qq2WA",  # High Desert United
            "DfbZp7mUKIs",  # Votabias
        ],
    },
    {
        "name": "Bass & Underground",
        "description": "Phonk + hardstyle + jumpstyle + horrorcore + weirdcore — tudo com bass forte",
        "ids": [
            "rxwRYGbMs9E",  # ZXVABEAT - LARPTEKK
            "gWBbLBUKhXU",  # taryu - KERTZAGEM
            "J6HDDrlrM-c",  # deonXQ - Major Tom
            "4HpC6IksiGI",  # HUSSVRX - TERRIBLE THOUGHTS
            "M0MuFG5lwWM",  # Empty/Stian K - Be Alive
            "YsgrrpayIuk",  # ٴ - febuary
            "7mWgZOsZpQw",  # saraunh0ly - mmm00nm0thz
            "lv4yi7SudVk",  # sematary - bunny suit
            "NFJ72G_8rLs",  # Jecjec - Winkles Twinkle
            "Jx7KiK49lEU",  # raq archives - YUKE APATHY
            "xeh_sYIeRCI",  # Iron wave - Andergrand
            "lhbi4YYBSaY",  # S-Class - i_ya_odna
            "Fa0MJNODGyU",  # rukiwaa/gnot - weirdcore
        ],
    },
]


def main():
    yt = YTMusic(str(AUTH_FILE))
    for pl in PLAYLISTS:
        print(f"Criando: {pl['name']} ({len(pl['ids'])} músicas)...")
        try:
            pid = yt.create_playlist(pl["name"], pl["description"])
            for i in range(0, len(pl["ids"]), 100):
                yt.add_playlist_items(pid, pl["ids"][i:i + 100])
            print(f"  [OK] https://music.youtube.com/playlist?list={pid}")
        except Exception as e:
            print(f"  [ERRO] {e}")


if __name__ == "__main__":
    main()
