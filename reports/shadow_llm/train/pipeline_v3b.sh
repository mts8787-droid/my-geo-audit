#!/bin/bash
# v3 학습 종료 대기 → v3 평가(새 정답) → v3b 학습 → v3b 평가. 메모리 공유 때문에 순차 실행.
cd /Users/dubaba/my-geo-project/my-geo-audit
PY=~/.venvs/mlx/bin/python; LORA=~/.venvs/mlx/bin/mlx_lm.lora
BASE=mlx-community/Qwen2.5-3B-Instruct-4bit; T=reports/shadow_llm/train; D=$T/lora_data_v3b
V3=$T/lora_q25_3b_v3; V3B=$T/lora_q25_3b_v3b; mkdir -p $V3B
until grep -qE '0001600_adapters|Traceback|Killed' $V3/train.log; do sleep 60; done
grep -q '0001600_adapters' $V3/train.log || { echo "V3 FAILED"; exit 1; }
for M in V3 V3B; do
  if [ $M = V3B ]; then
    echo "== v3b train $(date '+%H:%M')"
    $LORA --model $BASE --train --data $D --adapter-path $V3B/adapters --iters 1600 --batch-size 4 --num-layers 16 --learning-rate 1e-4 --max-seq-length 768 --mask-prompt --steps-per-eval 400 --val-batches 25 --save-every 400 --grad-checkpoint > $V3B/train.log 2>&1
    grep -q '0001600_adapters' $V3B/train.log || { echo "V3B FAILED"; exit 1; }
    DIR=$V3B
  else DIR=$V3; fi
  echo "== $M eval $(date '+%H:%M')"
  $PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $D/test.jsonl --ids $D/test_ids.json --out $DIR/pred_test_newgold.jsonl 2>$DIR/eval.err | tee $DIR/eval_newgold.txt
  $PY lora_eval.py --model $BASE --adapter $DIR/adapters --data $D/test_ts.jsonl --ids $D/test_ts_ids.json --out $DIR/pred_test_ts.jsonl 2>>$DIR/eval.err | tee $DIR/eval_ts.txt
done
echo "== PIPELINE DONE $(date '+%H:%M')"
