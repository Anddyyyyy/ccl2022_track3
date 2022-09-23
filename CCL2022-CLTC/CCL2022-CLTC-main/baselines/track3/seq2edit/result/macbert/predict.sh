#!/bin/bash

# predict yaclc-minimal_testA
deepspeed --include localhost:0 --master_port 42991 ../../predict.py \
    --batch_size 256 \
    --iteration_count 5 \
    --min_len 3 \
    --max_len 128 \
    --min_error_probability 0.0 \
    --additional_confidence 0.0 \
    --sub_token_mode "average" \
    --max_pieces_per_token 5 \
    --model_dir ../../ckpts/macbert/ \
    --ckpt_id "epoch-19" \
    --deepspeed_config "../../deepspeed_config.json" \
    --detect_vocab_path "../../data/vocabulary/d_tags.txt" \
    --correct_vocab_path "../../data/vocabulary/labels.txt" \
    --pretrained_transformer_path "../../../pretrain_model/chinese-macbert-base" \
    --input_path "../../../../../datasets/track3/testA/yaclc-minimal_testA.src" \
    --out_path "./yaclc-minimal_testA.preds" \
    --special_tokens_fix 1 \
    --detokenize 1 \
    --amp

python ../../../../../../utils/preprocess_test_para.py \
        -s ../../../../../datasets/track3/testA/yaclc-minimal_testA.src \
        -t ./yaclc-minimal_testA.preds \
        -f ./yaclc-minimal_testA.para

# predict yaclc-fluency_testA
deepspeed --include localhost:0 --master_port 42991 ../../predict.py \
    --batch_size 256 \
    --iteration_count 5 \
    --min_len 3 \
    --max_len 128 \
    --min_error_probability 0.0 \
    --additional_confidence 0.0 \
    --sub_token_mode "average" \
    --max_pieces_per_token 5 \
    --model_dir ../../ckpts/macbert/ \
    --ckpt_id "epoch-19" \
    --deepspeed_config "../../deepspeed_config.json" \
    --detect_vocab_path "../../data/vocabulary/d_tags.txt" \
    --correct_vocab_path "../../data/vocabulary/labels.txt" \
    --pretrained_transformer_path "../../../pretrain_model/chinese-macbert-base" \
    --input_path "../../../../../datasets/track3/testA/yaclc-fluency_testA.src" \
    --out_path "./yaclc-fluency_testA.preds" \
    --special_tokens_fix 1 \
    --detokenize 1 \
    --amp

python ../../../../../../utils/preprocess_test_para.py \
        -s ../../../../../datasets/track3/testA/yaclc-fluency_testA.src \
        -t ./yaclc-fluency_testA.preds \
        -f ./yaclc-fluency_testA.para
        
        
# predict yaclc-minimal_testB
deepspeed --include localhost:0 --master_port 42991 ../../predict.py \
    --batch_size 256 \
    --iteration_count 5 \
    --min_len 3 \
    --max_len 128 \
    --min_error_probability 0.0 \
    --additional_confidence 0.0 \
    --sub_token_mode "average" \
    --max_pieces_per_token 5 \
    --model_dir ../../ckpts/macbert/ \
    --ckpt_id "epoch-19" \
    --deepspeed_config "../../deepspeed_config.json" \
    --detect_vocab_path "../../data/vocabulary/d_tags.txt" \
    --correct_vocab_path "../../data/vocabulary/labels.txt" \
    --pretrained_transformer_path "../../../pretrain_model/chinese-macbert-base" \
    --input_path "../../../../../datasets/track3/testB/yaclc-minimal_testB.src" \
    --out_path "./yaclc-minimal_testB.preds" \
    --special_tokens_fix 1 \
    --detokenize 1 \
    --amp

python ../../../../../../utils/preprocess_test_para.py \
        -s ../../../../../datasets/track3/testB/yaclc-minimal_testB.src \
        -t ./yaclc-minimal_testB.preds \
        -f ./yaclc-minimal_testB.para

# predict yaclc-fluency_testB
deepspeed --include localhost:0 --master_port 42991 ../../predict.py \
    --batch_size 256 \
    --iteration_count 5 \
    --min_len 3 \
    --max_len 128 \
    --min_error_probability 0.0 \
    --additional_confidence 0.0 \
    --sub_token_mode "average" \
    --max_pieces_per_token 5 \
    --model_dir ../../ckpts/macbert/ \
    --ckpt_id "epoch-19" \
    --deepspeed_config "../../deepspeed_config.json" \
    --detect_vocab_path "../../data/vocabulary/d_tags.txt" \
    --correct_vocab_path "../../data/vocabulary/labels.txt" \
    --pretrained_transformer_path "../../../pretrain_model/chinese-macbert-base" \
    --input_path "../../../../../datasets/track3/testB/yaclc-fluency_testB.src" \
    --out_path "./yaclc-fluency_testB.preds" \
    --special_tokens_fix 1 \
    --detokenize 1 \
    --amp

python ../../../../../../utils/preprocess_test_para.py \
        -s ../../../../../datasets/track3/testB/yaclc-fluency_testB.src \
        -t ./yaclc-fluency_testB.preds \
        -f ./yaclc-fluency_testB.para