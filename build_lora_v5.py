"""
v5 학습 데이터 (2026-11-10 사용자 결정: 모델 하나를 최신으로, v2·v4 혼용 금지):
  - 일반 페이지: v2 와 같은 라벨·이유(lora_data_v2). 무작위 일반 블라인드 199문장(11-09 새 기준 정답)에서 v2 F1 85.2 로
    v3d 70.3·v4 68.6 보다 높았다. v3·v4 는 일반 라벨을 재라벨해 재현율이 떨어졌다.
  - 트러블슈팅: v3d·v4 와 같은 10-24 기준 데이터(lora_data_v3d 의 트러블슈팅 행). 블라인드 TS 100 F1 v4 61.1·v3d 54.1·v2 8.3.
  - 시스템 프롬프트: v2·v3d 와 같음(바꾸지 않음).
  /usr/bin/python3 build_lora_v5.py
"""
import json, os, random
T = "reports/shadow_llm/train"; OUT = f"{T}/lora_data_v5"; os.makedirs(OUT, exist_ok=True)
random.seed(13)
ts_text = {r["text"] for r in map(json.loads, open(f"{T}/dataset_ts_v2.jsonl"))} | \
          {r["text"] for r in map(json.loads, open(f"{T}/dataset_v1.jsonl")) if r["page_type"] == "support_troubleshoot"}
def rows(p): return [json.loads(l) for l in open(p)]
def is_ts(x): return x["messages"][1]["content"] in ts_text
assert rows(f"{T}/lora_data_v2/train.jsonl")[0]["messages"][0] == rows(f"{T}/lora_data_v3d/train.jsonl")[0]["messages"][0]
out = {}
for s, ts_src in (("train", "train"), ("valid", "valid"), ("test", None)):
    g = [x for x in rows(f"{T}/lora_data_v2/{s}.jsonl") if not is_ts(x)]
    t = [x for x in rows(f"{T}/lora_data_v3d/{ts_src}.jsonl") if is_ts(x)] if ts_src else []
    out[s] = g + t
    if s != "test": random.shuffle(out[s])
    print(s, "일반", len(g), "트러블슈팅", len(t))
out["test_ts"] = rows(f"{T}/lora_data_v3d/test_ts.jsonl")
for s, r in out.items():
    with open(f"{OUT}/{s}.jsonl", "w") as f:
        for x in r: f.write(json.dumps(x, ensure_ascii=False) + "\n")
print("test_ts", len(out["test_ts"]))
