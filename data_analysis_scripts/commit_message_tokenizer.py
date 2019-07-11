from collections import OrderedDict
import itertools
from keras.preprocessing.text import Tokenizer
import os
from typing import Dict, List


def invert_dict(input_dict: Dict[str, int]) -> Dict[int, List[str]]:
    result = dict()

    for key, value in input_dict.items():
        if value not in result:
            result[value] = [key]
        else:
            result[value].append(key)

    return result


def commit_msg_tokenizing(com_com_log: str):
    msg_vs_counts = {}
    msgs = []
    with open(com_com_log, 'r') as com_com_log_file:
        for line in com_com_log_file:
            if line.startswith("parent_commit_file_hash"):
                continue
            line_list = line.split(";")
            message = line_list[2]
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

    counts_vs_msg = invert_dict(msg_vs_counts)
    counts_vs_msg_sorted = OrderedDict(sorted(counts_vs_msg.items(), reverse=True))
    top_popular_msg = dict(itertools.islice(counts_vs_msg_sorted.items(), 0, 20))
    for key, value in top_popular_msg.items():
        print("{:>3}: {}".format(key, value))
    print()

    tokenizer = Tokenizer()
    tokenizer.fit_on_texts(msgs)

    counts_vs_word = invert_dict(tokenizer.word_counts)
    counts_vs_word_sorted = OrderedDict(sorted(counts_vs_word.items(), reverse=True))
    top_popular_words = dict(itertools.islice(counts_vs_word_sorted.items(), 0, 20))
    print(top_popular_words)

    # print(tokenizer.word_counts)
    # print(tokenizer.document_count)
    # print(tokenizer.word_index)
    # print(tokenizer.word_docs)


if __name__ == "__main__":
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    git_dir_name = "aurora"
    git_dir = os.path.join(parent_dir, git_dir_name)
    com_com_log_file = f"gcm_{git_dir_name}_com_com_msg_author_date.log"
    com_com_log_file = os.path.join(parent_dir, com_com_log_file)
    commit_msg_tokenizing(com_com_log_file)
