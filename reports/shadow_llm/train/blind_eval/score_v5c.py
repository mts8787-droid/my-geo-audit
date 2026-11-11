import json, os
D = "/Users/dubaba/my-geo-project/my-geo-audit/reports/shadow_llm/train/blind_eval"; T = os.path.dirname(D)
def jl(p): return {json.loads(l)["id"]: json.loads(l) for l in open(p)}
def f1(pairs):
    tp=sum(p and g for p,g in pairs); fp=sum(p and not g for p,g in pairs); fn=sum(g and not p for p,g in pairs)
    P=tp/(tp+fp) if tp+fp else 0; R=tp/(tp+fn) if tp+fn else 0
    return f"F1 {(2*P*R/(P+R) if P+R else 0)*100:5.1f} (P {P*100:5.1f} R {R*100:5.1f}, 예측y {tp+fp:3d})"
smp = {x["id"]: x for x in json.load(open(f"{D}/sample.json"))}
v4g = jl(f"{D}/pred_v4_general.jsonl"); v4t = jl(f"{D}/pred_v4_ts.jsonl"); v5g = jl(f"{D}/pred_v5_general.jsonl"); v5t = jl(f"{D}/pred_v5_ts.jsonl"); v5f = jl(f"{D}/pred_v5_flip4.jsonl"); v6g = jl(f"{D}/pred_v5b_general.jsonl"); v6t = jl(f"{D}/pred_v5b_ts.jsonl"); v6f = jl(f"{D}/pred_v5b_flip4.jsonl"); v7g = jl(f"{D}/pred_v5c_general.jsonl"); v7t = jl(f"{D}/pred_v5c_ts.jsonl"); v7f = jl(f"{D}/pred_v5c_flip4.jsonl")
old = {"v2": (jl(f"{T}/ollama_v2/pred_test.jsonl"), jl(f"{D}/pred_v2.jsonl")),
       "v3d": (jl(f"{T}/lora_q25_3b_v3d/pred_test_newgold.jsonl"), jl(f"{D}/pred_v3d.jsonl"))}
def pred(m, i):
    x = smp[i]
    if m == "v4": return (v4t if x["set"]=="ts_new" else v4g).get(i, {})
    if m == "v5": return (v5t if x["set"]=="ts_new" else v5g).get(i, {})
    if m == "v5b": return (v6t if x["set"]=="ts_new" else v6g).get(i, {})
    if m == "v5c": return (v7t if x["set"]=="ts_new" else v7g).get(i, {})
    return (old[m][1] if x["set"]=="ts_new" else old[m][0]).get(x["src"], {})
for gf, label in (("answers_1024rule.json","10-24 규칙"), ("answers_v4rule.json","v4 기준(69 재판정)")):
    ans = {a["id"]: a for a in json.load(open(f"{D}/{gf}")) if a.get("c")}
    for name, st in (("일반", "general"), ("트러블슈팅", "ts_new")):
        ids = [i for i in ans if smp[i]["set"]==st]
        if not ids: continue
        print(f"\n## {name} {len(ids)} [{label}] 정답y {sum(ans[i]['c']=='y' for i in ids)}")
        for m in ("v2","v3d","v4","v5","v5b","v5c"):
            print(f"  {m:4s} 인용 {f1([(pred(m,i).get('citable')=='y', ans[i]['c']=='y') for i in ids])}   정의 {f1([(pred(m,i).get('definition')=='y', ans[i].get('d')=='y') for i in ids])}")
fs = {x["id"]: x for x in json.load(open(f"{D}/flip4_sample.json"))}
ho = json.load(open(f"{D}/flip4_holdout_ids.json")); v4f = jl(f"{D}/pred_v4_flip4.jsonl")
for name, ids in (("flip4 holdout 전체", ho), ("  후보(숫자)", [i for i in ho if fs[i]["kind"]=="candidate"]), ("  본문", [i for i in ho if fs[i]["kind"]=="body"])):
    print(f"\n## {name} {len(ids)} 정답y {sum(fs[i]['answer']=='y' for i in ids)}")
    for m in ("v2","v3d","v4","v5","v5b","v5c"):
        p = (lambda i: v4f[i].get("citable")=="y") if m=="v4" else (lambda i: v5f[i].get("citable")=="y") if m=="v5" else (lambda i: v6f[i].get("citable")=="y") if m=="v5b" else (lambda i: v7f[i].get("citable")=="y") if m=="v5c" else (lambda i: fs[i][m]=="y")
        print(f"  {m:4s} 인용 {f1([(p(i), fs[i]['answer']=='y') for i in ids])}")
