import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "data" / "v3" / "_inspect"

path = BASE / sys.argv[1]
title = sys.argv[2]
text = path.read_text(encoding="utf-8")
pattern = re.compile(rf"^(={{2,5}})\s*{re.escape(title)}\s*\1\s*$", re.M)
match = pattern.search(text)
if not match:
    print("SECTION NOT FOUND", title)
    sys.exit(1)
start = match.end()
next_heading = re.search(r"^={2,5}\s*", text[start:], re.M)
end = start + next_heading.start() if next_heading else len(text)
body = text[start:end]
print("chars", len(body))
paras = [p.strip() for p in body.splitlines() if p.strip()]
for i, p in enumerate(paras):
    print(f"[{i:03d}] ({len(p):4d}) {p[:300]}")
