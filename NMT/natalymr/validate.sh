#!/usr/bin/env bash

dev=/home/ubuntu/crawler/data/nematus_data/test.diffs
ref=/home/ubuntu/crawler/data/nematus_data/test.msg

# run model on test set and get the score
python ../../../nematus/nematus/translate.py \
     -m ../../../nematus/nematus/models/model.first_try.npz  \
     -s /home/ubuntu/crawler/data/nematus_data/test.diffs \
     -t /home/ubuntu/crawler/data/nematus_data/test.msg \
     -o /home/ubuntu/crawler/data/nematus_data/test.msg.from_model \
     -v

