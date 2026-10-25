#!/bin/bash
# 블라인드 트러블슈팅 새 100문장에 v2(올라마 hiro)·v3·v3b·v3c 예측. 정답은 검수자 블라인드 라벨로 나중에 채점.
cd /Users/dubaba/my-geo-project/my-geo-audit
/usr/bin/python3 ollama_eval.py --data reports/shadow_llm/train/blind_eval/ts_new.jsonl --ids reports/shadow_llm/train/blind_eval/ts_new_ids.json --out reports/shadow_llm/train/blind_eval/pred_v2.jsonl > /dev/null 2>reports/shadow_llm/train/blind_eval/pred_v2.err
for v in v3 v3b v3c; do
  ~/.venvs/mlx/bin/python lora_eval.py --model mlx-community/Qwen2.5-3B-Instruct-4bit --adapter reports/shadow_llm/train/lora_q25_3b_$v/adapters --data reports/shadow_llm/train/blind_eval/ts_new.jsonl --ids reports/shadow_llm/train/blind_eval/ts_new_ids.json --out reports/shadow_llm/train/blind_eval/pred_$v.jsonl > /dev/null 2>reports/shadow_llm/train/blind_eval/pred_$v.err
done
echo DONE
