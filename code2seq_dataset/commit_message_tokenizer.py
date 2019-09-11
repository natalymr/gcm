import collections
from collections import OrderedDict
import itertools
from keras.preprocessing.text import Tokenizer
import os
from typing import Dict, List


SEPARATOR = "THIS_STRING_WILL_NEVER_APPEAR_IN_DATASET_AND_IT_WILL_BE_USED_AS_SEPARATOR"


def invert_dict(input_dict: Dict[str, int]) -> Dict[int, List[str]]:
    output_dict: Dict[int, List[str]] = collections.defaultdict(list)

    for key, value in input_dict.items():
        output_dict[value].append(key)

    return output_dict


def commit_msg_tokenizing(com_com_log: str):
    msg_vs_counts: Dict[str, int] = {}
    msgs: List[str] = []

    with open(com_com_log, 'r') as com_com_log_file:
        for line in com_com_log_file:
            if line.startswith("parent_commit_file_hash"):
                continue
            line_list = line.split(SEPARATOR)
            message = line_list[4]
            if message == "no message" or \
                    message == "New version" or \
                    message == "Build completed" or \
                    message == "Build failed" or \
                    message == "*** empty log message ***":
                continue
            else:
                msgs.append(message)
                message = message.lower()
                if message in msg_vs_counts:
                    msg_vs_counts[message] += 1
                else:
                    msg_vs_counts[message] = 1

    print(f"Unique message number {len(msg_vs_counts)}")

    counts_vs_msg = invert_dict(msg_vs_counts)
    counts_vs_msg_sorted = OrderedDict(sorted(counts_vs_msg.items(), reverse=True))
    top_popular_msg = dict(itertools.islice(counts_vs_msg_sorted.items(), 0, 20))

    for key, value in counts_vs_msg_sorted.items():
        print("{:>3}: {} {}".format(key, len(value), value))

    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(msgs)

    counts_vs_word = invert_dict(tokenizer.word_counts)
    counts_vs_word_sorted = OrderedDict(sorted(counts_vs_word.items(), reverse=True))
    top_popular_words = dict(itertools.islice(counts_vs_word_sorted.items(), 0, 20))
    print(top_popular_words)


if __name__ == "__main__":
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    git_dir_name = "aurora"
    git_dir = os.path.join(parent_dir, git_dir_name)
    com_com_log_file = f"gcm_{git_dir_name}_com_com_msg_author_date.log"
    com_com_log_file = os.path.join(parent_dir, com_com_log_file)

    commit_msg_tokenizing(com_com_log_file)
