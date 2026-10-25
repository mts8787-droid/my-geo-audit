"""
v3b 학습 데이터 (2026-10-20): dataset_v3(4개 유형 결정 적용 + 옛 트러블슈팅 문장 TS 기준) + 트러블슈팅 검수 라벨(dataset_ts_v1).
  - 일반 test 1,052 는 test_ids 그대로, 정답은 dataset_v3 기준(결정 반영) → lora_data_v3b/test.jsonl
  - 트러블슈팅 홀드아웃은 v3 와 같은 test_ts(lora_data_v3/test_ts_ids.json)
  - v2·v3·v3b 를 모두 이 정답으로 채점해야 비교가 공정하다.
  /usr/bin/python3 build_lora_v3b.py
v3c: /usr/bin/python3 build_lora_v3b.py c → dataset_v3c 로 lora_data_v3c (평가는 lora_data_v3b 의 test 로 해야 같은 정답)
v3d (2026-10-24): 일반은 dataset_v3c 그대로, 트러블슈팅은 dataset_ts_v2(원인·증상 설명문 = 인용 y, 사용자 결정) → lora_data_v3d.
  test_ts 정답이 바뀌므로 트러블슈팅 비교는 lora_data_v3d/test_ts 로 v2·v3c 를 다시 채점해야 공정하다.
  /usr/bin/python3 build_lora_v3b.py d
"""
import json, os, random, sys
VAR = sys.argv[1] if len(sys.argv) > 1 else "b"
T = "reports/shadow_llm/train"; OUT = f"{T}/lora_data_v3{VAR}"; os.makedirs(OUT, exist_ok=True)
random.seed(13)
SYSTEM = json.loads(open(f"{T}/lora_data_v2/train.jsonl").readline())["messages"][0]["content"]
cl = {r["id"]: r for r in json.load(open(f"{T}/claude_labels.json"))}
GEN_VAR = {"b": "", "d": "c"}.get(VAR, VAR)
gen = [json.loads(l) for l in open(f"{T}/dataset_v3{GEN_VAR}.jsonl")]
ts = [json.loads(l) for l in open(f"{T}/dataset_ts_{'v2' if VAR == 'd' else 'v1'}.jsonl")]
test_ids = set(json.load(open(f"{T}/lora_data/test_ids.json")))
ts_test_ids = set(json.load(open(f"{T}/lora_data_v3/test_ts_ids.json")))

def why(r):
    if r.get("label_source", "v1") != "v1": return r.get("why") or ""
    return r.get("why") or cl.get(r["id"], {}).get("why", "")

def ex(r):
    out = {"citable": r["citable"], "definition": r["definition"], "summary": r["summary"], "why": why(r)}
    return {"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": r["text"]},
                         {"role": "assistant", "content": json.dumps(out, ensure_ascii=False)}]}

g_test = [r for r in gen if r["id"] in test_ids]
g_rest = [r for r in gen if r["id"] not in test_ids]; random.shuffle(g_rest)
g_valid, g_train = g_rest[:300], g_rest[300:]
t_test = [r for r in ts if r["id"] in ts_test_ids]
t_rest = [r for r in ts if r["id"] not in ts_test_ids]; random.shuffle(t_rest)
t_valid, t_train = t_rest[:200], t_rest[200:]
order = {i: k for k, i in enumerate(json.load(open(f"{T}/lora_data/test_ids.json")))}
g_test.sort(key=lambda r: order[r["id"]])
for name, rows in (("train", g_train + t_train), ("valid", g_valid + t_valid), ("test", g_test), ("test_ts", t_test)):
    if name in ("train", "valid"): random.shuffle(rows)
    with open(f"{OUT}/{name}.jsonl", "w") as f:
        for r in rows: f.write(json.dumps(ex(r), ensure_ascii=False) + "\n")
    print(name, len(rows))
json.dump([r["id"] for r in g_test], open(f"{OUT}/test_ids.json", "w"))
json.dump([r["id"] for r in t_test], open(f"{OUT}/test_ts_ids.json", "w"))
