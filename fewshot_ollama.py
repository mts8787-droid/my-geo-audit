"""
Few-shot 분류기 (Ollama qwen3:8b) — dataset_v1.jsonl(Claude+사람 라벨)을 정답으로 평가.
  python3 fewshot_ollama.py --build        # 예시 선정 + train/test 분할 저장
  python3 fewshot_ollama.py --run [--all]  # test(기본 20%) 또는 전체(예시 제외) 분류, 재시작 가능
  python3 fewshot_ollama.py --report       # 라벨별 일치율/정밀도/재현율 + regex 대비
환경변수: OLLAMA_URL(기본 http://localhost:11434), OLLAMA_MODEL(기본 qwen3:8b)
"""
import argparse, asyncio, json, os, random, re
from collections import Counter, defaultdict
from datetime import datetime
import httpx

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
D = "reports/shadow_llm/train"
DATA = f"{D}/dataset_v1.jsonl"
FS = f"{D}/fewshot"
EX, SPLIT, OUT = f"{FS}/examples.json", f"{FS}/split.json", f"{FS}/pred.jsonl"
LABELS = ("citable", "definition", "summary")
BATCH = 10

RULES = """You label sentences from LG.com pages (English, Spanish, Portuguese, German, Vietnamese). Judge each sentence on its own.
citable=y: a concrete, verifiable FACT an AI assistant could quote: a spec/number with its meaning, a named standard or certification,
  a measured/tested result, an award with source, a dated factual statement, or a concrete explanation of what a feature/technology does.
citable=n: slogans, vague praise, calls to action, menu/navigation text, promotions, prices, discounts, financing/warranty-period terms,
  coupons, contact details, legal text, questions, usage instructions, device-operation notes, asterisk footnotes/test-method notes, company history.
definition=y: explains WHAT a term, technology, feature, product category or concept IS or does ("X is a…", "X means…", "the X motor provides…").
  A PDP header "product name + Key Features" with concrete feature names also counts.
definition=n: company profile/"About LG" boilerplate, titles/headlines/breadcrumbs, benefit claims without a named thing, instructions, questions, notices.
summary=y: (part of) a block that summarizes the page or lists key features with CONCRETE items (Key Features / Características principales /
  Hauptmerkmale with specs, "In this article" overview, lead paragraph stating what the page covers).
summary=n: title, headline, dateline, menu, generic intro sentence, key-features list with only vague benefits, body paragraphs, FAQ questions."""


def load():
    return [json.loads(l) for l in open(DATA) if l.strip()]


