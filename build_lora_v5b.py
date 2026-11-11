"""
v5b 학습 데이터 (2026-11-10): v5(일반 v2 라벨 + 트러블슈팅 10-24) 와 같은 행에 페이지 유형 태그를 붙인다.
  v5 는 페이지 유형을 몰라 트러블슈팅 기준(원인·증상 설명 y)을 일반 문장에도 적용해 일반 블라인드 예측 y 88(정답 62)로 과다.
  사용자 메시지 = "[page: <page_type>] <문장>" — audit_model.label_sentence(page_type=...) 와 같은 형식이어야 한다.
  /usr/bin/python3 build_lora_v5b.py
"""
import json, os
T = "reports/shadow_llm/train"; SRC = f"{T}/lora_data_v5"; OUT = f"{T}/lora_data_v5b"; os.makedirs(OUT, exist_ok=True)
def tag(pt, text): return f"[page: {pt}] {text}"
ts_text = {r["text"] for r in map(json.loads, open(f"{T}/dataset_ts_v2.jsonl"))} | \
          {r["text"] for r in map(json.loads, open(f"{T}/dataset_v1.jsonl")) if r["page_type"] == "support_troubleshoot"}
pt_of = {r["text"]: r["page_type"] for r in map(json.loads, open(f"{T}/dataset_v1.jsonl"))}
for s in ("train", "valid", "test", "test_ts"):
    n = 0
    with open(f"{OUT}/{s}.jsonl", "w") as f:
        for l in open(f"{SRC}/{s}.jsonl"):
            x = json.loads(l); u = x["messages"][1]["content"]
            pt = "support_troubleshoot" if u in ts_text else pt_of[u]
            x["messages"][1]["content"] = tag(pt, u); n += pt == "support_troubleshoot"
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    print(s, "트러블슈팅", n)
for s in ("test_ids.json", "test_ts_ids.json"):
    open(f"{OUT}/{s}", "w").write(open(f"{SRC}/{s}").read())
B = f"{T}/blind_eval"
pt_blind = {x["id"]: ("support_troubleshoot" if x["set"] == "ts_new" else x["page_type"]) for x in json.load(open(f"{B}/sample.json"))}
pt_blind.update({x["id"]: x["page_type"] for x in json.load(open(f"{B}/flip4_sample.json"))})
for s in ("general", "ts", "flip4"):
    ids = json.load(open(f"{B}/v5in_{s}_ids.json"))
    with open(f"{B}/v5bin_{s}.jsonl", "w") as f:
        for i, l in zip(ids, open(f"{B}/v5in_{s}.jsonl")):
            x = json.loads(l); x["messages"][1]["content"] = tag(pt_blind[i], x["messages"][1]["content"])
            f.write(json.dumps(x, ensure_ascii=False) + "\n")
    open(f"{B}/v5bin_{s}_ids.json", "w").write(json.dumps(ids))
