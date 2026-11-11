#!/bin/bash
# v5 (2026-11-10): v2·v4 통합 단일 모델 — 일반은 v2 라벨, 트러블슈팅은 10-24 기준(v3d·v4 와 동일). build_lora_v5c.py → lora_data_v5c (v5 라벨, TS 13% · 1000 iters = v2 조건).
# 학습 → 평가(test·test_ts, 블라인드 general·ts·flip4) → fuse → ollama hiro-v5c (배포는 별도: hiro 백업 후 cp)
cd /Users/dubaba/my-geo-project/my-geo-audit
PY=~/.venvs/mlx/bin/python; LORA=~/.venvs/mlx/bin/mlx_lm.lora; FUSE=~/.venvs/mlx/bin/mlx_lm.fuse
BASE=mlx-community/Qwen2.5-3B-Instruct-4bit; T=reports/shadow_llm/train; D=$T/lora_data_v5c; B=$T/blind_eval
DIR=$T/lora_q25_3b_v5c; mkdir -p $DIR
echo "== v5c train $(date '+%m-%d %H:%M')"
$LORA --model $BASE --train --data $D --adapter-path $DIR/adapters --iters 1000 --batch-size 4 --num-layers 16 --learning-rate 1e-4 --max-seq-length 768 --mask-prompt --steps-per-eval 250 --val-batches 25 --save-every 250 --grad-checkpoint > $DIR/train.log 2>&1
grep -q '0001000_adapters' $DIR/train.log || { echo "V5C FAILED"; exit 1; }
echo "== v5c eval $(date '+%m-%d %H:%M')"
$PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $D/test.jsonl --ids $D/test_ids.json --out $DIR/pred_test.jsonl 2>$DIR/eval.err | tee $DIR/eval_test.txt
$PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $D/test_ts.jsonl --ids $D/test_ts_ids.json --out $DIR/pred_test_ts.jsonl 2>>$DIR/eval.err | tee $DIR/eval_ts.txt
for S in general ts flip4; do
  $PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $B/v5in_$S.jsonl --ids $B/v5in_${S}_ids.json --out $B/pred_v5c_$S.jsonl > /dev/null 2>>$DIR/eval.err
done
echo "== fuse $(date '+%m-%d %H:%M')"
$FUSE --model $BASE --adapter-path $DIR/adapters --save-path $T/fused_v5c --dequantize > $T/fuse_v5c.log 2>&1 || { echo "FUSE FAILED"; exit 1; }
echo "== ollama create hiro-v5c $(date '+%m-%d %H:%M')"
ollama create hiro-v5c -f $T/Modelfile.v5c --quantize q8_0 > $T/ollama_create_v5c.log 2>&1 || { echo "OLLAMA CREATE FAILED"; exit 1; }
echo "== PIPELINE DONE $(date '+%m-%d %H:%M')"
