from keras.preprocessing.text import text_to_word_sequence
import os
import pickle
from typing import Set

from code2seq_dataset.commit_message_tokenizer import SEPARATOR


def get_commits_for_train_aurora(com_com_log: str, empty_com_file: str, is_pickle: bool,
                                 output_file: str, new_com_com_log: str):
    needed_commits: Set[str] = set()
    with open(empty_com_file, 'rb') as file:
        empty_commits = pickle.load(file)

    with open(new_com_com_log, 'w') as new_com_com_log_file, open(com_com_log, 'r') as com_com_log_file:
        total_commit_number = 0
        for line in com_com_log_file:
            if line.startswith("parent_commit_file_hash"):
                continue

            line_list = line.split(SEPARATOR)
            cur_commit, message, author = line_list[1], line_list[4], line_list[2]

            if cur_commit in empty_commits:
                continue
            message = message.lower()
            if author == "builder":
                if message == "new version" or \
                        message == "build completed" or \
                        message == "build failed":
                    continue
            if message == "no message" or \
                    message == "*** empty log message ***" or \
                    message.startswith("this commit was manufactured by cvs2svn"):
                continue
            text_list = text_to_word_sequence(message)
            if text_list:
                total_commit_number += 1
                needed_commits.add(cur_commit)
            new_com_com_log_file.write(f"{line}")

    print(f"Number of needed commits {len(needed_commits)}")

    if is_pickle:
        with open(output_file, 'wb') as file:
            pickle.dump(needed_commits, file)
    else:
        with open(output_file, 'w') as file:
            for commit in needed_commits:
                file.write(f"{commit}\n")


def get_commits_for_train_intellij(com_com_log: str, empty_com_file: str, is_pickle: bool,
                                   output_file: str, new_com_com_log: str):
    needed_commits = set()
    with open(empty_com_file, 'rb') as file:
        empty_commits = pickle.load(file)

    with open(new_com_com_log, 'w') as new_com_com_log_file:
        with open(com_com_log, 'r') as com_com_log_file:
            total_commit_number = 0
            for line in com_com_log_file:
                if line.startswith("parent_commit_file_hash"):
                    continue

                line_list = line.split(SEPARATOR)
                cur_commit, message, author = line_list[1], line_list[4], line_list[2]

                if cur_commit in empty_commits:
                    continue
                message = message.lower()
                if message == "(no message)":
                    continue
                text_list = text_to_word_sequence(message)
                if text_list:
                    total_commit_number += 1
                    needed_commits.add(cur_commit)
                new_com_com_log_file.write(f"{line}")

    print(f"Number of needed commits {len(needed_commits)}")

    if is_pickle:
        with open(output_file, 'wb') as file:
            pickle.dump(needed_commits, file)
    else:
        with open(output_file, 'w') as file:
            for commit in needed_commits:
                file.write(f"{commit}\n")


def create_new_full_log_file(old_full_log: str, new_full_log: str, needed_commits_pickle_file: str):
    with open(needed_commits_pickle_file, 'rb') as f:
        needed_commits = pickle.load(f)

    with open(new_full_log, 'w') as new_full_log_file:
        with open(old_full_log, 'r') as old_full_log_file:
            for line in old_full_log_file:
                if line.startswith("commit_hash"):
                    continue
                line_list = line.split(SEPARATOR)
                commit = line_list[0]
                if commit in needed_commits:
                    new_full_log_file.write(line)


if __name__ == "__main__":
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    git_dir_name = "aurora"
    git_dir_name = "intellij"
    git_dir = os.path.join(parent_dir, git_dir_name)
    com_com_log_file = f"gcm_{git_dir_name}_com_com_msg_author_date_2010.log"
    com_com_log_file = os.path.join(parent_dir, com_com_log_file)
    no_files_change_commit_pickle_file = "no_files_change_commits.pickle"
    no_files_change_commit_pickle_file = os.path.join(parent_dir, no_files_change_commit_pickle_file)

    needed_commits_pickle_file = f"{git_dir_name}_commits_for_train.pickle"
    needed_commits_pickle_file = os.path.join(parent_dir, needed_commits_pickle_file)
    new_com_com_log_file = f"gcm_{git_dir_name}_for_train_com_com_author_date.log"
    new_com_com_log_file = os.path.join(parent_dir, new_com_com_log_file)

    # for aurora

    # get_commits_for_train_aurora(com_com_log_file, no_files_change_commit_pickle_file,
    #                              True, needed_commits_pickle_file, new_com_com_log_file)
    #
    # commits_for_train_file = f"{git_dir_name}_needed_commits.log"
    # commits_for_train_file = os.path.join(parent_dir, commits_for_train_file)
    # get_commits_for_train_aurora(com_com_log_file, no_files_change_commit_pickle_file,
    #                              False, commits_for_train_file, new_com_com_log_file)

    no_change_commit_pickle_file = f"no_files_change_commits_{git_dir_name}.pickle"
    no_change_commit_pickle_file = os.path.join(parent_dir, no_change_commit_pickle_file)
    get_commits_for_train_intellij(com_com_log_file, no_change_commit_pickle_file, True, needed_commits_pickle_file,
                                   new_com_com_log_file)

    old_full_log_file = f"gcm_{git_dir_name}_full.log"
    old_full_log_file = os.path.join(parent_dir, old_full_log_file)
    new_full_log_file = f"gcm_{git_dir_name}_full_log_for_train_commits.log"
    new_full_log_file = os.path.join(parent_dir, new_full_log_file)
    create_new_full_log_file(old_full_log_file, new_full_log_file, needed_commits_pickle_file)
