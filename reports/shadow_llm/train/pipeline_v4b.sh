#!/bin/bash
# v4 (2026-11-09): 일반 페이지 인용 기준 확장(특허·고유 기술 설명 + 사용 편익, 수식어·마케팅 n) — build_lora_v4.py → lora_data_v4b.
# v4b (2026-11-10): LABEL_V4B 로 재라벨(기술 동작 설명·시험 각주 y) — build_lora_v4.py ... v4b → lora_data_v4b. 나머지는 v4 와 같음.
# 학습 → 평가(lora_data_v4b test·test_ts, 블라인드 general 200·ts 100·flip4 202) → fuse → ollama hiro-v4b (배포는 별도: hiro 백업 후 cp)
cd /Users/dubaba/my-geo-project/my-geo-audit
PY=~/.venvs/mlx/bin/python; LORA=~/.venvs/mlx/bin/mlx_lm.lora; FUSE=~/.venvs/mlx/bin/mlx_lm.fuse
BASE=mlx-community/Qwen2.5-3B-Instruct-4bit; T=reports/shadow_llm/train; D=$T/lora_data_v4b; B=$T/blind_eval
DIR=$T/lora_q25_3b_v4b; mkdir -p $DIR
echo "== v4b train $(date '+%m-%d %H:%M')"
$LORA --model $BASE --train --data $D --adapter-path $DIR/adapters --iters 1600 --batch-size 4 --num-layers 16 --learning-rate 1e-4 --max-seq-length 768 --mask-prompt --steps-per-eval 400 --val-batches 25 --save-every 400 --grad-checkpoint > $DIR/train.log 2>&1
grep -q '0001600_adapters' $DIR/train.log || { echo "V4 FAILED"; exit 1; }
echo "== v4b eval $(date '+%m-%d %H:%M')"
$PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $D/test.jsonl --ids $D/test_ids.json --out $DIR/pred_test.jsonl 2>$DIR/eval.err | tee $DIR/eval_test.txt
$PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $D/test_ts.jsonl --ids $D/test_ts_ids.json --out $DIR/pred_test_ts.jsonl 2>>$DIR/eval.err | tee $DIR/eval_ts.txt
for S in general ts flip4; do
  $PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $B/v4in_$S.jsonl --ids $B/v4in_${S}_ids.json --out $B/pred_v4b_$S.jsonl > /dev/null 2>>$DIR/eval.err
done
echo "== fuse $(date '+%m-%d %H:%M')"
$FUSE --model $BASE --adapter-path $DIR/adapters --save-path $T/fused_v4b --dequantize > $T/fuse_v4b.log 2>&1 || { echo "FUSE FAILED"; exit 1; }
echo "== ollama create hiro-v4b $(date '+%m-%d %H:%M')"
ollama create hiro-v4b -f $T/Modelfile.v4b --quantize q8_0 > $T/ollama_create_v4b.log 2>&1 || { echo "OLLAMA CREATE FAILED"; exit 1; }
echo "== PIPELINE DONE $(date '+%m-%d %H:%M')"
