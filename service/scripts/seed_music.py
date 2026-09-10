"""Nạp sẵn vài bài hát vào `music_tracks` để xem/thử trang "Quản lý nhạc"
trên web (KHÔNG tự xoá — khác sim_music_flow.py).

    python scripts/seed_music.py            # nạp vài query mẫu
    python scripts/seed_music.py --clear    # xoá sạch collection music_tracks
"""

import argparse
import pathlib
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import app.core.firebase as fb  # noqa: E402
from app.services import music_service  # noqa: E402

QUERIES = ["lofi", "acoustic chill", "piano relax", "vietnam indie"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear", action="store_true")
    args = parser.parse_args()

    if args.clear:
        n = 0
        for doc in fb.db.collection("music_tracks").stream():
            doc.reference.delete()
            n += 1
        print(f"Đã xoá {n} bài trong music_tracks")
        return

    total = 0
    for q in QUERIES:
        songs = music_service.search(q)
        total += len(songs)
        print(f"  '{q}': {len(songs)} bài đang bật")

    docs = list(fb.db.collection("music_tracks").stream())
    print(f"\nTổng cộng {len(docs)} bài trong music_tracks (một số có thể trùng).")
    print("→ Mở web admin trang 'Quản lý nhạc' để xem / thử tắt-bật.")


if __name__ == "__main__":
    main()
