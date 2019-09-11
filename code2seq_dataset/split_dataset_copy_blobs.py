import os
import pickle
from random import shuffle
from shutil import copyfile
from typing import List, Dict

from commit_message_tokenizer import SEPARATOR


def split_list_in_two_parts(input_list: List[str], part_size: float) -> (List[str], List[str]):
    size = len(input_list)
    first_part_size = int(size * part_size)

    return input_list[:first_part_size], input_list[first_part_size + 1:]


def get_all_blobs_from_commits_for_train(needed_commits_pickle_file: str, full_log: str,
                                         output_file: str):# -> Dict[str, List[str]]:
    with open(needed_commits_pickle_file, 'rb') as file:
        needed_commits = pickle.load(file)
    print(len(needed_commits))
    # shuffle list of commits for train
    needed_commits = list(needed_commits)
    shuffle(needed_commits)
    # split dataset
    commits_train, commits_tmp = split_list_in_two_parts(needed_commits, 0.7)
    commits_val, commits_test = split_list_in_two_parts(commits_tmp, 0.5)

    print(f"train: {len(commits_train)}, test: {len(commits_test)}, val: {len(commits_val)}")

    blobs_for_train = {'train': [], 'val': [], 'test': []}
    splitted_commits = {'train': commits_train, 'test': commits_test, 'val': commits_val}

    # i = 0
    # with open(full_log, 'r') as full_log_file:
    #     for line in full_log_file:
    #         if line.startswith("commit_hash"):  # csv title # заменить на проверку приведения к числу
    #             continue
    #         line_list = line.split(SEPARATOR)
    #         commit, file, old_blob, new_blob, msg = line_list[0], line_list[3], line_list[4], line_list[5], line_list[6]
    #         if msg.startswith("this commit"):
    #             print(msg)
    #
    #         if commit in needed_commits:
    #             i += 1
    #             if i % 20 == 0:
    #                 print(f"{i} from {len(needed_commits)}")
    #             # print(line)
    #             if file.endswith(".java"):
    #                 if commit in commits_train:
    #                     set = 'train'
    #                 elif commit in commits_val:
    #                     set = 'val'
    #                 else:
    #                     set = 'test'
    #
    #                 blobs_for_train[set].append(old_blob)
    #                 blobs_for_train[set].append(new_blob)

    with open(output_file, 'wb') as file:
        pickle.dump(splitted_commits, file)

    # return blobs_for_train


def copy_blob_in_needed_dirs(data_dict: Dict[str, List[str]], blobs_dir: str, output_dir_parent: str):
    for set, blobs in data_dict.items():
        for blob in blobs:
            src = os.path.join(blobs_dir, blob)
            dst = os.path.join(output_dir_parent, set)
            dst = os.path.join(dst, blob + ".java")
            copyfile(src, dst)


if __name__ == "__main__":
    parent_dir = "/Users/natalia.murycheva/Documents/gitCommitMessageCollectorStorage"
    # git_dir_name = "aurora"
    git_dir_name = "intellij"
    git_dir = os.path.join(parent_dir, "packed_intellij")  # for intellij only
    git_dir = os.path.join(git_dir, git_dir_name)

    full_log_file = f"gcm_{git_dir_name}_full_log_for_train_commits.log"
    full_log_file = os.path.join(parent_dir, full_log_file)

    needed_commits_pickle_file = f"{git_dir_name}_commits_for_train.pickle"
    needed_commits_pickle_file = os.path.join(parent_dir, needed_commits_pickle_file)

    splitted_commits = f"{git_dir_name}_splitted_commits_set_train_val_test.pickle"
    splitted_commits = os.path.join(parent_dir, splitted_commits)

    blobs_dir = os.path.join(parent_dir, f"{git_dir_name}_blobs")
    splitted_blobs_dir = os.path.join(parent_dir, f"{git_dir_name}_blobs_splitted")

    train_val_test = get_all_blobs_from_commits_for_train(needed_commits_pickle_file,
                                                          full_log_file,
                                                          splitted_commits)
    # copy_blob_in_needed_dirs(train_val_test, blobs_dir, splitted_blobs_dir)



