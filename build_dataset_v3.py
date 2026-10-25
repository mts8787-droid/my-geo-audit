"""
v3b 라벨 데이터 구성 (2026-10-20).
기존 일반 페이지 라벨(dataset_v1)을 유지하되, 검수자가 정한 4개 유형만 결정대로 고친다(out_tag/*.jsonl 태그).
  footnote → 인용 n·정의 n·요약 n / kf_list → 인용 n·정의 n·요약 n / mechanism → 인용 y·정의 y / capacity → 인용 y
옛 데이터의 트러블슈팅 문장(미검수)은 트러블슈팅 기준(GUIDELINE_TS) 재라벨로 교체한다
(out_v3_rejected/ 의 TS 문장 + out_v3/ts_rest.jsonl).
사람 검수 문장도 태그가 있으면 결정대로 맞춘다(검수자 본인의 결정이 개별 판정보다 우선).
  /usr/bin/python3 build_dataset_v3.py  → reports/shadow_llm/train/dataset_v3.jsonl
v3c (2026-10-21): v3b 가 작동 설명=정의 y 를 일반 기능 소개문까지 넓혀 배워 정의문 과잉 판정 → mechanism 은 인용 y 만, 정의는 기존 라벨 유지.
  /usr/bin/python3 build_dataset_v3.py c  → reports/shadow_llm/train/dataset_v3c.jsonl
"""
import json, glob, collections, sys
VAR = sys.argv[1] if len(sys.argv) > 1 else ""
T = "reports/shadow_llm/train"
rows = [json.loads(l) for l in open(f"{T}/dataset_v1.jsonl")]
tags = {}
for f in glob.glob(f"{T}/out_tag/*.jsonl"):
    for l in open(f):
        r = json.loads(l); tags[r["id"]] = r
ts_lab = {}
for f in glob.glob(f"{T}/out_v3_rejected/*.jsonl") + [f"{T}/out_v3/ts_rest.jsonl"]:
    try:
        for l in open(f):
            r = json.loads(l); ts_lab[r["id"]] = r
    except FileNotFoundError:
        pass
RULE = {"footnote": {"citable": "n", "definition": "n", "summary": "n"},
        "kf_list": {"citable": "n", "definition": "n", "summary": "n"},
        "mechanism": {"citable": "y", "definition": "y"},
        "capacity": {"citable": "y"}}
if VAR == "c": RULE["mechanism"] = {"citable": "y"}
stat = collections.Counter(); out = []
for r in rows:
    r = dict(r); r["label_source"] = "v1"
    if r["page_type"] == "support_troubleshoot":
        if not r.get("human_reviewed") and r["id"] in ts_lab:
            l = ts_lab[r["id"]]
            for k in ("citable", "definition"): r[k] = l[k]
            r["summary"] = "n"; r["why"] = l.get("why", ""); r["label_source"] = "ts_standard"; stat["ts_relabel"] += 1
        elif not r.get("human_reviewed"):
            stat["ts_missing"] += 1
    else:
        t = tags.get(r["id"])
        if t and t["tag"] in RULE:
            ch = [k for k, v in RULE[t["tag"]].items() if r[k] != v]
            for k, v in RULE[t["tag"]].items(): r[k] = v
            r["tag"] = t["tag"]
            if ch:
                r["why"] = t.get("why") or r.get("why", ""); r["label_source"] = f"decision:{t['tag']}"
                stat[f"changed:{t['tag']}"] += 1
                if r.get("human_reviewed"): stat["changed_human"] += 1
            stat[f"tag:{t['tag']}"] += 1
        elif not t:
            stat["untagged"] += 1
    out.append(r)
with open(f"{T}/dataset_v3{VAR}.jsonl", "w") as f:
    for r in out: f.write(json.dumps(r, ensure_ascii=False) + "\n")
c = sum(r["citable"] == "y" for r in out); d = sum(r["definition"] == "y" for r in out)
print(dict(stat)); print(f"dataset_v3{VAR}: {len(out)}문장, 인용 y {c} ({c/len(out):.1%}), 정의 y {d} ({d/len(out):.1%})")
