#!/bin/bash
# v3c 학습 → 평가. 하이퍼파라미터는 v3b 와 동일, 평가는 lora_data_v3b 의 test/test_ts(같은 정답).
cd /Users/dubaba/my-geo-project/my-geo-audit
PY=~/.venvs/mlx/bin/python; LORA=~/.venvs/mlx/bin/mlx_lm.lora
BASE=mlx-community/Qwen2.5-3B-Instruct-4bit; T=reports/shadow_llm/train; D=$T/lora_data_v3c; E=$T/lora_data_v3b
DIR=$T/lora_q25_3b_v3c; mkdir -p $DIR
echo "== v3c train $(date '+%H:%M')"
$LORA --model $BASE --train --data $D --adapter-path $DIR/adapters --iters 1600 --batch-size 4 --num-layers 16 --learning-rate 1e-4 --max-seq-length 768 --mask-prompt --steps-per-eval 400 --val-batches 25 --save-every 400 --grad-checkpoint > $DIR/train.log 2>&1
grep -q '0001600_adapters' $DIR/train.log || { echo "V3C FAILED"; exit 1; }
echo "== v3c eval $(date '+%H:%M')"
$PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $E/test.jsonl --ids $E/test_ids.json --out $DIR/pred_test_newgold.jsonl 2>$DIR/eval.err | tee $DIR/eval_newgold.txt
$PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $E/test_ts.jsonl --ids $E/test_ts_ids.json --out $DIR/pred_test_ts.jsonl 2>>$DIR/eval.err | tee $DIR/eval_ts.txt
echo "== PIPELINE DONE $(date '+%H:%M')"
