#!/bin/bash
# base_dir="/home/username/workspace"
mkdir result
deepspeed --include localhost:0 --master_port 42991 predict.py \
    --batch_size 256 \
    --iteration_count 5 \
    --min_len 3 \
    --max_len 128 \
    --min_error_probability 0.0 \
    --additional_confidence 0.0 \
    --sub_token_mode "average" \
    --max_pieces_per_token 5 \
    --model_dir ./ckpts/ckpt_20220818_18:01:52/ \
    --ckpt_id "epoch-17" \
    --deepspeed_config "./deepspeed_config.json" \
    --detect_vocab_path "./data/vocabulary/d_tags.txt" \
    --correct_vocab_path "./data/vocabulary/labels.txt" \
    --pretrained_transformer_path "../pretrain_model/chinese-roberta-wwm-ext" \
    --input_path "../../../datasets/track3/testA/yaclc-minimal_testA.src" \
    --out_path "result/yaclc-minimal_testA.preds" \
    --special_tokens_fix 1 \
    --detokenize 1 \
    --amp
