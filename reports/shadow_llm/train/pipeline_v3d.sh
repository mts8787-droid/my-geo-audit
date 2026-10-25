#!/bin/bash
# v3d (2026-10-24): 트러블슈팅 원인·증상 설명문 = 인용 y (사용자 결정) 반영. 일반 데이터는 v3c 와 동일.
# 학습 → 평가(새 트러블슈팅 정답 lora_data_v3d/test_ts, 일반 정답 lora_data_v3b/test) → v2·v3c 도 새 정답으로 재채점 → fuse → ollama hiro-v3d
cd /Users/dubaba/my-geo-project/my-geo-audit
PY=~/.venvs/mlx/bin/python; LORA=~/.venvs/mlx/bin/mlx_lm.lora; FUSE=~/.venvs/mlx/bin/mlx_lm.fuse
BASE=mlx-community/Qwen2.5-3B-Instruct-4bit; T=reports/shadow_llm/train; D=$T/lora_data_v3d; E=$T/lora_data_v3b
DIR=$T/lora_q25_3b_v3d; mkdir -p $DIR
echo "== v3d train $(date '+%m-%d %H:%M')"
$LORA --model $BASE --train --data $D --adapter-path $DIR/adapters --iters 1600 --batch-size 4 --num-layers 16 --learning-rate 1e-4 --max-seq-length 768 --mask-prompt --steps-per-eval 400 --val-batches 25 --save-every 400 --grad-checkpoint > $DIR/train.log 2>&1
grep -q '0001600_adapters' $DIR/train.log || { echo "V3D FAILED"; exit 1; }
echo "== v3d eval $(date '+%m-%d %H:%M')"
$PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $D/test_ts.jsonl --ids $D/test_ts_ids.json --out $DIR/pred_test_ts.jsonl 2>$DIR/eval.err | tee $DIR/eval_ts.txt
$PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $E/test.jsonl --ids $E/test_ids.json --out $DIR/pred_test_newgold.jsonl 2>>$DIR/eval.err | tee $DIR/eval_newgold.txt
for M in v2 v3c; do
  echo "== $M re-eval on v3d test_ts gold $(date '+%m-%d %H:%M')"
  $PY lora_eval.py --model $BASE --adapter $T/lora_q25_3b_$M/adapters --data $D/test_ts.jsonl --ids $D/test_ts_ids.json --out $T/lora_q25_3b_$M/pred_test_ts_v3dgold.jsonl 2>>$DIR/eval.err | tee $T/lora_q25_3b_$M/eval_ts_v3dgold.txt
done
echo "== fuse $(date '+%m-%d %H:%M')"
$FUSE --model $BASE --adapter-path $DIR/adapters --save-path $T/fused_v3d --dequantize > $T/fuse_v3d.log 2>&1 || { echo "FUSE FAILED"; exit 1; }
echo "== ollama create hiro-v3d $(date '+%m-%d %H:%M')"
ollama create hiro-v3d -f $T/Modelfile.v3d --quantize q8_0 > $T/ollama_create_v3d.log 2>&1 || { echo "OLLAMA CREATE FAILED"; exit 1; }
echo "== PIPELINE DONE $(date '+%m-%d %H:%M')"
