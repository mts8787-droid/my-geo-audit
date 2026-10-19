"""
LoRA 어댑터 평가 — lora_data/test.jsonl(1,052문장, Few-shot 평가셋과 동일)로 라벨 3개 정밀도/재현율.
  ~/.venvs/mlx/bin/python lora_eval.py --model <base> --adapter <dir> [--out pred.jsonl]
"""
import argparse, json, sys, time
from mlx_lm import load, generate
from mlx_lm.sample_utils import make_sampler

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True); ap.add_argument("--adapter", default=None)
ap.add_argument("--data", default="reports/shadow_llm/train/lora_data/test.jsonl")
ap.add_argument("--out", required=True); ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--ids", default="reports/shadow_llm/train/lora_data/test_ids.json")
a = ap.parse_args()

model, tok = load(a.model, adapter_path=a.adapter)
rows = [json.loads(l) for l in open(a.data) if l.strip()]
ids = json.load(open(a.ids))
if a.limit: rows, ids = rows[:a.limit], ids[:a.limit]
sampler = make_sampler(temp=0.0)
LAB = ("citable", "definition", "summary")
stats = {k: [0, 0, 0, 0] for k in LAB}  # tp fp fn tn
na = 0
t_all = 0.0
with open(a.out, "w") as f:
    for i, (r, rid) in enumerate(zip(rows, ids), 1):
        msgs = r["messages"][:2]
        gold = json.loads(r["messages"][2]["content"])
        prompt = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
        t0 = time.perf_counter()
        txt = generate(model, tok, prompt=prompt, max_tokens=80, sampler=sampler, verbose=False)
        t_all += time.perf_counter() - t0
        try:
            pred = json.loads(txt[txt.index("{"): txt.rindex("}") + 1])
        except Exception:
            pred = {}; na += 1
        rec = {"id": rid, "why": pred.get("why") if isinstance(pred.get("why"), str) else None}
        for k in LAB:
            v = pred.get(k) if pred.get(k) in ("y", "n") else None
            rec[k] = v
            if v is None: continue
            g = gold[k]
            s = stats[k]
            if v == "y" and g == "y": s[0] += 1
            elif v == "y": s[1] += 1
            elif g == "y": s[2] += 1
            else: s[3] += 1
        f.write(json.dumps(rec) + "\n")
        if i % 100 == 0: print(f"[{i}/{len(rows)}] 무응답 {na}", file=sys.stderr, flush=True)
print(f"예측 {len(rows)}문장, 파싱 실패 {na}, 문장당 {t_all/len(rows)*1000:.0f}ms (생성만, 모델 로드 제외)")
for k in LAB:
    tp, fp, fn, tn = stats[k]; n = tp + fp + fn + tn
    p = tp / (tp + fp) if tp + fp else 0; r = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * p * r / (p + r) if p + r else 0
    print(f"{k:11s} 일치 {(tp+tn)/n:5.1%}  정밀도 {p:5.1%}  재현율 {r:5.1%}  F1 {f1:5.1%}  (정답y {tp+fn}, 예측y {tp+fp})")
