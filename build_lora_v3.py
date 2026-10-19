"""
v3 학습 데이터 구성 (2026-10-20): v2 학습·검증셋(일반 페이지, lora_data_v2) + 트러블슈팅 검수 완료 라벨(dataset_ts_v1.jsonl).
  - lora_data_v3/train.jsonl : v2 train + ts train
  - lora_data_v3/valid.jsonl : v2 valid + ts valid
  - lora_data_v3/test.jsonl  : v2 test(1,052, 보정 gold) 그대로 — 기존 평가와 비교용
  - lora_data_v3/test_ts.jsonl : ts 홀드아웃 — 트러블슈팅 성능 비교용 (ids: test_ts_ids.json)
시스템 프롬프트는 v2 와 동일(올라마 Modelfile 에 박혀 있으므로 바꾸지 않는다).
  /usr/bin/python3 build_lora_v3.py
"""
import json, os, random
T = "reports/shadow_llm/train"; OUT = f"{T}/lora_data_v3"; os.makedirs(OUT, exist_ok=True)
random.seed(11)
v2 = {s: [json.loads(l) for l in open(f"{T}/lora_data_v2/{s}.jsonl")] for s in ("train", "valid", "test")}
SYSTEM = v2["train"][0]["messages"][0]["content"]
ts = [json.loads(l) for l in open(f"{T}/dataset_ts_v1.jsonl")]

def ex(r):
    out = {"citable": r["citable"], "definition": r["definition"], "summary": r["summary"], "why": r["why"]}
    return {"messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": r["text"]},
                         {"role": "assistant", "content": json.dumps(out, ensure_ascii=False)}]}

# ts 홀드아웃: 국가별 균등 + 양성(인용/정의 y) 비율 유지 → 약 600문장
pos = [r for r in ts if r["citable"] == "y" or r["definition"] == "y"]; neg = [r for r in ts if r not in pos]
random.shuffle(pos); random.shuffle(neg)
np = len(pos) * 2 // 5
test_ts = pos[:np] + neg[: 500 - np]
tid = {r["id"] for r in test_ts}
rest = [r for r in ts if r["id"] not in tid]; random.shuffle(rest)
valid_ts, train_ts = rest[:200], rest[200:]

for name, rows in (("train", v2["train"] + [ex(r) for r in train_ts]), ("valid", v2["valid"] + [ex(r) for r in valid_ts]),
                   ("test", v2["test"]), ("test_ts", [ex(r) for r in test_ts])):
    if name != "test": random.shuffle(rows)
    with open(f"{OUT}/{name}.jsonl", "w") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{name}: {len(rows)}")
json.dump([r["id"] for r in test_ts], open(f"{OUT}/test_ts_ids.json", "w"))
print(f"ts 분할: train {len(train_ts)} valid {len(valid_ts)} test {len(test_ts)} (양성 {sum(1 for r in test_ts if r in pos)})")
