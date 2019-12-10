#!/usr/bin/env bash


python ../../../nematus/nematus/nmt.py \
  --model ../../../nematus/models/model.first_try.npz \
  --embedding_size 512 \
  --state_size 1024 \
  --n_words_src 16912 \
  --n_words 9383 \
  --decay_c 0 \
  --clip_c 1 \
  --learning_rate 0.0001 \
  --optimizer adam \
  --maxlen 300 \
  --translation_maxlen 30 \
  --batch_size 80 \
  --valid_batch_size 80 \
  --source_dataset /home/ubuntu/crawler/data/nematus_data/train.diffs \
  --target_dataset /home/ubuntu/crawler/data/nematus_data/train.msg \
  --valid_source_dataset /home/ubuntu/crawler/data/nematus_data/test.diffs \
  --valid_target_dataset /home/ubuntu/crawler/data/nematus_data/test.msg \
  --dictionaries /home/ubuntu/crawler/data/nematus_data/train.diffs.json /home/ubuntu/crawler/data/nematus_data/train.msg.json \
  --valid_freq 1 \
  --patience 1000 \
  --disp_freq 1 \
  --save_freq 1 \
  --sample_freq 1000 \
  --rnn_dropout_embedding 0.2 \
  --rnn_dropout_hidden 0.2 \
  --rnn_dropout_source 0.1 \
  --rnn_dropout_target 0.1 \
  --no_shuffle \
  --valid_script "./validate.sh"

