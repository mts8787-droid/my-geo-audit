"""
올라마에 올린 감사 모델(hiro) 평가 — lora_data_v2/test.jsonl(1,052문장)로 라벨 3개 정밀도/재현율 + 문장당 시간.
시스템 프롬프트는 Modelfile에 내장돼 있으므로 user 메시지(문장)만 보낸다.
  /usr/bin/python3 ollama_eval.py --model hiro --out reports/shadow_llm/train/ollama_v2/pred_test.jsonl
"""
import argparse, json, sys, time, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="hiro")
ap.add_argument("--data", default="reports/shadow_llm/train/lora_data_v2/test.jsonl")
ap.add_argument("--out", required=True); ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--host", default="http://127.0.0.1:11434")
ap.add_argument("--ids", default="reports/shadow_llm/train/lora_data/test_ids.json")
a = ap.parse_args()

rows = [json.loads(l) for l in open(a.data) if l.strip()]
ids = json.load(open(a.ids))
if a.limit: rows, ids = rows[:a.limit], ids[:a.limit]
LAB = ("citable", "definition", "summary")
stats = {k: [0, 0, 0, 0] for k in LAB}
na = 0; t_all = 0.0

def chat(user):
    body = json.dumps({"model": a.model, "stream": False, "format": "json",
                       "messages": [{"role": "user", "content": user}],
                       "options": {"temperature": 0, "num_predict": 80}}).encode()
    req = urllib.request.Request(a.host + "/api/chat", body, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["message"]["content"]

with open(a.out, "w") as f:
    for i, (r, rid) in enumerate(zip(rows, ids), 1):
        user = r["messages"][1]["content"]; gold = json.loads(r["messages"][2]["content"])
        t0 = time.perf_counter()
        try: txt = chat(user)
        except Exception as e: txt = ""; print("ERR", rid, e, file=sys.stderr)
        t_all += time.perf_counter() - t0
        try: pred = json.loads(txt[txt.index("{"): txt.rindex("}") + 1])
        except Exception: pred = {}; na += 1
        rec = {"id": rid, "why": pred.get("why") if isinstance(pred.get("why"), str) else None}
        for k in LAB:
            v = pred.get(k) if pred.get(k) in ("y", "n") else None
            rec[k] = v
            if v is None: continue
            g = gold[k]; s = stats[k]
            if v == "y" and g == "y": s[0] += 1
            elif v == "y": s[1] += 1
            elif g == "y": s[2] += 1
            else: s[3] += 1
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if i % 100 == 0: print(f"[{i}/{len(rows)}] 무응답 {na} {t_all/i*1000:.0f}ms/문장", file=sys.stderr, flush=True)
print(f"예측 {len(rows)}문장, 파싱 실패 {na}, 문장당 {t_all/len(rows)*1000:.0f}ms (올라마 API 왕복)")
for k in LAB:
    tp, fp, fn, tn = stats[k]; n = tp + fp + fn + tn
    p = tp / (tp + fp) if tp + fp else 0; r = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * p * r / (p + r) if p + r else 0
    print(f"{k:11s} 일치 {(tp+tn)/n:5.1%}  정밀도 {p:5.1%}  재현율 {r:5.1%}  F1 {f1:5.1%}  (정답y {tp+fn}, 예측y {tp+fp})")
