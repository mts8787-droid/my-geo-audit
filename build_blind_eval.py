"""
블라인드 평가 정답지 표본 (2026-10-21).
기존 검수는 '라벨 vs v2 답' 중 고르는 방식이라 정답의 절반 이상이 v2 답 그 자체 → v2 에 유리한 착시.
어떤 모델 답도 보여주지 않고 검수자가 직접 y/n 을 다는 300문장을 뽑는다.
  - 일반 200: 어느 모델도 학습하지 않은 평가셋(test 1,052) 중 사람이 본 적 없는 문장.
    y 후보(라벨·v2·v3·v3b·v3c 중 하나라도 인용·정의 y) 전부 + 전부 n 무작위. 모든 모델에 대칭이라 비교는 공정하고 y 가 드문 문제를 보완.
  - 트러블슈팅 100: 미검수 test_ts 에 y 후보가 11개뿐이라, 학습·검수에 안 쓴 페이지에서 새로 뽑은 문장(blind_ts_extract.py)
    정규식 후보 50 · 본문 앞부분 30 · 무작위 20 — 모델 예측으로 고르지 않음.
  /usr/bin/python3 build_blind_eval.py → reports/shadow_llm/train/blind_eval/sample.json
"""
import json, os, random, re
T = "reports/shadow_llm/train"; OUT = f"{T}/blind_eval"; os.makedirs(OUT, exist_ok=True)
random.seed(21)
def jl(p): return {json.loads(l)["id"]: json.loads(l) for l in open(p)}
def preds(p):
    if p.endswith(".json"): return json.load(open(p))
    return jl(p)
gen = jl(f"{T}/dataset_v3.jsonl"); ts = jl(f"{T}/dataset_ts_v1.jsonl")
ko = {r["id"]: r.get("ko", "") for r in json.load(open(f"{T}/claude_labels.json"))}
g_ids = json.load(open(f"{T}/lora_data_v3b/test_ids.json")); t_ids = json.load(open(f"{T}/lora_data_v3b/test_ts_ids.json"))
P_g = [preds(f"{T}/ollama_v2/pred_test.jsonl")] + [preds(f"{T}/lora_q25_3b_{v}/pred_test_newgold.jsonl") for v in ("v3", "v3b", "v3c")]
def any_y(r, P):
    srcs = [r] + [p.get(r["id"], {}) for p in P]
    return any(s.get(k) == "y" for s in srcs for k in ("citable", "definition"))
def pick(rows, P, n_pos, n_neg):
    pos = [r for r in rows if any_y(r, P)]; neg = [r for r in rows if not any_y(r, P)]
    random.shuffle(pos); random.shuffle(neg)
    return pos[:n_pos] + neg[:n_neg], len(pos), len(neg)
g_rows = [gen[i] for i in g_ids if not gen[i].get("human_reviewed")]
g_s, gp, gn = pick(g_rows, P_g, 200, 0); g_s += random.sample([r for r in g_rows if r not in g_s], 200 - len(g_s))
tp = json.load(open(f"{OUT}/ts_pool.json")); t_s = []
_u = {}
for r in tp: _u.setdefault(re.sub(r"\s+", " ", r["text"]).strip().lower(), r)
tp = list(_u.values())  # 페이지 간 같은 문장 중복 제거
for grp, n in (("cand", 50), ("head", 30), ("rand", 20)):
    t_s += random.sample([r for r in tp if r["group"] == grp], n)
for k, r in enumerate(t_s): r["id"] = f"new{k:03d}"
sample = [{"src": r["id"], "text": r["text"], "cc": r["cc"], "page_type": r["page_type"], "ko": ko.get(r["id"], ""), "url": r.get("url", ""), "set": "ts_new" if r["id"].startswith("new") else "general"} for r in g_s + t_s]
random.shuffle(sample)
for k, s in enumerate(sample, 1): s["id"] = f"b{k:03d}"
json.dump(sample, open(f"{OUT}/sample.json", "w"), ensure_ascii=False, indent=1)
print(f"일반 후보 {len(g_rows)}(y후보 {gp}) → {len(g_s)} / 트러블슈팅 새 문장 → {len(t_s)} / 번역 없음 {sum(1 for s in sample if not s['ko'])}")
