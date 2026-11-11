import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

for path in sorted(RAW.glob("quan*_*.txt")):
    text = path.read_text(encoding="utf-8")
    print("\n" + "=" * 80)
    print(path.name, "chars", len(text))
    lines = text.splitlines()
    current = "(front matter)"
    start = 0
    sections = []
    for i, line in enumerate(lines):
        m = re.match(r"^(={3,4})\s*(.*?)\s*\1\s*$", line)
        if m:
            body = "\n".join(lines[start:i]).strip()
            sections.append((current, len(body), body[:90].replace("\n", " ")))
            current = f"{len(m.group(1))} {m.group(2)}"
            start = i + 1
    body = "\n".join(lines[start:]).strip()
    sections.append((current, len(body), body[:90].replace("\n", " ")))
    for heading, length, preview in sections:
        if length == 0 and heading == "(front matter)":
            continue
        print(f"{heading:40s} {length:6d}  {preview}")
