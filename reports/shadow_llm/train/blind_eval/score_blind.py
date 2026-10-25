"""
블라인드 정답(검수자가 모델 답 없이 단 y/n)으로 v2·v3·v3b·v3c 채점.
  /usr/bin/python3 reports/shadow_llm/train/blind_eval/score_blind.py answers.json
answers.json = 검수 페이지 '결과 복사' 내용 [{"id":"b001","c":"y","d":"n","u":1?}, ...]
"""
import json, sys, os
D = os.path.dirname(os.path.abspath(__file__)); T = os.path.dirname(D)
smp = {x["id"]: x for x in json.load(open(f"{D}/sample.json"))}
ans = {a["id"]: a for a in json.load(open(sys.argv[1])) if a.get("c") and a.get("d")}
def jl(p): return {json.loads(l)["id"]: json.loads(l) for l in open(p)}
M = {"v2 (운영)": (jl(f"{T}/ollama_v2/pred_test.jsonl"), jl(f"{D}/pred_v2.jsonl"))}
for v in ("v3", "v3b", "v3c"):
    M[v] = (jl(f"{T}/lora_q25_3b_{v}/pred_test_newgold.jsonl"), jl(f"{D}/pred_{v}.jsonl"))
def pred(m, x): return (M[m][1] if x["set"] == "ts_new" else M[m][0]).get(x["src"], {})
def f1(ids, m, k, gk):
    tp = fp = fn = 0
    for i in ids:
        g = ans[i][gk] == "y"; p = pred(m, smp[i]).get(k) == "y"
        tp += p and g; fp += p and not g; fn += g and not p
    P = tp / (tp + fp) if tp + fp else 0; R = tp / (tp + fn) if tp + fn else 0
    return (2 * P * R / (P + R) if P + R else 0) * 100, P * 100, R * 100, tp + fn, tp + fp
for name, ids in (("전체", list(ans)), ("일반", [i for i in ans if smp[i]["set"] == "general"]), ("트러블슈팅(새 문장)", [i for i in ans if smp[i]["set"] == "ts_new"])):
    if not ids: continue
    print(f"\n## {name} {len(ids)}문장 (정답 인용 y {sum(ans[i]['c']=='y' for i in ids)}, 정의 y {sum(ans[i]['d']=='y' for i in ids)}, 애매 {sum(1 for i in ids if ans[i].get('u'))})")
    for m in M:
        c = f1(ids, m, "citable", "c"); d = f1(ids, m, "definition", "d")
        print(f"  {m:9s} 인용 F1 {c[0]:5.1f} (P {c[1]:5.1f} R {c[2]:5.1f}, 예측y {c[4]})   정의 F1 {d[0]:5.1f} (P {d[1]:5.1f} R {d[2]:5.1f}, 예측y {d[4]})")
