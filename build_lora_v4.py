"""
v4 학습 데이터 (2026-11-09 사용자 결정): 일반 페이지 인용 y = 숫자·연도·통계·인증·EEAT + 특허·고유 기술 설명 + 사용 편익,
단 마케팅 문구·"최고의·혁신적인·최상의" 류 수식어가 있으면 n (GUIDELINE.md 끝, LABEL_V4.md).
  - 일반: dataset_v3c 의 citable 을 LABEL_V4 기준 재라벨(Claude, 블라인드 142문장 F1 76 확인)로 교체.
    블라인드 평가 문장(sample.json·flip4_sample.json)과 같은 텍스트는 학습에서 뺀다.
  - 11월 #36 재판정에서 빠진 문장 202개 추가(flip4 평가 페이지와 같은 URL 제외). 정의·요약은 v3d 판정값.
  - 트러블슈팅: v3d 와 같은 dataset_ts_v2 (10-24 기준).
  - 시스템 프롬프트 citable 정의를 새 기준으로 교체 → Modelfile.v4 SYSTEM 도 같은 문구여야 한다.
  /usr/bin/python3 build_lora_v4.py <재라벨 폴더(out_*.json)> <extra_rows.json> <extra_v3d.json> [v4b]
v4b (2026-11-10): v4 가 일반 블라인드 재현율 56% 로 과엄격 → LABEL_V4B(수치 없어도 기술 동작 설명 y, 시험·인증 각주 y)로
  재라벨한 폴더를 주고 4번째 인자 v4b → lora_data_v4b, 시스템 프롬프트도 같은 보정.
"""
import json, os, random, sys, glob
LAB, EXTRA, EXTRA_V3D = sys.argv[1], sys.argv[2], sys.argv[3]
VER = sys.argv[4] if len(sys.argv) > 4 else "v4"
T = "reports/shadow_llm/train"; OUT = f"{T}/lora_data_{VER}"; os.makedirs(OUT, exist_ok=True)
random.seed(13)
OLD_SYSTEM = json.loads(open(f"{T}/lora_data_v3d/train.jsonl").readline())["messages"][0]["content"]
OLD_C = OLD_SYSTEM.split("\n")[1]
NEW_C = ("citable: a sentence an AI assistant could quote as fact: a number, year, statistic, certification, test, patent, "
         "award with source or expert/clinical evidence; an explanation of what a named LG technology is and how it works; "
         "a concrete user benefit or usage fact; a definition. Not: marketing copy, slogans, sentences decorated with praise "
         "words (best, innovative, ultimate, perfect, revolutionary), vague convenience or app-control claims, effects without "
         "concrete basis, menus, spec fragments, promotions, prices, legal text, footnotes, instructions, company news.")
if VER == "v4b":
    NEW_C = ("citable: a sentence an AI assistant could quote as fact: a number, year, statistic, certification, test, patent, "
             "award with source or expert/clinical evidence; an explanation of what a named LG technology detects, learns, "
             "adjusts or removes (no number needed); a concrete user benefit or usage fact; a definition; a footnote stating a "
             "test, certification or study condition. Not: marketing copy, slogans, sentences decorated with praise words (best, "
             "innovative, ultimate, perfect, revolutionary), vague convenience or app-control claims, effects without a stated "
             "mechanism or basis, menus, spec fragments, promotions, prices, legal or promotional footnotes, instructions, company news.")
assert OLD_C.startswith("citable:")
SYSTEM = OLD_SYSTEM.replace(OLD_C, NEW_C)
open(f"{OUT}/system.txt", "w").write(SYSTEM)
lab = {}
for p in glob.glob(f"{LAB}/out_*.json"):
    lab.update(json.load(open(p)))
cl = {r["id"]: r for r in json.load(open(f"{T}/claude_labels.json"))}
blind = {x["text"] for x in json.load(open(f"{T}/blind_eval/sample.json"))} | \
        {x["text"] for x in json.load(open(f"{T}/blind_eval/flip4_sample.json"))}
def why(r):
    if r.get("label_source", "v1") != "v1": return r.get("why") or ""
    return r.get("why") or cl.get(r["id"], {}).get("why", "")
gen, changed = [], 0
for l in open(f"{T}/dataset_v3c.jsonl"):
    r = json.loads(l)
    if r["text"] in blind: continue
    if r.get("page_type") == "support_troubleshoot":  # 트러블슈팅 문장은 v3c 라벨 그대로(10-24 기준)
        gen.append(r); continue
    n = lab[r["id"]]
    w = why(r)
    if n["c"] != r["citable"]:
        changed += 1; w = n["why"]
    gen.append({**r, "citable": n["c"], "why": w, "label_source": "v4"})
ev3d = json.load(open(EXTRA_V3D))
for x in json.load(open(EXTRA)):
    d = ev3d.get(x["id"], {})
    gen.append({"id": x["id"], "text": x["text"], "page_type": x["page_type"], "citable": lab[x["id"]]["c"],
                "definition": d.get("definition") or "n", "summary": d.get("summary") or "n",
                "why": lab[x["id"]]["why"], "label_source": "v4"})
ts = [json.loads(l) for l in open(f"{T}/dataset_ts_v2.jsonl")]
def ex(r):
    out = {"citable": r["citable"], "definition": r["definition"], "summary": r["summary"], "why": why(r) if r.get("label_source") != "v4" else r["why"]}
    return {"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": r["text"]},
                         {"role": "assistant", "content": json.dumps(out, ensure_ascii=False)}]}
test_ids = set(json.load(open(f"{T}/lora_data/test_ids.json")))
ts_test_ids = set(json.load(open(f"{T}/lora_data_v3/test_ts_ids.json")))
g_test = [r for r in gen if r["id"] in test_ids]
g_rest = [r for r in gen if r["id"] not in test_ids]; random.shuffle(g_rest)
g_valid, g_train = g_rest[:300], g_rest[300:]
t_test = [r for r in ts if r["id"] in ts_test_ids]
t_rest = [r for r in ts if r["id"] not in ts_test_ids]; random.shuffle(t_rest)
t_valid, t_train = t_rest[:200], t_rest[200:]
for name, rows in (("train", g_train + t_train), ("valid", g_valid + t_valid), ("test", g_test), ("test_ts", t_test)):
    if name in ("train", "valid"): random.shuffle(rows)
    with open(f"{OUT}/{name}.jsonl", "w") as f:
        for r in rows: f.write(json.dumps(ex(r), ensure_ascii=False) + "\n")
    print(name, len(rows))
json.dump([r["id"] for r in g_test], open(f"{OUT}/test_ids.json", "w"))
json.dump([r["id"] for r in t_test], open(f"{OUT}/test_ts_ids.json", "w"))
print("일반", len(gen), "인용 라벨 변경", changed, "인용 y", sum(r["citable"] == "y" for r in gen))
