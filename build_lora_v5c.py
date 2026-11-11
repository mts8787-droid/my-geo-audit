"""
v5c 학습 데이터 (2026-11-10): v5 와 같은 라벨이지만 트러블슈팅 행을 v2 와 같은 비율(학습 13%)로 줄인다.
  v5(TS 45%) 일반 76.0, v5b(+페이지 태그) 69.6 — v2(TS 13%, 1000 iters) 85.2 와의 차이가 TS 비중이라 보고 v2 조건을 재현한다.
  TS 행은 인용 y/n 비율을 유지한 층화 표본 520, valid 60. 테스트는 v5 와 같음.
  /usr/bin/python3 build_lora_v5c.py
"""
import json, os, random
T = "reports/shadow_llm/train"; SRC = f"{T}/lora_data_v5"; OUT = f"{T}/lora_data_v5c"; os.makedirs(OUT, exist_ok=True)
random.seed(13)
ts_text = {r["text"] for r in map(json.loads, open(f"{T}/dataset_ts_v2.jsonl"))} | \
          {r["text"] for r in map(json.loads, open(f"{T}/dataset_v1.jsonl")) if r["page_type"] == "support_troubleshoot"}
def cit(x): return json.loads(x["messages"][2]["content"])["citable"]
for s, k in (("train", 520), ("valid", 60), ("test", None), ("test_ts", None)):
    R = [json.loads(l) for l in open(f"{SRC}/{s}.jsonl")]
    if k:
        g = [x for x in R if x["messages"][1]["content"] not in ts_text]
        t = [x for x in R if x["messages"][1]["content"] in ts_text]
        ty = [x for x in t if cit(x) == "y"]; tn = [x for x in t if cit(x) != "y"]
        ny = round(k * len(ty) / len(t)); t = random.sample(ty, ny) + random.sample(tn, k - ny)
        R = g + t; random.shuffle(R); print(s, "일반", len(g), "트러블슈팅", len(t), "(y", ny, ")")
    with open(f"{OUT}/{s}.jsonl", "w") as f:
        for x in R: f.write(json.dumps(x, ensure_ascii=False) + "\n")
for s in ("test_ids.json", "test_ts_ids.json"):
    open(f"{OUT}/{s}", "w").write(open(f"{SRC}/{s}").read())
