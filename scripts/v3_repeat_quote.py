# -*- coding: utf-8 -*-
"""Check W06-015 / E11-018 positions across v2/v3 splits."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "v3"
IDS = ["W06-015", "E11-018"]


def pos_from_random(path, label):
    df = pd.read_csv(path, encoding="utf-8-sig")
    rows = []
    for sid in IDS:
        sub = df[df["sent_id"] == sid]
        if sub.empty:
            rows.append({"split": label, "sent_id": sid, "position": "not in sample"})
        else:
            row = sub.iloc[0]
            rows.append({
                "split": label, "sent_id": sid, "work_title": row["work_title"],
                "author": row["author"], "period": row["period"],
                "position": row["split"],
            })
    return rows


def pos_from_group(path, label):
    df = pd.read_csv(path, encoding="utf-8-sig")
    mapping = dict(zip(df["work_id"], df["split"]))
    rows = []
    for sid in IDS:
        wid = sid.split("-")[0]
        rows.append({
            "split": label, "sent_id": sid,
            "work_title": "法言·吾子（節選）" if sid.startswith("W06") else "漢書·藝文志（詩、詩賦略節選）",
            "author": "揚雄" if sid.startswith("W06") else "班固",
            "period": "西漢" if sid.startswith("W06") else "東漢",
            "position": mapping.get(wid, "not in split"),
        })
    return rows


def pos_from_pair(path, label):
    info = json.loads(Path(path).read_text(encoding="utf-8"))
    test_authors = set(info["test_authors"])
    rows = []
    for sid, author, title, period in [
        ("W06-015", "揚雄", "法言·吾子（節選）", "西漢"),
        ("E11-018", "班固", "漢書·藝文志（詩、詩賦略節選）", "東漢"),
    ]:
        rows.append({
            "split": label,
            "sent_id": sid,
            "work_title": title,
            "author": author,
            "period": period,
            "position": "test" if author in test_authors else "train",
            "note": f"test_authors={sorted(test_authors)}",
        })
    return rows


def main():
    rows = []
    rows += pos_from_random(ROOT / "data" / "dataset_v2.csv", "v2_main")
    rows += pos_from_group(ROOT / "output" / "grouped" / "group_split.csv", "v2_grouped")
    rows += pos_from_random(ROOT / "data" / "v3" / "dataset_labelonly.csv", "v3_labelonly")
    rows += pos_from_random(ROOT / "data" / "v3" / "dataset_v3.csv", "v3_main")
    rows += pos_from_group(ROOT / "output" / "v3" / "grouped" / "group_split.csv", "v3_grouped")

    # genre experiment: W06 is 子書; E11 is 史書, outside 子書 test
    main = pd.read_csv(ROOT / "data" / "v3" / "dataset_v3.csv", encoding="utf-8-sig")
    for sid, title, author, period, genre in [
        ("W06-015", "法言·吾子（節選）", "揚雄", "西漢", "子書"),
        ("E11-018", "漢書·藝文志（詩、詩賦略節選）", "班固", "東漢", "史書"),
    ]:
        sub = main[main["sent_id"] == sid]
        if sid == "W06-015" and not sub.empty:
            position = sub.iloc[0]["split"] + "（子書 held-out 以此 split 為準）"
        elif sid == "E11-018":
            position = "not in 子書 test（史書）"
        else:
            position = "not in sample"
        rows.append({"split": "v3_genre_experiment", "sent_id": sid,
                     "work_title": title, "author": author, "period": period,
                     "position": position})

    for pair in ["P1_liuan_wangchong", "P2_liuan_huantan",
                 "P3_yangxiong_wangchong", "P4_yangxiong_huantan"]:
        path = ROOT / "output" / "v3" / "author_pairings" / pair / "split_info.json"
        if path.exists():
            rows += pos_from_pair(path, f"v3_{pair}")

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "repeat_quote_positions.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# W06-015／E11-018 重引例位置",
        "",
        "共享引文：「詩人之賦麗以則，辭人之賦麗以淫」。",
        "",
        "| split | sent_id | 篇名 | 作者 | 分期 | 位置 |",
        "|---|---|---|---|---|---|",
    ]
    for _, row in df.iterrows():
        lines.append(
            f"| {row['split']} | {row['sent_id']} | {row.get('work_title', '')} | "
            f"{row.get('author', '')} | {row.get('period', '')} | {row['position']} |")
    lines += [
        "",
        "注意：v2_main 與 v3_labelonly 兩者都在測試；v3_main 與 v3_grouped 兩者都在訓練。",
        "v2_grouped 是 W06 在訓練、E11 在測試，才是重引跨切分的實例。",
        "作者配對中，W06 在 P3/P4 為測試、P1/P2 為訓練；E11 在四組皆為訓練。",
        "",
    ]
    (OUT / "repeat_quote_positions.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
