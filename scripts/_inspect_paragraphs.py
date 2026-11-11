import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

files = sys.argv[1:]
for name in files:
    path = RAW / name
    if not path.exists():
        path = ROOT / "data" / "_inspect" / name
    text = path.read_text(encoding="utf-8")
    print("\n" + "=" * 90)
    print(name, "chars", len(text))
    paras = [p.strip() for p in text.split("\n") if p.strip()]
    for i, p in enumerate(paras):
        print(f"[{i:03d}] ({len(p):4d}) {p[:120]}")