def build():
    rows = load()
    rnd = random.Random(1018)
    ids = [r["id"] for r in rows]
    rnd.shuffle(ids)
    test = set(ids[: len(ids) // 5])
    pool = [r for r in rows if r["id"] not in test and 25 <= len(r["text"]) <= 200]
    rnd.shuffle(pool)
    pool.sort(key=lambda r: not r["human_reviewed"])  # 사람 검토분 우선
    ex, used = [], set()

    def take(pred, n):
        k = 0
        for r in pool:
            if k >= n:
                break
            if r["id"] in used or not pred(r):
                continue
            # 언어 다양성: 같은 국가 3개 초과 방지
            if sum(1 for e in ex if e["cc"] == r["cc"]) >= 7:
                continue
            ex.append(r); used.add(r["id"]); k += 1

    take(lambda r: r["summary"] == "y", 4)
    take(lambda r: r["definition"] == "y" and r["citable"] == "y", 5)
    take(lambda r: r["definition"] == "y" and r["citable"] == "n", 3)
    take(lambda r: r["citable"] == "y" and r["definition"] == "n", 8)
    take(lambda r: r["regex_candidate"] and r["citable"] == "n", 10)   # 규칙이 잡았지만 아님(어려운 음성)
    take(lambda r: not r["regex_candidate"] and r["citable"] == "n" and r["definition"] == "n", 6)
    rnd.shuffle(ex)
    json.dump(ex, open(EX, "w"), ensure_ascii=False, indent=1)
    json.dump({"test": sorted(test), "examples": sorted(used)}, open(SPLIT, "w"))
    print(f"예시 {len(ex)}개 (국가 {Counter(e['cc'] for e in ex)}), test {len(test)}개, 나머지 train {len(rows)-len(test)-len(ex)}개")
    for e in ex:
        print(" ", e["citable"], e["definition"], e["summary"], e["cc"], e["text"][:90])


def prompt(examples, batch):
    exs = "\n".join(json.dumps({"text": e["text"], "citable": e["citable"], "definition": e["definition"], "summary": e["summary"]},
                               ensure_ascii=False) for e in examples)
    items = "\n".join(f"[{i}] {r['text'][:400]}" for i, r in enumerate(batch))
    return f"""{RULES}

Labeled examples (follow this judgment style exactly):
{exs}

Now label each numbered sentence. Return JSON only:
{{"results": [{{"i": 0, "citable": "y|n", "definition": "y|n", "summary": "y|n"}}, ...]}} with one entry per sentence, in order.

{items}"""


async def _llm(client, p):
    body = {"model": OLLAMA_MODEL, "stream": False, "think": False, "format": "json",
            "messages": [{"role": "user", "content": p}],
            "options": {"temperature": 0, "num_ctx": 8192}}
    r = await client.post(f"{OLLAMA_URL}/api/chat", json=body)
    r.raise_for_status()
    try:
        return json.loads(r.json()["message"]["content"])
    except Exception:
        return {}


async def run(all_rows):
    rows = load(); split = json.load(open(SPLIT)); ex = json.load(open(EX))
    exids = set(split["examples"]); test = set(split["test"])
    targets = [r for r in rows if r["id"] not in exids and (all_rows or r["id"] in test)]
    done = set()
    if os.path.exists(OUT):
        done = {json.loads(l)["id"] for l in open(OUT) if l.strip()}
    targets = [r for r in targets if r["id"] not in done]
    print(f"대상 {len(targets)}문장 / 배치 {BATCH} / 모델 {OLLAMA_MODEL}", flush=True)
    async with httpx.AsyncClient(timeout=300) as client:
        for b in range(0, len(targets), BATCH):
            batch = targets[b:b + BATCH]; t0 = datetime.now()
            res = await _llm(client, prompt(ex, batch))
            got = {x.get("i"): x for x in (res.get("results") or []) if isinstance(x, dict)}
            with open(OUT, "a") as f:
                for i, r in enumerate(batch):
                    g = got.get(i, {})
                    f.write(json.dumps({"id": r["id"], **{k: (g.get(k) if g.get(k) in ("y", "n") else None) for k in LABELS}}) + "\n")
            miss = sum(1 for i in range(len(batch)) if i not in got)
            print(f"[{b+len(batch)}/{len(targets)}] {(datetime.now()-t0).seconds}s miss={miss}", flush=True)


def report():
    rows = {r["id"]: r for r in load()}
    pred = [json.loads(l) for l in open(OUT) if l.strip()]
    print(f"예측 {len(pred)}문장")
    for k in LABELS:
        tp = fp = fn = tn = na = 0
        for p in pred:
            g = rows[p["id"]][k]; v = p[k]
            if v is None: na += 1; continue
            if v == "y" and g == "y": tp += 1
            elif v == "y": fp += 1
            elif g == "y": fn += 1
            else: tn += 1
        n = tp + fp + fn + tn
        prec = tp / (tp + fp) if tp + fp else 0; rec = tp / (tp + fn) if tp + fn else 0
        print(f"{k:11s} 일치 {(tp+tn)/n:5.1%}  정밀도 {prec:5.1%}  재현율 {rec:5.1%}  (정답y {tp+fn}, 예측y {tp+fp}, 무응답 {na})")
    # regex 대비 (#36)
    tp = fp = fn = 0
    for p in pred:
        r = rows[p["id"]]; g = r["citable"] == "y"; c = r["regex_candidate"]
        tp += g and c; fp += c and not g; fn += g and not c
    print(f"regex #36    정밀도 {tp/(tp+fp):5.1%}  재현율 {tp/(tp+fn):5.1%}  (같은 문장 기준)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true"); ap.add_argument("--run", action="store_true")
    ap.add_argument("--all", action="store_true"); ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    if a.build: build()
    elif a.run: asyncio.run(run(a.all))
    elif a.report: report()
