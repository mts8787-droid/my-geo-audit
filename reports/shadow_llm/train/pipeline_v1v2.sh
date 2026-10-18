#!/bin/bash
# v1 학습 종료 대기 → v1 평가 → v2 학습 → v2 평가 (순차, GPU 메모리 공유 때문)
cd /Users/dubaba/my-geo-project/my-geo-audit
PY=~/.venvs/mlx/bin/python; LORA=~/.venvs/mlx/bin/mlx_lm.lora
BASE=mlx-community/Qwen2.5-3B-Instruct-4bit
V1=reports/shadow_llm/train/lora_q25_3b; V2=reports/shadow_llm/train/lora_q25_3b_v2; mkdir -p $V2
until grep -qE '0001000_adapters|Traceback|Killed' $V1/train.log; do sleep 30; done
grep -q '0001000_adapters' $V1/train.log || { echo "V1 FAILED"; exit 1; }
echo "== v1 eval $(date '+%H:%M')"
$PY lora_eval.py --model $BASE --adapter $V1/adapters --out $V1/pred_test.jsonl 2>$V1/eval.err | tee $V1/eval.txt
echo "== v2 train $(date '+%H:%M')"
$LORA --model $BASE --train --data reports/shadow_llm/train/lora_data_v2 --adapter-path $V2/adapters --iters 1000 --batch-size 4 --num-layers 16 --learning-rate 1e-4 --max-seq-length 768 --mask-prompt --steps-per-eval 250 --val-batches 25 --save-every 250 --grad-checkpoint > $V2/train.log 2>&1
grep -q '0001000_adapters' $V2/train.log || { echo "V2 FAILED"; exit 1; }
echo "== v2 eval $(date '+%H:%M')"
$PY lora_eval.py --model $BASE --adapter $V2/adapters --data reports/shadow_llm/train/lora_data_v2/test.jsonl --out $V2/pred_test.jsonl 2>$V2/eval.err | tee $V2/eval.txt
echo "== PIPELINE DONE $(date '+%H:%M')"
