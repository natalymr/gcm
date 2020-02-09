#!/usr/bin/env bash

dev=/home/ubuntu/crawler/data/nematus_data/test.diffs
ref=/home/ubuntu/crawler/data/nematus_data/test.msg

# run model on test set
python ../../../nematus/nematus/translate.py \
     -m ../../../nematus/models/model.first_try.npz  \
     -i /home/ubuntu/crawler/data/nematus_data/test.diffs \
     -o /home/ubuntu/crawler/data/nematus_data/test.msg.from_model \
     -v

# get the score
python ../../../nematus/nematus/score.py \
     -m ../../../nematus/models/model.first_try.npz  \Ω
     -s /home/ubuntu/crawler/data/nematus_data/test.msg.from_model \
     -t /home/ubuntu/crawler/data/nematus_data/test.msg \
     -v

