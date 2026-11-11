#!/bin/bash
# v5 (2026-11-10): v2·v4 통합 단일 모델 — 일반은 v2 라벨, 트러블슈팅은 10-24 기준(v3d·v4 와 동일). build_lora_v5.py → lora_data_v5.
# 학습 → 평가(test·test_ts, 블라인드 general·ts·flip4) → fuse → ollama hiro-v5 (배포는 별도: hiro 백업 후 cp)
cd /Users/dubaba/my-geo-project/my-geo-audit
PY=~/.venvs/mlx/bin/python; LORA=~/.venvs/mlx/bin/mlx_lm.lora; FUSE=~/.venvs/mlx/bin/mlx_lm.fuse
BASE=mlx-community/Qwen2.5-3B-Instruct-4bit; T=reports/shadow_llm/train; D=$T/lora_data_v5; B=$T/blind_eval
DIR=$T/lora_q25_3b_v5; mkdir -p $DIR
echo "== v5 train $(date '+%m-%d %H:%M')"
$LORA --model $BASE --train --data $D --adapter-path $DIR/adapters --iters 1600 --batch-size 4 --num-layers 16 --learning-rate 1e-4 --max-seq-length 768 --mask-prompt --steps-per-eval 400 --val-batches 25 --save-every 400 --grad-checkpoint > $DIR/train.log 2>&1
grep -q '0001600_adapters' $DIR/train.log || { echo "V5 FAILED"; exit 1; }
echo "== v5 eval $(date '+%m-%d %H:%M')"
$PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $D/test.jsonl --ids $D/test_ids.json --out $DIR/pred_test.jsonl 2>$DIR/eval.err | tee $DIR/eval_test.txt
$PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $D/test_ts.jsonl --ids $D/test_ts_ids.json --out $DIR/pred_test_ts.jsonl 2>>$DIR/eval.err | tee $DIR/eval_ts.txt
for S in general ts flip4; do
  $PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $B/v5in_$S.jsonl --ids $B/v5in_${S}_ids.json --out $B/pred_v5_$S.jsonl > /dev/null 2>>$DIR/eval.err
done
echo "== fuse $(date '+%m-%d %H:%M')"
$FUSE --model $BASE --adapter-path $DIR/adapters --save-path $T/fused_v5 --dequantize > $T/fuse_v5.log 2>&1 || { echo "FUSE FAILED"; exit 1; }
echo "== ollama create hiro-v5 $(date '+%m-%d %H:%M')"
ollama create hiro-v5 -f $T/Modelfile.v5 --quantize q8_0 > $T/ollama_create_v5.log 2>&1 || { echo "OLLAMA CREATE FAILED"; exit 1; }
echo "== PIPELINE DONE $(date '+%m-%d %H:%M')"
