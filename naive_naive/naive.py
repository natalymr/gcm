from keras.preprocessing.text import text_to_word_sequence
from nltk.translate.bleu_score import sentence_bleu, corpus_bleu
import os
import pickle
from typing import List


def naive(com_com_log: str, empty_com_file: str, candidate: List[str]) -> float:
    with open(empty_com_file, 'rb') as file:
        empty_commits = pickle.load(file)
    references = []
    with open(com_com_log, 'r') as com_com_log_file:
        total_commit_number = 0
        for line in com_com_log_file:
            if line.startswith("parent_commit_file_hash"):
                continue

            line_list = line.split(";")
            cur_commit, message, author = line_list[1], line_list[2], line_list[3]
            if cur_commit in empty_commits:
                continue
            message = message.lower()
            if author == "builder":
                if message == "new version" or \
                        message == "build completed" or \
                        message == "build failed":
                    continue
            if message == "no message" or \
                    message == "*** empty log message ***":
                continue
            text_list = text_to_word_sequence(message)
            if text_list:
                total_commit_number += 1
                references.append(text_list)
                if total_commit_number % 100 == 0:
                    print(f"{total_commit_number}")

    total_score = 0.
    for ref in references:
        score = sentence_bleu([ref], candidate, weights=(0.5, 0.5, 0, 0))  # weights=(1, 0, 0, 0)
        total_score += score
    result = total_score / total_commit_number

    print(f"Total commit number: {total_commit_number}")
    print(f"Score sum {total_score}")
    print(f"result = {result}")
    return result


if __name__ == "__main__":
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    git_dir_name = "aurora"
    git_dir = os.path.join(parent_dir, git_dir_name)
    com_com_log_file = f"gcm_{git_dir_name}_com_com_msg_author_date.log"
    com_com_log_file = os.path.join(parent_dir, com_com_log_file)
    no_change_commit_pickle_file = "no_files_change_commits.pickle"
    no_change_commit_pickle_file = os.path.join(parent_dir, no_change_commit_pickle_file)

    # score = naive(com_com_log_file, no_change_commit_pickle_file, ["test", "fixed"])
    score = naive(com_com_log_file, no_change_commit_pickle_file, ["fixed", "npe"])
